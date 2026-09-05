---
name: agent-audit
description: Audit existing AI agents for quality, overlap, weak descriptions, permission issues, and model fit. Use when reviewing agents, cleaning up an agent set, checking for god-agents, or improving agent definitions before shipping.
---

# Agent Audit

Systematically review agents and produce actionable findings.

## When to use
- Reviewing one or many agents
- After creating a new team of agents
- User asks to audit / improve / clean up agents

## Never do
- Give only vague advice — always propose concrete rewrites
- Ignore permission or overlap issues
- Approve a god-agent without flagging it

## Checklist (per agent)

1. **Single responsibility** — one clear job?
2. **Description** — specific and discoverable?
3. **System prompt** — clear role, boundaries, process?
4. **Permissions** — least privilege? (edit/bash/task/skill)
5. **Mode** — primary vs subagent appropriate?
6. **Model fit** — use `model-selection`
7. **Overlap** — conflicts with another agent?
8. **Project fit** — justified by target-repository workflows and constraints?
9. **Skill coverage** — required capabilities mapped to available, audited skills?
10. **Delegation validity** — targets exist, are allowed, and have hand-off contracts?
11. **Step budget** — finite, proportionate, and sufficient for verification?
12. **Recovery** — bounded retries, blocker handling, doom-loop escalation, and final statuses?

## Team-level gate

After reviewing agents individually, verify the assembled team:

- covers required project capabilities without duplicate ownership;
- has one clear completion owner for every workflow;
- separates implementation from independent risk gates where appropriate;
- contains no undeclared or circular delegation;
- does not rely on unavailable models, missing paths, or unaudited third-party skills;
- can produce a useful handoff when permissions, dependencies, or steps block work;
- if `software-knowledge` is installed, the orchestrator / primary can write
  `knowledge/**` and run the skill compile/lint scripts, with no
  `"*": deny` on the same `edit` object.

Treat unresolved unavailable models, essential missing skills, dangerous
permissions, invalid delegation, responsibility collisions, and an
orchestrator that cannot write `knowledge/` while `software-knowledge` is
required as critical.

## Report format

```markdown
# Agent Audit Report

## Summary
- Agents reviewed: N
- Critical: N | Needs improvement: N | Good: N

## Findings

### `agent-name`
- **Status**: Good | Needs Improvement | Critical
- **Issues**: ...
- **Recommended rewrite**: (concrete frontmatter + prompt changes)

## Overlap & structure issues
- ...

## Prioritised actions
1. ...

## Release gate
- Ready for configuration | Blocked
- Blocking findings: ...
```

Be direct. Prefer concrete patches over general commentary.
