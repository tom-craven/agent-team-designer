"""Regression tests for knowledge-coverage lint.

Fixtures are trimmed from real capture failures where flows, patterns,
amendments, and open items were recorded only inside decisions.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from compile_graph import compile_repo
from lint_knowledge import coverage_findings, main


def node(root: Path, rel: str, meta: dict[str, object], body: str) -> None:
    path = root / "knowledge" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    base = {"name": rel, "status": "active", "updated": "2026-10-02"}
    base.update(meta)
    path.write_text(
        "---\n" + yaml.safe_dump(base, sort_keys=False) + "---\n\n" + body,
        encoding="utf-8",
    )


def findings(root: Path) -> list[str]:
    index, graph, _warnings = compile_repo(root)
    return coverage_findings(root, index, graph)


def run_lint(root: Path, *flags: str) -> int:
    old = sys.argv
    try:
        sys.argv = ["lint_knowledge.py", str(root), *flags]
        return main()
    finally:
        sys.argv = old


STEPS = (
    "## Decision\n\n"
    "1. Orchestrator receives the link request.\n"
    "2. Orchestrator verifies the Passport identity.\n"
    "3. Mismatch is rejected with 403.\n"
    "4. Orchestrator forwards to internal storage.\n"
)


def test_decision_with_step_list_and_no_flow_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(root, "decisions/0033-link.md", {"id": "decision:0033", "kind": "decision"}, STEPS)
        assert any("decision:0033" in f and "flow" in f for f in findings(root))


def test_step_list_is_clean_once_flow_is_linked() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(root, "decisions/0033-link.md", {"id": "decision:0033", "kind": "decision"}, STEPS)
        node(
            root,
            "flows/identity-link.md",
            {"id": "flow:accounts.identity-link", "kind": "flow", "decided_by": ["decision:0033"]},
            "## Steps\n\nSee decision.\n",
        )
        assert not any("ordered step list" in f for f in findings(root))


def test_pattern_language_without_pattern_node_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0040-sync.md",
            {"id": "decision:0040", "kind": "decision"},
            "Retry-safe, the same non-atomic pattern account creation uses.\n",
        )
        assert any("pattern" in f and "decision:0040" in f for f in findings(root))


def test_prose_amendment_without_supersedes_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0029-derive.md",
            {"id": "decision:0029", "kind": "decision"},
            "**Amended by decision:0036:** three values now.\n",
        )
        assert any("amendment" in f for f in findings(root))


def test_open_items_without_evolving_decision_are_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0035-migrate.md",
            {"id": "decision:0035", "kind": "decision"},
            "**Open items carried forward:** PUT semantics.\n",
        )
        assert any("open items" in f for f in findings(root))


def test_resolved_open_question_prose_is_not_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0037-derive.md",
            {"id": "decision:0037", "kind": "decision"},
            "Its third open question is settled here. This closes the open item.\n",
        )
        assert not any("open items" in f for f in findings(root))


def test_draft_history_amended_in_prose_is_not_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0042-zones.md",
            {"id": "decision:0042", "kind": "decision"},
            "- Admin reads are not flattened (amended from the first draft).\n",
        )
        assert not any("amendment" in f for f in findings(root))


def test_inbound_supersedes_satisfies_amendment() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0029-derive.md",
            {"id": "decision:0029", "kind": "decision"},
            "**Amended by decision:0036:** three values now.\n",
        )
        node(
            root,
            "decisions/0036-restricted.md",
            {"id": "decision:0036", "kind": "decision", "supersedes": ["decision:0029"]},
            "Three visibility values.\n",
        )
        assert not any("amendment" in f for f in findings(root))


def test_arrow_chain_in_prose_without_flow_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0032-topology.md",
            {"id": "decision:0032", "kind": "decision"},
            "Reached customer → Enterprise Gateway → Domain Gateway.\n",
        )
        assert any("decision:0032" in f and "flow" in f for f in findings(root))


def test_status_section_disagreeing_with_frontmatter_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0005-shape.md",
            {"id": "decision:0005", "kind": "decision", "status": "evolving"},
            "## Status\n\nActive. Operations are authored.\n",
        )
        assert any("Status section says 'active'" in f for f in findings(root))


def test_invalid_status_value_fails_lint() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "decisions/0011-old.md",
            {"id": "decision:0011", "kind": "decision", "status": "superseded"},
            "Old.\n",
        )
        assert run_lint(root) == 1


def test_guard_by_deprecated_invariant_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(
            root,
            "invariants/old.md",
            {"id": "invariant:old", "kind": "invariant", "status": "deprecated",
             "superseded_by": "invariant:new"},
            "Old rule.\n",
        )
        node(root, "invariants/new.md", {"id": "invariant:new", "kind": "invariant"}, "Rule.\n")
        node(
            root,
            "flows/build.md",
            {"id": "flow:build", "kind": "flow", "invariants": ["invariant:old"]},
            "Steps.\n",
        )
        assert any("deprecated invariant:old" in f for f in findings(root))


def test_contract_without_capability_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        node(root, "contracts/storage.md", {"id": "contract:accounts.storage", "kind": "contract"}, "Body.\n")
        assert any("contract:accounts.storage" in f for f in findings(root))
        node(
            root,
            "capabilities/manage-profile.md",
            {"id": "capability:manage-profile", "kind": "capability", "realized_by": ["contract:accounts.storage"]},
            "Body.\n",
        )
        assert not any("contract:accounts.storage" in f for f in findings(root))


def test_many_decisions_with_empty_harvest_kinds_warn_then_fail_strict() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for n in range(5):
            node(
                root,
                f"decisions/000{n}-d.md",
                {"id": f"decision:000{n}", "kind": "decision"},
                "A plain choice.\n",
            )
        found = findings(root)
        for kind in ("capability", "flow", "pattern"):
            assert any(f"no {kind} nodes" in f for f in found)
        assert run_lint(root) == 0
        assert run_lint(root, "--strict") == 1
