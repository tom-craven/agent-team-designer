#!/usr/bin/env python3
"""Lint knowledge nodes for broken IDs, missing sources, and empty active nodes."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from compile_graph import EDGE_KEYS, METADATA_KEYS, compile_repo, parse_frontmatter

ACTIVE_TODO_MARKERS = ("TODO", "YYYY-MM-DD", "type:context.typename")
EDGE_TABLE_ROW = re.compile(r"^\|\s+`([^`]+)`(?:\s+/\s+`([^`]+)`)?\s+\|", re.MULTILINE)


def documented_edge_keys() -> set[str]:
    ontology = Path(__file__).resolve().parents[1] / "references" / "ontology.md"
    text = ontology.read_text(encoding="utf-8")
    keys: set[str] = set()
    for first, second in EDGE_TABLE_ROW.findall(text):
        keys.add(first)
        if second:
            keys.add(second)
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    index, graph, warnings = compile_repo(root)
    errors: list[str] = []
    ids = {n["id"] for n in index["nodes"]}

    documented = documented_edge_keys()
    compiler_keys = set(EDGE_KEYS)
    if compiler_keys != documented:
        errors.append(
            "ontology/compiler edge mismatch: "
            f"undocumented={sorted(compiler_keys - documented)}, "
            f"uncompiled={sorted(documented - compiler_keys)}"
        )

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
        if meta:
            unknown_keys = sorted(set(meta) - METADATA_KEYS)
            for key in unknown_keys:
                errors.append(f"unknown frontmatter key {key!r} in {node['id']}")
            for key in sorted(set(meta) & set(EDGE_KEYS)):
                value = meta.get(key)
                if value is not None and not isinstance(value, (list, str)):
                    errors.append(
                        f"edge {key!r} must be a string or list in {node['id']}"
                    )
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
