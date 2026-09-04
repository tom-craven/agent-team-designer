#!/usr/bin/env python3
"""Compile knowledge nodes into knowledge/index.yaml and knowledge/graph.yaml."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

EDGE_KEYS = {
    "owns": "owns",
    "implements": "implements",
    "depends_on": "depends_on",
    "must_not_depend_on": "must_not_depend_on",
    "collaborates_with": "collaborates_with",
    "emits": "emits",
    "consumes": "consumes",
    "guarded_by": "guarded_by",
    "invariants": "guarded_by",
    "decided_by": "decided_by",
    "used_in": "used_in",
    "uses": "used_in",
    "realized_by": "realized_by",
    "applies_to": "applies_to",
    "supersedes": "supersedes",
    "superseded_by": "superseded_by",
    "emitted_by": "emitted_by",
    "consumers": "consumed_by",
    "enforced_by": "enforced_by",
}

SKIP_DIR_NAMES = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__"}


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict):
        return None, text
    return meta, parts[2]


def iter_knowledge_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        name = path.name
        rel = path.relative_to(root).as_posix()
        if name.endswith(".context.md"):
            files.append(path)
            continue
        if rel.startswith("knowledge/") and name.endswith(".md") and name != "README.md":
            files.append(path)
    return sorted(files)


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return [str(value)]


def compile_repo(root: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    seen_ids: dict[str, str] = {}

    for path in iter_knowledge_files(root):
        rel = path.relative_to(root).as_posix()
        meta, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta:
            warnings.append(f"no frontmatter: {rel}")
            continue
        node_id = meta.get("id")
        kind = meta.get("kind")
        if not node_id or not kind:
            warnings.append(f"missing id or kind: {rel}")
            continue
        node_id = str(node_id)
        if node_id in seen_ids:
            warnings.append(f"duplicate id {node_id}: {rel} and {seen_ids[node_id]}")
        seen_ids[node_id] = rel

        nodes.append(
            {
                "id": node_id,
                "kind": str(kind),
                "name": meta.get("name") or path.stem,
                "path": rel,
                "status": meta.get("status") or "evolving",
                "source": meta.get("source"),
                "bounded_context": meta.get("bounded_context"),
                "owners": as_list(meta.get("owners")),
                "tags": as_list(meta.get("tags")),
            }
        )

        for key, edge_type in EDGE_KEYS.items():
            for target in as_list(meta.get(key)):
                edges.append({"from": node_id, "type": edge_type, "to": str(target)})

    index = {
        "generated": date.today().isoformat(),
        "node_count": len(nodes),
        "nodes": nodes,
    }
    graph = {
        "generated": date.today().isoformat(),
        "nodes": [{"id": n["id"], "kind": n["kind"], "path": n["path"]} for n in nodes],
        "edges": edges,
    }
    return index, graph, warnings


def dump(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    index, graph, warnings = compile_repo(root)
    dump(root / "knowledge" / "index.yaml", index)
    dump(root / "knowledge" / "graph.yaml", graph)

    print(f"wrote {len(index['nodes'])} nodes, {len(graph['edges'])} edges")
    for warning in warnings:
        print(f"warn: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
