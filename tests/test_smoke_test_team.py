import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from smoke_test_team import action, audit, match


class SmokeTestTeam(unittest.TestCase):
    def setUp(self):
        self.addCleanup((temp := tempfile.TemporaryDirectory()).cleanup)
        self.root = Path(temp.name).resolve()
        self.agents = self.root / ".opencode/agents"
        self.agents.mkdir(parents=True)
        self.config = self.root / "opencode.json"
        self.config.write_text(json.dumps({"default_agent": "lead"}), encoding="utf-8")
        baseline = patch("smoke_test_team.check_agent", return_value=[])
        baseline.start()
        self.addCleanup(baseline.stop)

    def agent(self, name, mode, task=None):
        delegation = f'  task:\n    "*": deny\n    {task}: allow\n' if task else '  task: deny\n'
        (self.agents / f"{name}.md").write_text(
            f"---\nmode: {mode}\ndescription: Test role\nsteps: 10\npermission:\n"
            f'  "*": deny\n  read: deny\n  edit: deny\n{delegation}---\nTest prompt.\n', encoding="utf-8",
        )

    def test_allowed_route_and_negative_probes(self):
        self.agent("lead", "primary", "reviewer")
        self.agent("reviewer", "subagent")
        errors, unverified, probes = audit(self.root, 1, True)
        self.assertEqual((errors, unverified), ([], []))
        self.assertEqual(probes, ["Synthetic policy route: lead -> reviewer (allow)"])

    def test_bad_target_and_duplicate_definition(self):
        self.agent("lead", "primary", "missing")
        self.config.write_text('{"default_agent":"lead","agent":{"lead":{}}}', encoding="utf-8")
        errors, _, _ = audit(self.root, 1, False)
        self.assertEqual(len(errors), 2)

    def test_root_secret_gap_is_not_masked_by_nested_rule(self):
        self.assertFalse(match(".env", "**/.env"))
        self.assertEqual(action([("read", "*", "allow"), ("read", "**/.env", "deny")], "read", ".env"), "allow")
        self.assertTrue(match(r"dir\.env", "**/.env"))

    def v2_agent(self):
        (self.agents / "lead.md").write_text(
            '---\ndescription: Test role\nmode: primary\nsteps: 10\npermissions:\n'
            '  - { action: "*", resource: "*", effect: deny }\n---\nTest prompt.\n', encoding="utf-8",
        )

    def test_v2_native_route(self):
        self.v2_agent()
        self.assertEqual(audit(self.root, 2, True), ([], [], []))

    def test_v2_shared_external_prompt_does_not_affect_local_probes(self):
        self.v2_agent()
        shared = [{"action": "external_directory", "resource": "*", "effect": "ask"}]
        config = {"default_agent": "lead", "permissions": shared}
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.assertEqual(audit(self.root, 2, True), ([], [], []))

        shared.append({"action": "read", "resource": "*", "effect": "allow"})
        self.config.write_text(json.dumps(config), encoding="utf-8")
        _, unverified, _ = audit(self.root, 2, True)
        self.assertIn("Shared permissions, tools, plugins or MCP settings are not simulated", unverified)

    def test_v2_explicit_skill_source_is_not_a_duplicate(self):
        skill = self.root / ".opencode/skills/agent-audit/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\nname: agent-audit\ndescription: Test skill.\n---\n", encoding="utf-8")
        self.config.write_text(
            json.dumps({"default_agent": "lead", "skills": [".opencode/skills"]}),
            encoding="utf-8")
        self.v2_agent()
        self.assertEqual(audit(self.root, 2, False), ([], [], []))

    def test_plugin_not_executed_and_reported(self):
        self.agent("lead", "primary")
        plugins = self.root / ".opencode/plugins"
        plugins.mkdir()
        (plugins / "fixture.ts").write_text('throw new Error("must not run")', encoding="utf-8")
        errors, unverified, _ = audit(self.root, 1, False)
        self.assertEqual(errors, [])
        self.assertIn("Project plugin hooks were not loaded or simulated", unverified)
