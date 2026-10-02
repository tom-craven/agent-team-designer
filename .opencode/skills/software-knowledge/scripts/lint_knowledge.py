#!/usr/bin/env python3
"""Lint knowledge nodes for broken IDs, missing sources, and empty active nodes.

Also reports knowledge-coverage gaps: knowledge that exists but was captured
under the wrong kind (flows, patterns, capabilities, amendments, and open items
buried inside decisions). Coverage findings are warnings unless --strict.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from compile_graph import EDGE_KEYS, METADATA_KEYS, as_list, compile_repo, parse_frontmatter

ACTIVE_TODO_MARKERS = ("TODO", "YYYY-MM-DD", "type:context.typename")
VALID_STATUSES = {"evolving", "active", "deprecated"}
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


COVERAGE_MIN_DECISIONS = 5
HARVEST_KINDS = ("capability", "flow", "pattern")
ORDERED_STEP = re.compile(r"^\s*\d+\.\s+\S", re.MULTILINE)
PATTERN_SIGNAL = re.compile(
    r"\b(?:same|recurring|reusable|standard)\b[^.\n]{0,60}\bpattern\b"
    r"|\b(?:like|as) every other\b",
    re.IGNORECASE,
)
AMENDMENT_SIGNAL = re.compile(
    r"^\s*\*\*(?:amended|refined|tightened|superseded)\b|\bno longer holds\b",
    re.IGNORECASE | re.MULTILINE,
)
# Only labelled open-item sections count; prose such as "settles the open
# question" or "closes the open item" is resolution, not an open item.
OPEN_ITEM_SIGNAL = re.compile(
    r"^\s*(?:#+\s*|\*\*)open (?:items?|questions?|decisions?)\b",
    re.IGNORECASE | re.MULTILINE,
)
# A request or build path written as prose: two or more arrows on one line.
ARROW_CHAIN = re.compile(r"(?:→|->)[^\n]*(?:→|->)")
STATUS_SECTION = re.compile(
    r"^##\s+Status\s*\n+\s*\**(active|evolving|deprecated|superseded)\b",
    re.IGNORECASE | re.MULTILINE,
)


def longest_ordered_run(body: str) -> int:
    """Length of the longest run of consecutive numbered list lines."""
    longest = current = 0
    for line in body.splitlines():
        if ORDERED_STEP.match(line):
            current += 1
            longest = max(longest, current)
        elif line.strip():
            if not line.startswith((" ", "\t")):
                current = 0
    return longest


def coverage_findings(
    root: Path, index: dict, graph: dict
) -> list[str]:
    """Detect knowledge that exists but was captured under the wrong kind."""
    findings: list[str] = []
    nodes = {n["id"]: n for n in index["nodes"]}
    kinds = [n["kind"] for n in index["nodes"]]
    neighbours: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    superseded_targets: set[str] = set()
    for edge in graph["edges"]:
        neighbours.setdefault(edge["from"], set()).add(edge["to"])
        neighbours.setdefault(edge["to"], set()).add(edge["from"])
        if edge["type"] == "supersedes":
            superseded_targets.add(edge["to"])

    def linked_kinds(node_id: str) -> set[str]:
        return {
            nodes[other]["kind"]
            for other in neighbours.get(node_id, set())
            if other in nodes
        }

    decision_count = kinds.count("decision")
    if decision_count >= COVERAGE_MIN_DECISIONS:
        for kind in HARVEST_KINDS:
            present = kinds.count(kind) + (
                kinds.count("anti_pattern") if kind == "pattern" else 0
            )
            if present == 0:
                findings.append(
                    f"coverage: {decision_count} decisions but no {kind} nodes; "
                    "run the harvest workflow"
                )

    for node in index["nodes"]:
        node_id = node["id"]
        if node["status"] == "deprecated":
            continue
        raw = (root / node["path"]).read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        meta = meta or {}
        linked = linked_kinds(node_id)

        if node["kind"] in ("decision", "invariant"):
            has_steps = longest_ordered_run(body) >= 4 or ARROW_CHAIN.search(body)
            if has_steps and "flow" not in linked:
                findings.append(
                    f"coverage: {node_id} contains an ordered step list but links "
                    "no flow; extract the steps into a flow node"
                )
            if PATTERN_SIGNAL.search(body) and not linked & {"pattern", "anti_pattern"}:
                findings.append(
                    f"coverage: {node_id} describes a repeated design but links no "
                    "pattern; extract it into a pattern node"
                )

        if node["kind"] == "decision":
            stated = STATUS_SECTION.search(body)
            if stated:
                word = stated.group(1).lower()
                word = "deprecated" if word == "superseded" else word
                if word != node["status"]:
                    findings.append(
                        f"coverage: {node_id} frontmatter status is "
                        f"{node['status']!r} but its Status section says {word!r}"
                    )
            if AMENDMENT_SIGNAL.search(body) and not (
                meta.get("supersedes")
                or meta.get("superseded_by")
                or node_id in superseded_targets
            ):
                findings.append(
                    f"coverage: {node_id} records an amendment in prose; record it "
                    "as a new decision with supersedes/superseded_by"
                )
            if node["status"] == "active" and OPEN_ITEM_SIGNAL.search(body):
                has_evolving = any(
                    nodes[other]["kind"] == "decision"
                    and nodes[other]["status"] == "evolving"
                    for other in neighbours.get(node_id, set())
                    if other in nodes
                )
                if not has_evolving:
                    findings.append(
                        f"coverage: {node_id} carries open items; record each as a "
                        "decision with status: evolving and link it"
                    )

        if node["kind"] == "contract" and "capability" not in linked:
            findings.append(
                f"coverage: {node_id} is not linked to any capability; add "
                "realized_by from the capability it serves"
            )

        for target in sorted(
            set(as_list(meta.get("guarded_by"))) | set(as_list(meta.get("invariants")))
        ):
            if target in nodes and nodes[target]["status"] == "deprecated":
                findings.append(
                    f"coverage: {node_id} is guarded_by deprecated {target}; "
                    "point it at the replacement in superseded_by"
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat knowledge-coverage findings as errors",
    )
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
        if meta and meta.get("status") is not None and meta.get("status") not in VALID_STATUSES:
            errors.append(
                f"invalid status {meta.get('status')!r} in {node['id']}; "
                f"use one of {sorted(VALID_STATUSES)}"
            )
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

    for finding in coverage_findings(root, index, graph):
        if args.strict:
            errors.append(finding)
        else:
            print(f"warn: {finding}", file=sys.stderr)

    print(f"linted {len(index['nodes'])} nodes, {len(graph['edges'])} edges")
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
