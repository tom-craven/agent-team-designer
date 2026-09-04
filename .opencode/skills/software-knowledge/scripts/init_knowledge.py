#!/usr/bin/env python3
"""Scaffold the software-knowledge layout in a target repository."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"

DIRS = [
    "knowledge/contexts",
    "knowledge/capabilities",
    "knowledge/contracts",
    "knowledge/flows",
    "knowledge/decisions",
    "knowledge/invariants",
    "knowledge/patterns",
    "knowledge/runbooks",
]

COPIES = {
    "root.AGENTS.md": "AGENTS.md",
    "ARCHITECTURE.md": "ARCHITECTURE.md",
    "system.md": "knowledge/system.md",
}


def write_if_absent(path: Path, source: Path) -> str:
    if path.exists():
        return f"skip  {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, path)
    return f"add   {path}"


def write_text_if_absent(path: Path, text: str) -> str:
    if path.exists():
        return f"skip  {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return f"add   {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument(
        "--force-index",
        action="store_true",
        help="overwrite empty generated catalogs",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"root does not exist: {root}", file=sys.stderr)
        return 1

    print(f"scaffolding knowledge layout in {root}")
    for rel in DIRS:
        path = root / rel
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists() and not any(path.iterdir()):
            gitkeep.write_text("", encoding="utf-8")
        print(f"dir   {path.relative_to(root)}")

    for src_name, dest in COPIES.items():
        print(write_if_absent(root / dest, ASSETS / src_name))

    keepme = (
        "# Generated catalogs live here.\n"
        "# Run scripts/compile_graph.py after adding nodes.\n"
    )
    print(write_text_if_absent(root / "knowledge" / "README.md", keepme))
    print(
        write_text_if_absent(
            root / "knowledge" / "index.yaml",
            "nodes: []\n",
        )
    )
    print(
        write_text_if_absent(
            root / "knowledge" / "graph.yaml",
            "nodes: []\nedges: []\n",
        )
    )

    scripts_dir = root / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    for name in ("compile_graph.py", "lint_knowledge.py"):
        print(write_if_absent(scripts_dir / name, SKILL_ROOT / "scripts" / name))

    print("done. fill knowledge/system.md and AGENTS.md next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
