#!/usr/bin/env python3
"""Verify that generated OpenCode agents carry the secret-protection baseline.

Usage: python3 scripts/check_secret_baseline.py [AGENTS_DIR ...]
Defaults to .opencode/agents. Exits 1 when any agent fails.

Baseline source: .opencode/skills/agent-org-design/reference/secret-baseline.md
Dependency-free: parses the simple nested-map frontmatter used by agent files.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_PATH_DENIES = [
    "**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/*.p12", "**/*.jks",
    "**/id_rsa*", "**/.npmrc", "**/.pypirc", "**/.netrc", "**/settings.xml",
    "gradle.properties", "**/gradle.properties", "**/*.tfvars", "**/*.tfstate",
    "**/kubeconfig*", "**/.aws/**", "**/.docker/config.json",
    "**/credentials*", "**/secrets/**",
]

REQUIRED_BASH_DENIES = [
    "env*", "printenv*", "Get-ChildItem env:*", "git log -p*", "git show*",
    "terraform output*", "kubectl get secret*", "docker inspect*",
    "mvn help:effective-settings*", "*gradle* properties*",
]

PROMPT_MARKER = "[REDACTED]"
UNSCOPED_BASH = {"*", "git diff*", "git log*", "cat *", "type *", "Get-Content *"}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not match:
        return {}, text
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in match.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        kv = re.match(r'^("([^"]*)"|\'([^\']*)\'|[^:]+):\s*(.*)$', line)
        if not kv:
            continue
        key = kv.group(2) if kv.group(2) is not None else (
            kv.group(3) if kv.group(3) is not None else kv.group(1).strip())
        value = kv.group(4).split(" #")[0].strip().strip('"').strip("'")
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = value
    return root, match.group(2)


def ordered_rule(rules, pattern: str) -> str | None:
    if isinstance(rules, dict):
        return rules.get(pattern)
    return None


def check_agent(path: Path) -> list[str]:
    errors: list[str] = []
    fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    perm = fm.get("permission")
    if not isinstance(perm, dict):
        return ["missing permission block"]

    read = perm.get("read")
    if read == "deny":
        pass
    elif not isinstance(read, dict):
        errors.append("read must be an object with explicit secret denials")
    else:
        for p in REQUIRED_PATH_DENIES:
            if read.get(p) != "deny":
                errors.append(f"read: missing deny for {p}")

    edit = perm.get("edit")
    if edit not in ("deny",):
        if not isinstance(edit, dict):
            errors.append("edit must be 'deny' or an object with secret denials")
        else:
            for p in REQUIRED_PATH_DENIES:
                if edit.get(p) != "deny":
                    errors.append(f"edit: missing deny for {p}")

    if perm.get("grep") != "deny":
        errors.append("grep must be deny (cannot enforce read exclusions)")

    bash = perm.get("bash")
    if bash == "allow":
        errors.append("bash: unrestricted allow")
    elif isinstance(bash, dict):
        keys = list(bash.keys())
        allows = [k for k, v in bash.items() if v == "allow"]
        for k in allows:
            if k in UNSCOPED_BASH:
                errors.append(f"bash: unscoped allow '{k}' can disclose secrets")
        if allows:
            last_allow = max(keys.index(k) for k in allows)
            for p in REQUIRED_BASH_DENIES:
                if bash.get(p) != "deny":
                    errors.append(f"bash: missing deny for {p}")
                elif keys.index(p) < last_allow:
                    errors.append(f"bash: deny '{p}' must come after all allows")

    if PROMPT_MARKER not in body:
        errors.append("prompt: missing mandatory secret-redaction clause")
    return errors


def main(argv: list[str]) -> int:
    dirs = [Path(a) for a in argv] or [Path(".opencode/agents")]
    failed = 0
    checked = 0
    for d in dirs:
        files = sorted(d.glob("*.md")) if d.is_dir() else [d]
        for f in files:
            checked += 1
            errs = check_agent(f)
            if errs:
                failed += 1
                print(f"FAIL {f}")
                for e in errs:
                    print(f"  - {e}")
            else:
                print(f"PASS {f}")
    if checked == 0:
        print("No agent files found.")
        return 1
    print(f"{checked - failed}/{checked} agents pass the secret baseline.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
