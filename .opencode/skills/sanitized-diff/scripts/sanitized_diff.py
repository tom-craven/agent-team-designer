#!/usr/bin/env python3
"""Print a redacted, snapshot-identified diff of the working tree against HEAD.

Run it from the repository root, with no argument or exactly `--page N`:
    py -3 scripts/sanitized_diff.py            (Windows; same as --page 1)
    py -3 scripts/sanitized_diff.py --page 2
    python3 scripts/sanitized_diff.py --page 2 (elsewhere)

Large diffs are split into pages at file boundaries. Every page carries the same
master SNAPSHOT ID (over the whole change), `PAGE k of N`, a page hash and the
complete changed-path inventory with a page map. A review is complete only when
every page 1..N was read under the same master ID.

Reviewable scope: optional file `scripts/sanitized_diff.paths` next to this
script, one glob per line (`#` comments). Absent file = every non-protected path.

Fail closed: any internal error prints nothing but a BLOCKED line, exit 2.
A change too large to page (see limits) is withheld, exit 3.
Dependency-free; the only subprocess is git with fixed, hard-coded arguments.
"""
import fnmatch
import hashlib
import os
import re
import subprocess
import sys

# Secret-bearing paths (secret-baseline.md). Matched against the whole
# forward-slash path, case-insensitively. Content is never emitted for these.
PROTECTED = [
    "*.env", "*.env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks",
    "*.keystore", "*id_rsa*", "*id_ed25519*", "*.npmrc", "*.pypirc", "*.netrc",
    "*settings.xml", "*gradle.properties", "*.tfvars", "*.tfstate",
    "*.tfstate.*", "*kubeconfig*", "*.kube/*", "*.aws/*", "*.azure/*",
    "*.docker/config.json", "*credentials*", "*secrets/*", "*auth.json",
    ".git/*",
]
MAX_BYTES = 1_000_000  # larger untracked files are listed, not diffed
PAGE_LINES = 800       # target diff lines per page (cut at file boundaries)
MAX_PAGES = 8          # more pages than this: the change is withheld
MAX_BLOCK_LINES = 2000  # one file's diff above this: the change is withheld

PEM = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(-----END [A-Z ]*PRIVATE KEY-----|$)", re.S)
TOKEN = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|"
    r"xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9_-]{20,}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")
KV = re.compile(
    r"(?i)((?:pass(?:word|wd)?|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"client[_-]?secret|authorization|bearer|credentials?)[\"']?\s*[:=]\s*|bearer\s+)"
    r"(\"[^\"]+\"|'[^']+'|[^\s,;\"']+)")
URLCRED = re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)[^@\s/]+(@)")
LONG = re.compile(r"[A-Za-z0-9+/=_-]{32,}")


def git(*args):
    # Scrub the environment: GIT_* variables can redirect the repository or run
    # programs. fsmonitor and hooks-path are disabled so repository config cannot
    # execute code during a read-only diff.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    p = subprocess.run(
        ["git", "--no-pager", "-c", "core.quotepath=off", "-c", "core.fsmonitor=false",
         "-c", "core.hooksPath=", "-c", "diff.external=", *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    if p.returncode != 0:
        raise RuntimeError("git failed")
    return p.stdout


CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
CTRL_PATH = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def esc(s, pattern=CTRL):
    """Escape control characters so content or names cannot forge report
    structure or inject terminal escape sequences."""
    return pattern.sub(lambda m: "\\x%02x" % ord(m.group(0)), s)


def filehash(root, path):
    """Hash a working-tree file for the snapshot only; never printed."""
    full = os.path.join(root, path)
    h = hashlib.sha256()
    if os.path.islink(full):
        h.update(b"link:" + os.readlink(full).encode("utf-8", "replace"))
    elif os.path.isfile(full):
        with open(full, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    else:
        h.update(b"absent")
    return h.hexdigest()


def entropy(s):
    from math import log2
    return -sum(s.count(c) / len(s) * log2(s.count(c) / len(s)) for c in set(s))


def redact(line):
    line = URLCRED.sub(r"\1[REDACTED]\2", line)
    line = TOKEN.sub("[REDACTED]", line)
    line = KV.sub(lambda m: m.group(1) + "[REDACTED]", line)
    return LONG.sub(lambda m: "[REDACTED]" if entropy(m.group(0)) > 3.5 else m.group(0), line)


def protected(path):
    p = path.replace("\\", "/").lower()
    return any(fnmatch.fnmatchcase(p, pat) or fnmatch.fnmatchcase("/" + p, "*/" + pat.lstrip("*/"))
               for pat in PROTECTED)


def scope():
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanitized_diff.paths")
    if not os.path.isfile(cfg):
        return None
    with open(cfg, encoding="utf-8") as f:
        pats = [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    return pats or None


def in_scope(path, pats):
    p = path.replace("\\", "/")
    return pats is None or any(fnmatch.fnmatchcase(p, g) for g in pats)


def sanitize_text(text):
    text = PEM.sub("[REDACTED PRIVATE KEY]", text)
    return "\n".join(esc(redact(l)) for l in text.split("\n"))


def parse_args(argv):
    """Accept exactly no argument, or `--page N` with N a positive integer."""
    if not argv:
        return 1
    if len(argv) == 2 and argv[0] == "--page" and re.fullmatch(r"[1-9][0-9]{0,2}", argv[1]):
        return int(argv[1])
    raise RuntimeError("usage: sanitized_diff.py [--page N]")


def paginate(blocks):
    """Greedy split at file boundaries; a file is never split across pages."""
    pages, cur, cur_lines = [], [], 0
    for blk in blocks:
        if cur and cur_lines + blk["lines"] > PAGE_LINES:
            pages.append(cur)
            cur, cur_lines = [], 0
        cur.append(blk)
        cur_lines += blk["lines"]
    pages.append(cur)
    return pages


def main():
    wanted = parse_args(sys.argv[1:])
    root = git("rev-parse", "--show-toplevel").decode().strip()
    if os.path.normcase(os.path.realpath(os.getcwd())) != os.path.normcase(os.path.realpath(root)):
        raise RuntimeError("run from the repository root")
    head = git("rev-parse", "HEAD").decode().strip()
    pats = scope()

    # name-status with rename detection; NUL separated
    raw = git("diff", "--name-status", "-z", "-M", "--no-ext-diff", "--no-textconv", "HEAD").decode("utf-8", "replace")
    parts = [x for x in raw.split("\0") if x]
    changes, i = [], 0
    while i < len(parts):
        st = parts[i]
        if st[0] in "RC":
            changes.append((st[0], parts[i + 2], parts[i + 1])); i += 3
        else:
            changes.append((st[0], parts[i + 1], None)); i += 2
    untracked = [x for x in git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8", "replace").split("\0") if x]
    changes += [("?", u, None) for u in untracked]

    inventory, blocks, omitted, withheld = [], [], [], []

    def add_block(shown, text):
        blocks.append({"path": shown, "text": text, "lines": text.count("\n") + 1})

    for st, rawpath, old in changes:
        path = rawpath  # real path for file access; `shown` is the escaped form
        shown = esc(path, CTRL_PATH)
        if protected(path) or (old and protected(old)):
            inventory.append(f"{st}\t[PROTECTED PATH: name withheld]")
            withheld.append(path)
            continue
        if not in_scope(path, pats):
            omitted.append(f"{st}\t{shown}")
            withheld.append(path)
            continue
        inventory.append(f"{st}\t{shown}" + (f"\t(from {esc(old, CTRL_PATH)})" if old else ""))
        if st == "D":
            add_block(shown, f"--- deleted: {shown} (content not shown)")
            continue
        if st == "?":
            full = os.path.join(root, path)
            if os.path.islink(full) or not os.path.isfile(full) or os.path.getsize(full) > MAX_BYTES:
                add_block(shown, f"+++ new (not diffed: symlink, non-file or >{MAX_BYTES} bytes): {shown}")
                continue
            with open(full, "rb") as f:
                data = f.read()
            if b"\0" in data:
                add_block(shown, f"+++ new binary: {shown}")
                continue
            txt = sanitize_text(data.decode("utf-8", "replace"))
            add_block(shown, f"+++ new file: {shown}\n" + "\n".join("+" + l for l in txt.split("\n")))
            continue
        out = git("diff", "--no-ext-diff", "--no-textconv", "--no-color", "-M", "HEAD", "--", path).decode("utf-8", "replace")
        if "Binary files" in out:
            add_block(shown, f"~~~ binary changed: {shown}")
        else:
            add_block(shown, sanitize_text(out).rstrip("\n"))

    report = "\n".join(b["text"] for b in blocks) + "\n"
    inv = "\n".join(sorted(inventory)) + "\n"
    # Withheld and out-of-scope files contribute a content hash to the snapshot
    # (never printed), so changing them still invalidates earlier approvals.
    wh = "\n".join(sorted(f"{p}:{filehash(root, p)}" for p in withheld))
    snap = hashlib.sha256((head + "\n" + inv + report + "\n" + wh).encode("utf-8", "replace")).hexdigest()[:16]
    sid = f"{head[:12]}-{snap}"
    pages = paginate(blocks)
    npages = len(pages)
    total = sum(b["lines"] for b in blocks)
    too_big = npages > MAX_PAGES or any(b["lines"] > MAX_BLOCK_LINES for b in blocks)

    def header():
        print(f"SNAPSHOT: {sid}")
        print(f"BASELINE: HEAD {head}")
        print("SCOPE: " + ("all non-protected paths" if pats is None else ", ".join(pats)))
        print("REDACTION: pattern-based on added and removed lines; not a guarantee, human review still required")

    if too_big:
        header()
        print("--- CHANGED PATHS (complete) ---")
        print(inv, end="")
        if omitted:
            print("--- OUT OF SCOPE (names only, no content) ---")
            print("\n".join(sorted(omitted)))
        print(f"--- DIFF NOT SHOWN: {total} lines in {npages} pages exceeds the limit "
              f"({MAX_PAGES} pages, {MAX_BLOCK_LINES} lines per file); narrow scripts/sanitized_diff.paths ---")
        print(f"END SNAPSHOT: {sid} (diff withheld, NOT approvable)")
        sys.exit(3)
    if wanted > npages:
        raise RuntimeError(f"page {wanted} out of range (1..{npages})")

    page = pages[wanted - 1]
    page_text = "\n".join(b["text"] for b in page) + "\n"
    page_hash = hashlib.sha256(page_text.encode("utf-8", "replace")).hexdigest()[:12]
    page_map = []
    for idx, pg in enumerate(pages, 1):
        for b in pg:
            page_map.append(f"{idx}\t{b['path']}")

    header()
    print(f"PAGE: {wanted} of {npages}")
    print(f"PAGE HASH: {page_hash}")
    print("--- CHANGED PATHS (complete) ---")
    print(inv, end="")
    if omitted:
        print("--- OUT OF SCOPE (names only, no content) ---")
        print("\n".join(sorted(omitted)))
    print("--- PAGE MAP (page, path) ---")
    print("\n".join(page_map) if page_map else "(no in-scope changes)")
    print(f"--- SANITIZED DIFF (page {wanted} of {npages}) ---")
    print(page_text, end="")
    print(f"END SNAPSHOT: {sid} (page {wanted}/{npages}, {page_text.count(chr(10))} diff lines)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # fail closed: never emit partial output
        sys.stdout.flush()
        print(f"BLOCKED: sanitized diff unavailable ({type(exc).__name__}: {exc})", file=sys.stderr)
        sys.exit(2)
