#!/usr/bin/env python3
"""Analyse the knowledge tree for prune opportunities. READ-ONLY.

Reports candidates for merging, condensing, refining, or (with user
confirmation) removing knowledge, with the evidence and the size each would
save. It never writes, edits, or deletes anything: the agent reviews the report,
proposes a plan, and applies it only after the user approves.

Categories:
  superseded   deprecated or superseded nodes that are not yet tombstones
  duplicate    exact or near-duplicate bodies of the same kind
  orphan       nodes with no inbound or outbound edges
  stale        `evolving` nodes not updated for --stale-days (user confirmation
               is always required before any removal)
  oversized    nodes whose body exceeds --max-lines
  dead         deprecated nodes with no replacement and no inbound edges
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from compile_graph import compile_repo, parse_frontmatter

TOMBSTONE_MAX_LINES = 8
DEFAULT_STALE_DAYS = 90
DEFAULT_MAX_LINES = 120
DEFAULT_SIMILARITY = 0.90
# Kinds that are never offered for orphan, stale, or oversized pruning.
PROTECTED_KINDS = {"system", "bounded_context", "invariant"}
# Kinds whose orphan state is normal.
ORPHAN_EXEMPT_KINDS = {"system", "bounded_context", "module"}


def body_lines(body: str) -> int:
    return sum(1 for line in body.splitlines() if line.strip())


def normalise(body: str) -> str:
    text = re.sub(r"\s+", " ", body.strip().lower())
    return text


def parse_updated(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def analyse(
    root: Path,
    stale_days: int = DEFAULT_STALE_DAYS,
    max_lines: int = DEFAULT_MAX_LINES,
    similarity: float = DEFAULT_SIMILARITY,
    today: date | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    index, graph, _warnings = compile_repo(root)

    inbound: dict[str, list[tuple[str, str]]] = {}
    outbound: dict[str, int] = {}
    for edge in graph["edges"]:
        inbound.setdefault(edge["to"], []).append((edge["from"], edge["type"]))
        outbound[edge["from"]] = outbound.get(edge["from"], 0) + 1

    info: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for node in index["nodes"]:
        path = root / node["path"]
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        meta = meta or {}
        size = len(raw.encode("utf-8"))
        total_bytes += size
        info[node["id"]] = {
            "node": node,
            "meta": meta,
            "body": body,
            "lines": body_lines(body),
            "bytes": size,
        }

    candidates: list[dict[str, Any]] = []

    def add(category: str, node_id: str, **extra: Any) -> None:
        item = info[node_id]
        candidates.append(
            {
                "category": category,
                "id": node_id,
                "path": item["node"]["path"],
                "kind": item["node"]["kind"],
                "status": item["node"]["status"],
                "lines": item["lines"],
                "bytes": item["bytes"],
                **extra,
            }
        )

    # --- superseded -> tombstone candidates ---
    for node_id, item in info.items():
        meta = item["meta"]
        status = item["node"]["status"]
        successors = sorted(
            set(
                [str(v) for v in _as_list(meta.get("superseded_by"))]
                + [src for src, kind in inbound.get(node_id, []) if kind == "supersedes"]
            )
        )
        if status == "deprecated" and successors:
            if item["lines"] > TOMBSTONE_MAX_LINES:
                refs = sorted(
                    {
                        f"{src} ({kind})"
                        for src, kind in inbound.get(node_id, [])
                        if kind not in ("supersedes",)
                    }
                )
                add(
                    "superseded",
                    node_id,
                    action="tombstone",
                    successors=successors,
                    inbound_to_redirect=refs,
                    saves_lines=item["lines"] - TOMBSTONE_MAX_LINES,
                    note=(
                        "fold the rationale for the change into the successor's "
                        "History, then shrink this node to a stub; keep the ID"
                    ),
                )
        elif status == "active" and any(
            kind == "supersedes" for _src, kind in inbound.get(node_id, [])
        ):
            add(
                "superseded",
                node_id,
                action="review-partial",
                successors=successors,
                saves_lines=0,
                note=(
                    "partially superseded and still active: keep the load-bearing "
                    "part, trim the replaced part, then deprecate when none remains"
                ),
            )

        if status == "deprecated" and not successors and not inbound.get(node_id):
            add(
                "dead",
                node_id,
                action="confirm-removal",
                saves_lines=item["lines"],
                note=(
                    "deprecated, no replacement, nothing references it; removal "
                    "needs user confirmation and a retired-ID note"
                ),
            )

    # --- duplicates ---
    by_kind: dict[str, list[str]] = {}
    for node_id, item in info.items():
        if item["lines"] == 0:
            continue
        by_kind.setdefault(item["node"]["kind"], []).append(node_id)

    seen_pairs: set[tuple[str, str]] = set()
    for kind, ids in by_kind.items():
        digests: dict[str, list[str]] = {}
        for node_id in ids:
            digest = hashlib.sha256(
                normalise(info[node_id]["body"]).encode("utf-8")
            ).hexdigest()
            digests.setdefault(digest, []).append(node_id)
        for group in digests.values():
            if len(group) > 1:
                group = sorted(group)
                for other in group[1:]:
                    seen_pairs.add((group[0], other))
                    add(
                        "duplicate",
                        other,
                        action="merge",
                        duplicate_of=group[0],
                        match="exact",
                        saves_lines=info[other]["lines"],
                        note="identical body; keep one, redirect edges",
                    )
        ordered = sorted(ids)
        for i, first in enumerate(ordered):
            for second in ordered[i + 1 :]:
                if (first, second) in seen_pairs:
                    continue
                a = normalise(info[first]["body"])
                b = normalise(info[second]["body"])
                if not a or not b:
                    continue
                matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
                if (
                    matcher.real_quick_ratio() >= similarity
                    and matcher.quick_ratio() >= similarity
                    and matcher.ratio() >= similarity
                ):
                    add(
                        "duplicate",
                        second,
                        action="review-merge",
                        duplicate_of=first,
                        match=f"near ({matcher.ratio():.2f})",
                        saves_lines=min(info[first]["lines"], info[second]["lines"]),
                        note="near-identical; confirm they carry the same claims",
                    )

    # --- orphans, stale, oversized ---
    for node_id, item in info.items():
        node = item["node"]
        kind = node["kind"]
        status = node["status"]
        linked = bool(inbound.get(node_id)) or bool(outbound.get(node_id))
        if kind in PROTECTED_KINDS:
            continue
        if not linked and kind not in ORPHAN_EXEMPT_KINDS and status != "deprecated":
            add(
                "orphan",
                node_id,
                action="link-or-merge",
                saves_lines=0,
                note="no edges in or out; link it, merge it, or confirm removal",
            )
        if status == "evolving":
            updated = parse_updated(item["meta"].get("updated"))
            age = (today - updated).days if updated else None
            if age is None or age >= stale_days:
                add(
                    "stale",
                    node_id,
                    action="ask-user",
                    age_days=age,
                    needs_user_confirmation=True,
                    saves_lines=item["lines"],
                    note=(
                        "evolving and not updated for "
                        f"{'an unknown time' if age is None else str(age) + ' days'}; "
                        "never remove without explicit user confirmation"
                    ),
                )
        if item["lines"] > max_lines and status != "deprecated":
            add(
                "oversized",
                node_id,
                action="refine",
                saves_lines=item["lines"] - max_lines,
                note=(
                    "body exceeds the limit; remove text that restates code, "
                    "extract flows or patterns, or split by kind"
                ),
            )

    totals: dict[str, dict[str, int]] = {}
    for item in candidates:
        bucket = totals.setdefault(item["category"], {"count": 0, "saves_lines": 0})
        bucket["count"] += 1
        bucket["saves_lines"] += int(item.get("saves_lines", 0))

    return {
        "root": str(root),
        "checked": today.isoformat(),
        "parameters": {
            "stale_days": stale_days,
            "max_lines": max_lines,
            "similarity": similarity,
        },
        "node_count": len(info),
        "total_bytes": total_bytes,
        "candidates": candidates,
        "totals": totals,
    }


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return [str(value)]


def render(report: dict[str, Any]) -> str:
    lines = [
        f"Prune analysis (read-only), checked {report['checked']}",
        f"nodes: {report['node_count']}, size: {report['total_bytes']} bytes",
        "parameters: "
        + ", ".join(f"{k}={v}" for k, v in report["parameters"].items()),
        "",
    ]
    if not report["candidates"]:
        lines.append("No prune candidates found.")
        return "\n".join(lines)
    order = ["superseded", "duplicate", "dead", "orphan", "stale", "oversized"]
    for category in order:
        items = [c for c in report["candidates"] if c["category"] == category]
        if not items:
            continue
        total = report["totals"][category]
        lines.append(
            f"## {category} ({total['count']}, up to {total['saves_lines']} lines)"
        )
        for item in items:
            detail = [f"action={item['action']}", f"status={item['status']}"]
            for key in ("successors", "duplicate_of", "match", "age_days"):
                if key in item and item[key] not in (None, []):
                    detail.append(f"{key}={item[key]}")
            if item.get("inbound_to_redirect"):
                detail.append(f"redirect={item['inbound_to_redirect']}")
            if item.get("needs_user_confirmation"):
                detail.append("NEEDS USER CONFIRMATION")
            lines.append(f"- {item['id']} [{item['path']}] " + ", ".join(detail))
            lines.append(f"    {item['note']}")
        lines.append("")
    lines.append(
        "No file was changed. Review, write a plan with an essence ledger, and "
        "apply only after the user approves."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--similarity", type=float, default=DEFAULT_SIMILARITY)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not (root / "knowledge").is_dir():
        print(f"error: no knowledge/ directory under {root}", file=sys.stderr)
        return 2
    report = analyse(root, args.stale_days, args.max_lines, args.similarity)
    print(json.dumps(report, indent=2, default=str) if args.json else render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
