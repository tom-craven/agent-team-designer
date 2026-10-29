"""Regression tests for the read-only prune analyser."""

from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from prune_knowledge import analyse, main, render  # noqa: E402

TODAY = date(2026, 10, 29)
LONG = "\n".join(f"Line {i} of the old rationale." for i in range(20))


def node(root: Path, rel: str, meta: dict[str, object], body: str) -> Path:
    path = root / "knowledge" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    base = {"name": rel, "status": "active", "updated": "2026-10-20"}
    base.update(meta)
    path.write_text(
        "---\n" + yaml.safe_dump(base, sort_keys=False) + "---\n\n" + body,
        encoding="utf-8",
    )
    return path


def result(root: Path, **kwargs):
    return analyse(root, today=TODAY, **kwargs)


def by_category(report, category):
    return [c for c in report["candidates"] if c["category"] == category]


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_superseded_decision_is_a_tombstone_candidate():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0001-old.md",
             {"id": "decision:0001", "kind": "decision", "status": "deprecated",
              "superseded_by": ["decision:0002"]}, LONG)
        node(root, "decisions/0002-new.md",
             {"id": "decision:0002", "kind": "decision",
              "supersedes": ["decision:0001"]}, "Short current decision.")
        report = result(root)
        items = by_category(report, "superseded")
        assert [i["id"] for i in items] == ["decision:0001"]
        assert items[0]["action"] == "tombstone"
        assert items[0]["successors"] == ["decision:0002"]
        assert items[0]["saves_lines"] == 20 - 8


def test_existing_tombstone_is_not_reported():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0001-old.md",
             {"id": "decision:0001", "kind": "decision", "status": "deprecated",
              "superseded_by": ["decision:0002"]}, "Superseded by 0002.")
        node(root, "decisions/0002-new.md",
             {"id": "decision:0002", "kind": "decision",
              "supersedes": ["decision:0001"]}, "Current.")
        assert by_category(result(root), "superseded") == []


def test_inbound_references_to_superseded_node_are_listed_for_redirect():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0001-old.md",
             {"id": "decision:0001", "kind": "decision", "status": "deprecated",
              "superseded_by": ["decision:0002"]}, LONG)
        node(root, "decisions/0002-new.md",
             {"id": "decision:0002", "kind": "decision",
              "supersedes": ["decision:0001"]}, "Current.")
        node(root, "flows/checkout.md",
             {"id": "flow:checkout", "kind": "flow",
              "decided_by": ["decision:0001"]}, "Checkout path.")
        item = by_category(result(root), "superseded")[0]
        assert item["inbound_to_redirect"] == ["flow:checkout (decided_by)"]


def test_partially_superseded_active_node_is_review_only():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0001-old.md",
             {"id": "decision:0001", "kind": "decision"}, LONG)
        node(root, "decisions/0002-new.md",
             {"id": "decision:0002", "kind": "decision",
              "supersedes": ["decision:0001"]}, "Amends part.")
        item = by_category(result(root), "superseded")[0]
        assert item["action"] == "review-partial"
        assert item["saves_lines"] == 0


def test_exact_duplicate_detected_and_near_duplicate_reviewed():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        text = "Money is always stored as integer minor units across the system."
        node(root, "patterns/a.md", {"id": "pattern:a", "kind": "pattern"}, text)
        node(root, "patterns/b.md", {"id": "pattern:b", "kind": "pattern"}, text)
        node(root, "patterns/c.md", {"id": "pattern:c", "kind": "pattern"},
             text + " Always.")
        items = by_category(result(root), "duplicate")
        exact = [i for i in items if i["match"] == "exact"]
        near = [i for i in items if i["match"].startswith("near")]
        assert exact and exact[0]["action"] == "merge"
        assert near and all(i["action"] == "review-merge" for i in near)


def test_different_kinds_are_never_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        text = "Identical wording in two different kinds of node."
        node(root, "patterns/a.md", {"id": "pattern:a", "kind": "pattern"}, text)
        node(root, "flows/a.md", {"id": "flow:a", "kind": "flow"}, text)
        assert by_category(result(root), "duplicate") == []


def test_orphan_reported_but_protected_and_exempt_kinds_are_not():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "patterns/lonely.md",
             {"id": "pattern:lonely", "kind": "pattern"}, "Alone.")
        node(root, "invariants/rule.md",
             {"id": "invariant:rule", "kind": "invariant"}, "Rule.")
        node(root, "system.md", {"id": "system:demo", "kind": "system"}, "Sys.")
        ids = [i["id"] for i in by_category(result(root), "orphan")]
        assert ids == ["pattern:lonely"]


def test_stale_evolving_requires_user_confirmation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0005-open.md",
             {"id": "decision:0005", "kind": "decision", "status": "evolving",
              "updated": "2026-06-01"}, "Undecided.")
        node(root, "decisions/0006-fresh.md",
             {"id": "decision:0006", "kind": "decision", "status": "evolving",
              "updated": "2026-10-25"}, "Recent.")
        items = by_category(result(root), "stale")
        assert [i["id"] for i in items] == ["decision:0005"]
        assert items[0]["needs_user_confirmation"] is True
        assert items[0]["action"] == "ask-user"


def test_default_stale_threshold_is_ninety_days():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0007-edge.md",
             {"id": "decision:0007", "kind": "decision", "status": "evolving",
              "updated": "2026-07-31"}, "Edge.")  # 90 days before TODAY
        node(root, "decisions/0008-edge.md",
             {"id": "decision:0008", "kind": "decision", "status": "evolving",
              "updated": "2026-08-01"}, "Inside.")  # 89 days
        ids = [i["id"] for i in by_category(result(root), "stale")]
        assert ids == ["decision:0007"]


def test_oversized_node_reported_with_saving():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        body = "\n".join(f"Sentence {i}." for i in range(150))
        node(root, "flows/big.md", {"id": "flow:big", "kind": "flow"}, body)
        item = by_category(result(root), "oversized")[0]
        assert item["action"] == "refine"
        assert item["saves_lines"] == 30


def test_dead_deprecated_node_needs_confirmation_wording():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "patterns/gone.md",
             {"id": "pattern:gone", "kind": "pattern", "status": "deprecated"},
             "Old shape.")
        item = by_category(result(root), "dead")[0]
        assert item["action"] == "confirm-removal"


def test_analysis_never_writes_anything():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node(root, "decisions/0001-old.md",
             {"id": "decision:0001", "kind": "decision", "status": "deprecated",
              "superseded_by": ["decision:0002"]}, LONG)
        node(root, "decisions/0002-new.md",
             {"id": "decision:0002", "kind": "decision",
              "supersedes": ["decision:0001"]}, "Current.")
        before = snapshot(root)
        report = result(root)
        render(report)
        assert snapshot(root) == before


def test_cli_exit_codes(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert main([str(root)]) == 2
        node(root, "patterns/a.md", {"id": "pattern:a", "kind": "pattern"}, "x")
        assert main([str(root)]) == 0
        assert "Prune analysis (read-only)" in capsys.readouterr().out
