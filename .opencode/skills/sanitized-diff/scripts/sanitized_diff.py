#!/usr/bin/env python3
"""Print a redacted, snapshot-identified diff of the working tree against HEAD.

Takes NO arguments. Run it from the repository root:
    py -3 scripts/sanitized_diff.py        (Windows)
    python3 scripts/sanitized_diff.py      (elsewhere)

Reviewable scope: optional file `scripts/sanitized_diff.paths` next to this
script, one glob per line (`#` comments). Absent file = every non-protected path.

Fail closed: any internal error prints nothing but a BLOCKED line, exit 2.
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
MAX_BYTES = 1_000_000  # larger files are listed, not diffed
MAX_LINES = 1200  # above this the diff is withheld: one tool read must hold it all

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


def main():
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

    inventory, body, omitted, withheld = [], [], [], []
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
            body.append(f"--- deleted: {shown} (content not shown)")
            continue
        if st == "?":
            full = os.path.join(root, path)
            if os.path.islink(full) or not os.path.isfile(full) or os.path.getsize(full) > MAX_BYTES:
                body.append(f"+++ new (not diffed: symlink, non-file or >{MAX_BYTES} bytes): {shown}")
                continue
            with open(full, "rb") as f:
                data = f.read()
            if b"\0" in data:
                body.append(f"+++ new binary: {shown}")
                continue
            txt = sanitize_text(data.decode("utf-8", "replace"))
            body.append(f"+++ new file: {shown}")
            body.extend("+" + l for l in txt.split("\n"))
            continue
        out = git("diff", "--no-ext-diff", "--no-textconv", "--no-color", "-M", "HEAD", "--", path).decode("utf-8", "replace")
        if "Binary files" in out:
            body.append(f"~~~ binary changed: {shown}")
        else:
            body.append(sanitize_text(out).rstrip("\n"))

    report = "\n".join(body) + "\n"
    inv = "\n".join(sorted(inventory)) + "\n"
    # Withheld and out-of-scope files contribute a content hash to the snapshot
    # (never printed), so changing them still invalidates earlier approvals.
    wh = "\n".join(sorted(f"{p}:{filehash(root, p)}" for p in withheld))
    snap = hashlib.sha256((head + "\n" + inv + report + "\n" + wh).encode("utf-8", "replace")).hexdigest()[:16]
    sid = f"{head[:12]}-{snap}"
    nlines = report.count("\n")
    too_big = nlines > MAX_LINES
    print(f"SNAPSHOT: {sid}")
    print(f"BASELINE: HEAD {head}")
    print("SCOPE: " + ("all non-protected paths" if pats is None else ", ".join(pats)))
    print("REDACTION: pattern-based on added and removed lines; not a guarantee, human review still required")
    print("--- CHANGED PATHS (complete) ---")
    print(inv, end="")
    if omitted:
        print("--- OUT OF SCOPE (names only, no content) ---")
        print("\n".join(sorted(omitted)))
    if too_big:
        print(f"--- DIFF NOT SHOWN: {nlines} lines exceeds {MAX_LINES}; narrow scripts/sanitized_diff.paths ---")
        print(f"END SNAPSHOT: {sid} (diff withheld, NOT approvable)")
        sys.exit(3)
    print("--- SANITIZED DIFF ---")
    print(report, end="")
    print(f"END SNAPSHOT: {sid} ({nlines} diff lines)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # fail closed: never emit partial output
        sys.stdout.flush()
        print(f"BLOCKED: sanitized diff unavailable ({type(exc).__name__}: {exc})", file=sys.stderr)
        sys.exit(2)
