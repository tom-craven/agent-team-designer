"""Tests for scripts/check_secret_baseline.py (V1 maps and V2 rule lists)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_secret_baseline.py"
spec = importlib.util.spec_from_file_location("check_secret_baseline", SCRIPT)
csb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csb)

BODY = "\n- Never print secrets; write `[REDACTED]` instead.\n"


def rule(action: str, resource: str, effect: str) -> str:
    return f'  - action: {action}\n    resource: "{resource}"\n    effect: {effect}\n'


def v2_agent(extra_tail: str = "", shell_allow: bool = True) -> str:
    rules = rule("read", "*", "allow")
    rules += "".join(rule("read", p, "deny") for p in csb.REQUIRED_PATH_DENIES)
    rules += "".join(rule("edit", p, "deny") for p in csb.REQUIRED_PATH_DENIES)
    rules += rule("grep", "*", "deny")
    rules += rule("shell", "*", "deny")
    if shell_allow:
        rules += rule("shell", "mvn test*", "allow")
    rules += "".join(rule("shell", p, "deny") for p in csb.REQUIRED_BASH_DENIES)
    rules += extra_tail
    return f"---\ndescription: x\nmode: subagent\npermissions:\n{rules}---\n{BODY}"


def check(tmp_path: Path, text: str) -> list[str]:
    f = tmp_path / "agent.md"
    f.write_text(text, encoding="utf-8")
    return csb.check_agent(f)


def test_v2_compliant_agent_passes(tmp_path):
    assert check(tmp_path, v2_agent()) == []


def test_v2_trailing_allow_overrides_secret_deny(tmp_path):
    errs = check(tmp_path, v2_agent(rule("read", "**", "allow")))
    assert any("read: secret path **/.env" in e for e in errs)


def test_v2_wildcard_action_allow_overrides(tmp_path):
    errs = check(tmp_path, v2_agent(rule("*", "*", "allow")))
    assert any(e.startswith("grep") for e in errs)
    assert any("shell: missing deny" in e for e in errs)


def test_v2_shell_deny_before_allow_fails(tmp_path):
    errs = check(tmp_path, v2_agent(rule("shell", "git status*", "allow")))
    assert any("must come after all allows" in e for e in errs)


def test_v2_unscoped_shell_allow_fails(tmp_path):
    text = v2_agent().replace('resource: "mvn test*"', 'resource: "git diff*"')
    assert any("unscoped allow" in e for e in check(tmp_path, text))


def test_v2_inline_rules_parse(tmp_path):
    text = v2_agent().replace(
        rule("grep", "*", "deny"),
        '  - { action: grep, resource: "*", effect: deny }\n')
    assert check(tmp_path, text) == []


def test_v2_legacy_bash_action_alias(tmp_path):
    text = v2_agent().replace("action: shell", "action: bash")
    assert check(tmp_path, text) == []


def test_missing_redaction_clause_fails(tmp_path):
    text = v2_agent().replace("[REDACTED]", "redacted")
    assert any(e.startswith("prompt:") for e in check(tmp_path, text))


def test_mixed_formats_fail(tmp_path):
    text = v2_agent().replace("mode: subagent\n", "mode: subagent\npermission:\n  edit: deny\n")
    assert any("mixes V1" in e for e in check(tmp_path, text))


def test_v1_agent_still_checked(tmp_path):
    text = "---\ndescription: x\npermission:\n  grep: allow\n---\n" + BODY
    errs = check(tmp_path, text)
    assert any(e.startswith("read must be") for e in errs)
    assert any(e.startswith("grep must be deny") for e in errs)
