#!/usr/bin/env python3
"""Read-only preflight and synthetic policy probes for generated OpenCode teams.

No subprocesses, plugins, model sessions, connector calls or config expansion.
Only the designer's generated Markdown subset and strict JSON are supported.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from check_secret_baseline import check_agent, parse_frontmatter, parse_v2_permissions

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
BUILTINS = {"build", "plan", "general", "explore"}


def local(root: Path, path: Path) -> bool:
    """Reject escapes and aliases (including symlinks/junctions)."""
    try:
        return path.is_relative_to(root) and path.resolve() == path
    except (OSError, RuntimeError):
        return False


def match(probe: str, pattern: str) -> bool:
    expression = re.escape(pattern.replace("\\", "/")).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(expression, probe.replace("\\", "/"), re.S) is not None


def rules(fm: dict, raw: str, major: int) -> list[tuple[str, str, str]]:
    v2 = parse_v2_permissions(raw.split("---", 2)[1])
    if major == 2:
        if v2 is None or "permission" in fm:
            raise ValueError("expected native V2 permissions")
        rows = [(r.get("action"), r.get("resource"), r.get("effect")) for r in v2]
    else:
        if v2 is not None or not isinstance(fm.get("permission"), dict):
            raise ValueError("expected native V1 permission map")
        rows = [(a, p, e) for a, value in fm["permission"].items()
                for p, e in (value.items() if isinstance(value, dict) else [("*", value)])]
    if not rows or any(not a or not p or e not in {"allow", "ask", "deny"} for a, p, e in rows):
        raise ValueError("unsupported or malformed permission rules")
    return rows


def action(rows: list[tuple[str, str, str]], tool: str, resource: str) -> str:
    return next((e for a, p, e in reversed(rows) if match(tool, a) and match(resource, p)), "unspecified")


def audit(root: Path, major: int, simulate: bool) -> tuple[list[str], list[str], list[str]]:
    errors, unverified, probes = [], [], []
    folder = root / ".opencode/agents"
    if not local(root, folder) or not folder.is_dir():
        return ["Missing or unsafe .opencode/agents directory"], [], []
    teams, edges = {}, {}
    configs = [root / name for name in ("opencode.json", "opencode.jsonc", ".opencode/opencode.json", ".opencode/opencode.jsonc")]
    present = [f for f in configs if f.exists() or f.is_symlink()]
    if len(present) != 1:
        return ["Expected one project config; layered or missing config needs manual review"], [], []
    config = present[0]
    if not local(root, config):
        return ["Project config resolves outside its approved path"], [], []
    try:
        data = json.loads(config.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError
    except (ValueError, OSError):
        return ["Config is unreadable or is not strict JSON; review JSONC manually"], [], []
    if any(key in data for key in ("agent", "agents", "mode")):
        errors.append("JSON contains agent definitions; Markdown must be the only source")
    # This one shared V2 rule affects only external-directory checks, which
    # are outside the in-repository read/edit and delegation probes below.
    external_ask_only = major == 2 and data.get("permissions") == [
        {"action": "external_directory", "resource": "*", "effect": "ask"},
    ]
    if (("permissions" in data and not external_ask_only)
            or any(key in data for key in ("permission", "tools", "plugin", "mcp"))):
        unverified.append("Shared permissions, tools, plugins or MCP settings are not simulated")
    if any((root / p).exists() for p in (".opencode/plugins", ".opencode/plugin")):
        unverified.append("Project plugin hooks were not loaded or simulated")
    instructions = data.get("instructions", [])
    if not isinstance(instructions, list) or not all(isinstance(p, str) for p in instructions):
        errors.append("Unexpected instructions configuration shape")
    else:
        for item in instructions:
            path = root / item
            if any(c in item for c in "*?[{}") or not local(root, path) or item.startswith(("~", "http:", "https:")):
                unverified.append("A patterned, external or aliased instruction path needs separate verification")
            elif not path.is_file():
                errors.append("A configured local instruction file is missing")

    manifest_names = set()
    skills = data.get("skills", {} if major == 1 else [])
    if major == 1 and isinstance(skills, dict):
        if skills.get("urls"):
            unverified.append("Remote skill catalogs were not loaded")
        skills = skills.get("paths", [])
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        errors.append("Unexpected skills configuration shape")
        skills = []
    seen_skill_dirs: set[Path] = set()
    for source in [".opencode/skills", ".agents/skills", ".claude/skills", *skills]:
        if source.startswith(("~", "http:", "https:")):
            unverified.append("A global or remote skill source needs separate verification")
            continue
        directory = Path(source) if Path(source).is_absolute() else root / source.removeprefix("./")
        if not local(root, directory):
            unverified.append("An external or aliased skill source was not inspected")
            continue
        # The same directory can be auto-discovered and listed in the skills
        # array; scan it once so an explicit entry is not a false duplicate.
        if directory in seen_skill_dirs:
            continue
        seen_skill_dirs.add(directory)
        if not directory.is_dir():
            if source in skills:
                errors.append("A configured local skill directory is missing")
            continue
        for manifest in directory.glob("*/SKILL.md"):
            if not local(root, manifest) or not manifest.is_file():
                unverified.append("An aliased skill manifest was not inspected")
                continue
            fm, _ = parse_frontmatter(manifest.read_text(encoding="utf-8"))
            name = fm.get("name")
            if name != manifest.parent.name or not NAME.fullmatch(name) or not isinstance(fm.get("description"), str):
                errors.append("A discovered local skill has invalid name or description")
            elif name in manifest_names:
                errors.append(f"Duplicate local skill: {name}")
            else:
                manifest_names.add(name)

    task = "task" if major == 1 else "subagent"
    for file in sorted(folder.glob("*.md")):
        name = file.stem
        if not NAME.fullmatch(name) or not local(root, file) or not file.is_file():
            errors.append("Invalid or aliased agent file")
            continue
        try:
            raw = file.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(raw)
            if (not body.strip() or fm.get("mode") not in {"primary", "subagent", "all"}
                    or not str(fm.get("steps", "")).isdigit() or int(fm["steps"]) < 1
                    or not isinstance(fm.get("description"), str)):
                raise ValueError("missing required generated agent fields")
            rows = rules(fm, raw, major)
            teams[name] = (fm["mode"], rows)
            # Do not echo checker diagnostics, which may contain untrusted rule text.
            if check_agent(file):
                errors.append(f"{name}: static secret-baseline checker failed")
        except (ValueError, OSError):
            errors.append(f"{name}: unsupported or invalid agent definition")

    default = data.get("default_agent")
    if not isinstance(default, str) or teams.get(default, (None,))[0] not in {"primary", "all"}:
        errors.append("default_agent does not select a local primary")

    for name, (_, rows) in teams.items():
        edges[name] = set()
        for tool, target, effect in rows:
            if tool == task and effect in {"allow", "ask"}:
                if target not in teams or teams[target][0] == "primary":
                    errors.append(f"{name}: Task grant is broad or does not name a local subagent")
                elif action(rows, task, target) in {"allow", "ask"}:
                    edges[name].add(target)
            if tool == "skill" and effect in {"allow", "ask"} and target not in manifest_names:
                unverified.append(f"{name}: a skill grant is broad or not resolved locally")
        if simulate:
            for other in sorted(set(teams) | BUILTINS | {"synthetic-unauthorized-agent"}):
                actual = action(rows, task, other)
                if other not in edges[name] and actual != "deny":
                    errors.append(f"{name}: synthetic undeclared Task is not explicitly denied")
                    break
            for kind in ("read", "edit"):
                for sample in (".env", "sub/.env", "gradle.properties", "sub/settings.xml", "sample.pem", "sub/sample.pem"):
                    if action(rows, kind, sample) != "deny":
                        errors.append(f"{name}: synthetic {kind} probe not denied: {sample}")
            for target in sorted(edges[name]):
                probes.append(f"Synthetic policy route: {name} -> {target} ({action(rows, task, target)})")

    for origin in edges:
        pending, seen = list(edges[origin]), set()
        while pending:
            node = pending.pop()
            if node == origin:
                errors.append(f"{origin}: delegation cycle")
                break
            if node not in seen:
                seen.add(node)
                pending.extend(edges[node])
    return errors, sorted(set(unverified)), probes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--major", required=True, type=int, choices=(1, 2))
    parser.add_argument("--mode", choices=("static", "simulate"), default="static")
    args = parser.parse_args(argv)
    try:
        if not args.project.is_absolute() or args.project != args.project.resolve(strict=True):
            raise ValueError
        errors, unverified, probes = audit(args.project, args.major, args.mode == "simulate")
    except (OSError, ValueError, RuntimeError):
        print("FAIL: could not safely inspect the selected project")
        return 2
    for prefix, rows in (("FAIL", errors), ("UNVERIFIED", unverified), ("SIMULATION", probes)):
        for row in rows:
            print(f"{prefix}: {row}")
    print("Live OpenCode, model, hooks, handoffs and tools: NOT RUN")
    print("Preflight: " + ("failed" if errors else "incomplete" if unverified else "passed"))
    return 1 if errors else 2 if unverified else 0


if __name__ == "__main__":
    raise SystemExit(main())
