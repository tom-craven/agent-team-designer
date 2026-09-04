#!/usr/bin/env python3
"""Lint knowledge nodes for broken IDs, missing sources, and empty active nodes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compile_graph import compile_repo, parse_frontmatter

ACTIVE_TODO_MARKERS = ("TODO", "YYYY-MM-DD", "type:context.typename")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    index, graph, warnings = compile_repo(root)
    errors: list[str] = []
    ids = {n["id"] for n in index["nodes"]}

    for warning in warnings:
        if warning.startswith("duplicate id") or warning.startswith("missing id"):
            errors.append(warning)
        else:
            print(f"warn: {warning}", file=sys.stderr)

    for edge in graph["edges"]:
        if edge["to"] not in ids:
            errors.append(
                f"dangling edge {edge['from']} -{edge['type']}-> {edge['to']}"
            )

    for node in index["nodes"]:
        source = node.get("source")
        if node["kind"] == "type" and source and not (root / source).exists():
            errors.append(f"missing source for {node['id']}: {source}")

        raw = (root / node["path"]).read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        if node["status"] == "active" and any(m in raw for m in ACTIVE_TODO_MARKERS):
            errors.append(f"active node still looks like a template: {node['id']}")
        if node["status"] == "active" and meta and not body.strip():
            errors.append(f"active node has empty body: {node['id']}")
        if meta and meta.get("status") == "deprecated" and not meta.get("superseded_by"):
            print(f"warn: deprecated without superseded_by: {node['id']}", file=sys.stderr)

    print(f"linted {len(index['nodes'])} nodes, {len(graph['edges'])} edges")
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
