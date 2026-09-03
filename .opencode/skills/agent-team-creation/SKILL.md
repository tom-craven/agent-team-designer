---
name: agent-team-creation
description: Coordinate the end-to-end creation or restructuring of a runnable AI agent team for a target repository. Use when the user asks to analyse a project, design an agent organisation, create multiple agents and required skills, or install a complete OpenCode team.
---

# Agent Team Creation

Coordinate repository analysis, organisation design, agent definition, skill
resolution, audits, OpenCode configuration, and runtime validation. Route each
specialist decision to its owning skill; do not duplicate their procedures here.

## Required routing

| Stage | Owning skill |
|---|---|
| Organisation and delegation | `agent-org-design` |
| Prompt and role definition | `prompt-patterns` |
| Model choice | `model-selection` |
| Third-party skill discovery | `find-skills-sh` |
| Skill security review | `skill-security-audit` |
| New or improved skill | `skill-creator` |
| Agent and team quality gate | `agent-audit` |
| Runnable OpenCode configuration | `opencode-agent-config` |

## Preconditions

Before writing anything:

1. Confirm the target repository and whether the user wants analysis only or
   installation.
2. For installation, display every exact file or directory to be created or
   modified and obtain explicit confirmation.
3. Treat the destination as untrusted until the user confirms it.
4. Never create global registrations, symbolic links, or files outside the
   confirmed destination.

## Lifecycle

### 1. Analyse the target project

- Read applicable `AGENTS.md` files in the repository and parent hierarchy.
- Inventory `.agents/`, `.copilot/`, `.github/`, and `.opencode/`, including
  agents, skills, prompts, instructions, and OpenCode configuration.
- Inspect applicable trusted global OpenCode and Copilot sources without reading
  credentials, tokens, private keys, or session data.
- Identify project domains, recurring workflows, risk boundaries, existing
  agents, capability gaps, and conflicting instructions.
- Produce a source inventory and evidence-based capability requirements.

Do not design roles until this evidence exists.

### 2. Design the organisation

- Load `agent-org-design`.
- Decide whether one agent is sufficient before proposing a team.
- Define one responsibility per agent, reporting lines, delegation rules,
  hand-off contracts, escalation paths, and independent review gates.
- Reuse or reshape existing agents where that is cleaner than adding roles.
- Obtain user agreement on the organisation before installation unless the user
  explicitly authorized an end-to-end implementation from an agreed brief.

### 3. Design each agent

For every approved role:

1. Load `prompt-patterns` and define purpose, scope, exclusions, workflow,
   completion evidence, blocker handling, and output contract.
2. Load `model-selection`; confirm live GitHub Copilot availability before
   setting `model` and record the required evidence, cost, alternatives, and
   date checked.
3. Derive required capabilities from the role rather than assigning a generic
   skill bundle.
4. Select mode, finite step budget, and least-privilege permissions.
5. Define allowed delegation targets and doom-loop escalation behaviour.

Agent files must be named `<agent-name>.md` in kebab-case under
`<confirmed-path>/.opencode/agents/` when Markdown agents are requested.

### 4. Resolve skill requirements

Resolve each required capability in this order:

1. Reuse a suitable audited repository-local skill.
2. Reuse a suitable trusted global skill already exposed to the repository.
3. Load `find-skills-sh` and inspect third-party candidates.
4. Load `skill-security-audit` and audit a candidate before recommending or
   installing it. Popularity and publisher reputation are not security proof.
5. Load `skill-creator` only when no suitable safe skill exists or an existing
   owned skill needs improvement.
6. Audit custom skills containing scripts, executable content, dependencies, or
   network operations before wiring them to an agent.

Record every capability as `satisfied`, `new skill required`, `optional`, or
`unresolved`. Do not silently omit unresolved essential capabilities.

### 5. Audit the complete design

- Load `agent-audit` after all proposed agents and skills are visible together.
- Block configuration on unresolved critical findings.
- Require concrete corrections for role overlap, invalid delegation, excessive
  permissions, unavailable models, missing skills, or incomplete recovery rules.

### 6. Create OpenCode configuration

- Load `opencode-agent-config` before creating or changing `opencode.json` or
  `opencode.jsonc`.
- Preserve compatible existing settings and applicable local and global
  instruction and skill sources.
- Configure the approved agents, prompts, modes, models, steps, permissions,
  delegation, and recovery behaviour.
- Never broaden permissions merely to make validation pass.

### 7. Validate the runnable team

- Validate JSON or JSONC syntax and the current OpenCode schema.
- Confirm every configured agent, prompt, instruction, skill path, and
  delegation target resolves.
- Compare runtime configuration against the approved agent definitions.
- Exercise representative routing, delegation, denial, completion, and
  doom-loop recovery cases where the environment permits.
- Report included, omitted, missing, and conflicting sources and all unverified
  assumptions.

## Stage gates

Do not advance when a gate fails:

1. **Evidence gate:** target-project analysis and source inventory are complete.
2. **Organisation gate:** roles do not overlap and delegation is explicit.
3. **Agent gate:** prompts, models, permissions, steps, and capabilities are
   justified per role.
4. **Skill gate:** essential skills exist and third-party candidates have a
   security verdict.
5. **Design audit gate:** no unresolved critical agent or team findings remain.
6. **Runtime gate:** configuration resolves and representative checks pass.

## Never do

- Create a generic god-agent instead of separating genuinely distinct jobs.
- Choose models before confirming GitHub Copilot catalogue availability.
- Create a skill before checking existing local, global, and skills.sh options.
- Recommend or install an unaudited third-party skill.
- Treat agent Markdown as a runnable team without configuring and validating
  OpenCode when installation was requested.
- Replace repository guidance with generated instructions.
- Claim completion without naming created or modified files and verification.

## Required output

Report:

1. target-project evidence and source inventory;
2. organisation chart, role boundaries, delegation, and rationale;
3. complete agent definitions and model-selection evidence;
4. capability-to-skill matrix and security verdicts;
5. audit findings and resolutions;
6. OpenCode configuration changes and source precedence;
7. validation evidence, residual risks, and exactly one final status:
   `COMPLETE`, `PARTIAL`, `BLOCKED`, or `UNSAFE TO CONTINUE`.

## Test prompts

Should trigger:

- "Analyse this repository and build an OpenCode engineering team for it."
- "Create and install an orchestrator and specialist agents with the skills they need."
- "Restructure this project's agent team and make the OpenCode configuration runnable."

Should not trigger:

- "Audit this existing reviewer agent."
- "Which Copilot model should this one agent use?"
