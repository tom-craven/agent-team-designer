from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import sync_copilot_adapters as sync


VALID_FRONTMATTER = """---
name: agent-team-designer
description: Designs and audits agents.
model: gpt-5.6-terra
tools:
  - read
  - search
  - web
---

Prompt.
"""


class SyncCopilotAdaptersTest(unittest.TestCase):
    def test_digest_is_independent_of_line_endings(self) -> None:
        lf = b"first\nsecond\n"
        crlf = b"first\r\nsecond\r\n"
        cr = b"first\rsecond\r"

        self.assertEqual(sync.normalized_digest(lf), sync.normalized_digest(crlf))
        self.assertEqual(sync.normalized_digest(lf), sync.normalized_digest(cr))

    def test_valid_agent_metadata_passes(self) -> None:
        metadata = sync.parse_agent_frontmatter(VALID_FRONTMATTER)

        self.assertEqual([], sync.validate_agent_metadata(metadata))

    def test_wrong_name_and_empty_description_fail(self) -> None:
        metadata = sync.parse_agent_frontmatter(VALID_FRONTMATTER)
        metadata["name"] = "wrong-agent"
        metadata["description"] = ""

        errors = sync.validate_agent_metadata(metadata)

        self.assertIn("Copilot agent name must be agent-team-designer", errors)
        self.assertIn(
            "Copilot agent description must be a non-empty string", errors
        )

    def test_yaml_non_string_description_fails(self) -> None:
        for value in ("null", "false", "0", "[]", "{}"):
            with self.subTest(value=value):
                invalid = VALID_FRONTMATTER.replace(
                    "description: Designs and audits agents.",
                    f"description: {value}",
                )
                with self.assertRaisesRegex(ValueError, "must be a string"):
                    sync.parse_agent_frontmatter(invalid)

    def test_duplicate_and_unsupported_frontmatter_fail(self) -> None:
        duplicate = VALID_FRONTMATTER.replace(
            "description: Designs and audits agents.\n",
            "description: Designs and audits agents.\ndescription: Duplicate.\n",
        )
        unsupported = VALID_FRONTMATTER.replace(
            "name: agent-team-designer", '"name": agent-team-designer'
        )

        with self.assertRaisesRegex(ValueError, "duplicate"):
            sync.parse_agent_frontmatter(duplicate)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            sync.parse_agent_frontmatter(unsupported)

    def test_missing_adapter_and_stale_fingerprint_report_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in sync.CANONICAL_SKILLS:
                skill = root / ".opencode" / "skills" / name / "SKILL.md"
                skill.parent.mkdir(parents=True, exist_ok=True)
                skill.write_text(
                    f"---\nname: {name}\ndescription: Test {name}.\n---\n"
                )

            source_agent = root / sync.SOURCE_AGENT
            source_agent.parent.mkdir(parents=True, exist_ok=True)
            source_agent.write_text("canonical agent\n")

            copilot_agent = root / sync.COPILOT_AGENT
            copilot_agent.parent.mkdir(parents=True, exist_ok=True)
            copilot_agent.write_text(
                VALID_FRONTMATTER.replace(
                    "\nPrompt.\n",
                    "\n<!-- Canonical OpenCode agent SHA-256: "
                    + "0" * 64
                    + " -->\n\nPrompt.\n",
                )
            )

            with patch.object(sync, "ROOT", root):
                errors = sync.validate()

        self.assertTrue(
            any("missing generated adapter" in error for error in errors)
        )
        self.assertTrue(
            any("--accept-agent-source" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
