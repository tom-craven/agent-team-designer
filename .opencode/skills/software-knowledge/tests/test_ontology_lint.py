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


def write_type_node(root: Path, relative_path: str, source: str, node_id: str) -> None:
    source_path = root / source
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("class Order:\n    pass\n", encoding="utf-8")
    context_path = root / relative_path
    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(
        "---\n"
        f"id: {node_id}\n"
        "kind: type\n"
        "name: Order\n"
        f"source: {source}\n"
        "status: active\n"
        "updated: 2026-09-08\n"
        "---\n\n# Order\n\nOwns an order.\n",
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


def test_source_tree_context_node_is_compiled_and_linted() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_type_node(
            root,
            "src/orders/Order.context.md",
            "src/orders/order.py",
            "type:orders.order",
        )

        index, graph, warnings = compile_repo(root)

        assert not warnings
        assert index["nodes"] == [
            {
                "id": "type:orders.order",
                "kind": "type",
                "name": "Order",
                "path": "src/orders/Order.context.md",
                "status": "active",
                "source": "src/orders/order.py",
                "bounded_context": None,
                "owners": [],
                "tags": [],
            }
        ]
        assert graph["nodes"] == [
            {
                "id": "type:orders.order",
                "kind": "type",
                "path": "src/orders/Order.context.md",
            }
        ]
        old_argv = sys.argv
        try:
            sys.argv = ["lint_knowledge.py", str(root)]
            assert main() == 0
        finally:
            sys.argv = old_argv


def test_context_node_elsewhere_under_opencode_is_not_excluded() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_type_node(
            root,
            ".opencode/project/Order.context.md",
            ".opencode/project/order.py",
            "type:opencode.order",
        )

        index, _graph, warnings = compile_repo(root)

        assert not warnings
        assert {node["id"] for node in index["nodes"]} == {"type:opencode.order"}
