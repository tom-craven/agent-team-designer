from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from compile_graph import compile_repo
from lint_knowledge import documented_edge_keys, main


def write_node(root: Path, frontmatter: dict[str, object]) -> None:
    path = root / "knowledge" / "decisions" / "0001-test.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False)
        + "---\n\n# Test\n\nDecision body.\n",
        encoding="utf-8",
    )


def test_applies_to_is_compiled_and_not_reported_as_unknown() -> None:
    assert "applies_to" in documented_edge_keys()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_node(
            root,
            {
                "id": "decision:0001",
                "kind": "decision",
                "name": "Test",
                "status": "active",
                "updated": "2026-09-07",
                "applies_to": ["module:orders"],
            },
        )
        _index, graph, warnings = compile_repo(root)
        assert not warnings
        assert {edge["type"] for edge in graph["edges"]} == {"applies_to"}


def test_unknown_frontmatter_key_fails_lint() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_node(
            root,
            {
                "id": "decision:0001",
                "kind": "decision",
                "name": "Test",
                "status": "active",
                "updated": "2026-09-07",
                "applies_to": [],
                "not_an_ontology_key": [],
            },
        )
        import sys

        old_argv = sys.argv
        try:
            sys.argv = ["lint_knowledge.py", str(root)]
            assert main() == 1
        finally:
            sys.argv = old_argv


def test_opencode_skill_type_template_is_not_compiled_or_linted() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_node(
            root,
            {
                "id": "decision:0001",
                "kind": "decision",
                "name": "Test",
                "status": "active",
                "updated": "2026-09-07",
                "applies_to": [],
            },
        )
        template = (
            root
            / ".opencode"
            / "skills"
            / "software-knowledge"
            / "assets"
            / "type.context.md"
        )
        template.parent.mkdir(parents=True)
        template.write_text(
            "---\n"
            "id: type:context.typename\n"
            "kind: type\n"
            "name: TypeName\n"
            "source: src/context/type_name.py\n"
            "status: evolving\n"
            "updated: 2026-09-07\n"
            "---\n\n# TypeName\n",
            encoding="utf-8",
        )
        index, graph, warnings = compile_repo(root)
        assert not warnings
        assert {node["id"] for node in index["nodes"]} == {"decision:0001"}
        assert graph["edges"] == []
        old_argv = sys.argv
        try:
            sys.argv = ["lint_knowledge.py", str(root)]
            assert main() == 0
        finally:
            sys.argv = old_argv
