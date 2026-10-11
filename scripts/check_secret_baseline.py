#!/usr/bin/env python3
"""Verify that generated OpenCode agents carry the secret-protection baseline.

Usage: python3 scripts/check_secret_baseline.py [AGENTS_DIR ...]
Defaults to .opencode/agents. Exits 1 when any agent fails.

Baseline source: .opencode/skills/agent-org-design/reference/secret-baseline.md
Accepts V1 ``permission:`` maps and native V2 ``permissions:`` rule lists
(last matching rule wins). Dependency-free.
"""
from __future__ import annotations

import fnmatch
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


def parse_v2_permissions(frontmatter: str) -> list[dict] | None:
    """Parse a native V2 ``permissions:`` list of action/resource/effect rules.

    Supports block items (``- action: x`` followed by indented keys) and inline
    flow items (``- { action: x, resource: y, effect: z }``). Returns None when
    no ``permissions:`` key is present.
    """
    lines = frontmatter.splitlines()
    start = next((i for i, l in enumerate(lines)
                  if re.match(r"^permissions:\s*$", l)), None)
    if start is None:
        return None
    rules: list[dict] = []
    current: dict | None = None
    for raw in lines[start + 1:]:
        if raw.strip() and not raw.startswith((" ", "-")):
            break  # next top-level key
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            current = {}
            rules.append(current)
            line = line[1:].strip()
            if line.startswith("{") and line.endswith("}"):
                for part in line[1:-1].split(","):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        current[k.strip()] = _unquote(v)
                current = None
                continue
        if current is not None and ":" in line:
            k, v = line.split(":", 1)
            current[k.strip()] = _unquote(v)
    return rules


def _unquote(value: str) -> str:
    return value.split(" #")[0].strip().strip('"').strip("'")


# V1 action names map to their V2 equivalents.
ACTION_ALIASES = {"bash": "shell", "task": "subagent", "write": "edit",
                  "patch": "edit"}


def effective(rules: list[dict], action: str, probe: str) -> tuple[str | None, int]:
    """Return (effect, index) of the last rule matching action and probe."""
    result: tuple[str | None, int] = (None, -1)
    for i, r in enumerate(rules):
        r_action = ACTION_ALIASES.get(r.get("action", ""), r.get("action", ""))
        if not fnmatch.fnmatchcase(action, r_action):
            continue
        resource = r.get("resource", "*")
        if resource == probe or fnmatch.fnmatchcase(probe, resource):
            result = (r.get("effect"), i)
    return result


def check_v2_rules(rules: list[dict]) -> list[str]:
    errors: list[str] = []
    for action in ("read", "edit"):
        for p in REQUIRED_PATH_DENIES:
            if effective(rules, action, p)[0] != "deny":
                errors.append(f"{action}: secret path {p} is not effectively denied")
    if effective(rules, "grep", "*")[0] != "deny":
        errors.append("grep must be deny (cannot enforce read exclusions)")

    shell_allows = [i for i, r in enumerate(rules)
                    if ACTION_ALIASES.get(r.get("action"), r.get("action"))
                    in ("shell", "*") and r.get("effect") == "allow"]
    for i in shell_allows:
        if rules[i].get("resource", "*") in UNSCOPED_BASH:
            errors.append(
                f"shell: unscoped allow '{rules[i].get('resource', '*')}' can disclose secrets")
    if shell_allows:
        last_allow = max(shell_allows)
        for p in REQUIRED_BASH_DENIES:
            eff, idx = effective(rules, "shell", p)
            if eff != "deny":
                errors.append(f"shell: missing deny for {p}")
            elif idx < last_allow:
                errors.append(f"shell: deny '{p}' must come after all allows")
    return errors


def check_agent(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    v2_rules = parse_v2_permissions(match.group(1)) if match else None
    if v2_rules is not None:
        if "permission" in fm:
            errors.append("mixes V1 'permission' and V2 'permissions'; use one format")
        errors.extend(check_v2_rules(v2_rules))
        if PROMPT_MARKER not in body:
            errors.append("prompt: missing mandatory secret-redaction clause")
        return errors

    perm = fm.get("permission")
    if not isinstance(perm, dict):
        return ["missing permission block (V1 'permission' or V2 'permissions')"]

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
