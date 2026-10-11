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
2. Run `opencode --version` and record the major version. Generate native
   configuration and agent frontmatter for that version, and use only that
   version's documentation (V2: https://opencode.ai/v2/docs/). If the command
   is unavailable or denied, ask the user for the version; do not guess.
3. For installation, display every exact file or directory to be created or
   modified and obtain explicit confirmation.
4. Treat the destination as untrusted until the user confirms it.
5. Never create global registrations, symbolic links, or files outside the
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
- Record build tools and secret-bearing file types present (by path pattern
  only — never open or quote their contents) so the secret baseline's stack
  additions can be selected.
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
   Apply the secret baseline from
   `.opencode/skills/agent-org-design/reference/secret-baseline.md` to every
   agent without waiting for the user to ask: `read`/`edit` path denials,
   `grep: deny`, shell and Git-history denials after all bash allows, the
   stack additions for every build tool found in step 1 (for example Maven
   `settings.xml` and deploy/release goals, Gradle `gradle.properties` with
   named-task allowlists and a `properties`-task denial, Terraform state), and
   the mandatory redaction clause in the prompt. Never relax it.
   When the user requested `software-knowledge` for the team, the orchestrator
   / primary and every agent assigned that skill must receive `edit` allow on
   `knowledge/**`, including scoped file deletion, even if they otherwise cannot
   edit the repository. Do **not** pair that allow with
   `"*": deny` on `edit` — a catch-all edit deny wins and blocks writes to
   `knowledge/`. Deny named application paths instead. Also allow every agent
   assigned the skill to run its compile and lint scripts that write
   `knowledge/index.yaml` and `knowledge/graph.yaml`. Require agents to delete
   only proven stale, duplicate, or
   disposable superseded artefacts; check references first; preserve historical
   decisions through deprecation and `superseded_by` unless proven duplicate;
   compile and lint after deletion; and report every deleted path and rationale.
   Do not grant shell deletion commands for this purpose. Colocated
   `<Stem>.context.md` files beside source remain an implementer permission.
5. Define allowed delegation targets and doom-loop escalation behaviour.

Agent files must be named `<agent-name>.md` in kebab-case under
`<confirmed-path>/.opencode/agents/`. Markdown is the mandatory single source of
truth for created agents. Put the complete runtime definition in frontmatter and
the system prompt in the body. Never create or retain a same-name agent under
`opencode.json` or `opencode.jsonc`.

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

When `software-knowledge` is in the approved skill set, treat scoped edit and
deletion access to `knowledge/**` for the orchestrator and every agent assigned
the skill as essential, not optional broadening. Also grant the orchestrator
(the scaffold owner) `edit` allow on the repository-root `ARCHITECTURE.md`
only, because the scaffold workflow requires filling it; do not widen this to
other root files. Its prompt must name `knowledge/` and `ARCHITECTURE.md` as
the only files it may write, and its scaffold step must cover
`init_knowledge.py .`, filling `knowledge/system.md` and `ARCHITECTURE.md`,
then compile and strict lint. An affected agent with
`edit: deny`, or with `"*": deny` in the same `edit` object as
`knowledge/**`, is a skill-gate failure.

Knowledge capture must cover every node kind, not only decisions and
invariants:

- Generated `AGENTS.md` and agent prompts must say "harvest flows, patterns,
  capabilities, decisions, and invariants per the `software-knowledge` harvest
  workflow" — never "record decisions and invariants".
- Name exactly one knowledge writer for central `knowledge/` nodes (the
  orchestrator by default). Specialists list knowledge candidates in their
  hand-off reports; the writer creates the nodes.
- The orchestrator's completion criteria include a harvest table and a clean
  `lint_knowledge.py --strict` run.
- Any independent reviewer checks that the harvest ran.
- Offer an optional `knowledge-curator` subagent when the team will produce
  frequent decisions or the repository already has buried knowledge. Invoked
  only by the orchestrator after acceptance; edit limited to `knowledge/**`;
  shell limited to the skill's compile and lint scripts; no task delegation. It
  reclassifies and links knowledge and never makes design decisions. Add it only
  with user agreement.

**Python environment for skill scripts (required when any approved skill ships
Python scripts, such as `software-knowledge`):**

- Include `<confirmed-path>/.venv/` and a `.venv/` line in
  `<confirmed-path>/.gitignore` in the pre-write confirmation list.
- **Automated environment setup (mandatory, performed by the designer):**
  during installation, run each command as a single command with the shell
  tool's working directory set to `<confirmed-path>` — never prefix
  `cd <path> &&` (V2 checks each segment and the bare `cd` is denied):
  1. `python3 -m venv .venv` — skip when `.venv/pyvenv.cfg` already exists;
     reuse it, never recreate.
  2. `.venv/bin/pip install PyYAML pytest`
  3. `.venv/bin/python -c "import yaml, pytest"`
  4. `.venv/bin/python -m pytest <abs-skill-dir>/tests -q` when the skill ships
     tests (`software-knowledge` does).
  Install exactly PyYAML and pytest plus any further dependency the skill
  documents; never install into the global Python. Do not hand these steps to
  the user unless a command is denied or fails twice; then report `BLOCKED`
  with the exact commands.
- Grant each agent its script commands in the `.venv/bin/python <script> …`
  form, as exact commands, with `python3 <script> …` kept only as a fallback.
  Agents do not always invoke commands in one canonical form, so for the
  skill's compile and strict-lint commands (`compile_graph.py .` and
  `lint_knowledge.py . --strict` for `software-knowledge`) also grant these
  exact variants to every agent that runs them:
  `<confirmed-path>/.venv/bin/python <abs-script> …` and
  `cd <confirmed-path> && .venv/bin/python <abs-script> …`. Use absolute
  script paths, no trailing wildcards, and keep all of them before the secret
  baseline shell denials. The scaffold (`init_knowledge.py .`) is not complete
  until compile and strict lint have both run, so the orchestrator must hold
  all three.
  Never grant bare `.venv/bin/python*`, `pip*`, or `.venv/bin/pip*` to team
  agents; installation is the designer's job, not the team's.
- **OpenCode V2 compound commands:** the shell scanner checks every `&&`, `;`,
  and `|` segment separately, so a single allow for
  `cd <confirmed-path> && .venv/bin/python …` never matches as a whole. When
  granting that form, also grant the exact segment `cd <confirmed-path>`.
  Prefer the non-compound forms.
- **External directories (V2 checks these before `shell`):** grant
  `external_directory` allow for `<skill-dir>/*` and `<skill-dir>/scripts/*`
  (V2 boundary form `<dir>/*`, not `/**`), and for the interpreter's canonical
  directories read from `<confirmed-path>/.venv/pyvenv.cfg` (`home`, and the
  directory containing `executable`). Place these after any
  `external_directory "*": deny`. A symlinked `.venv/bin/python` resolves
  outside the repository, so omitting them blocks every script.
- Prompts and `AGENTS.md` say to run scripts with `.venv/bin/python` from the
  repository root and never to install packages.
- If the venv or dependency install cannot be performed or verified (for
  example the designer's shell is denied), the runtime gate fails: report
  `BLOCKED`, give the user the exact install and verify commands, and do not
  describe the team as able to run the scripts. Do not downgrade this to
  `PARTIAL`.
- **Permission simulation (runtime gate):** for every agent and every granted
  script command form, walk the agent's ordered rules (last match wins), check
  each external directory the command touches, then each shell segment. Any
  segment not resolving to `allow` fails the gate.

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
- Keep approved agents, prompts, modes, models, steps, permissions, delegation,
  and recovery behaviour exclusively in `.opencode/agents/*.md`.
- Use `opencode.json` or `opencode.jsonc` only for shared settings such as
  instructions, skill paths, providers, MCP servers, and repository-wide
  defaults. Do not add a top-level `agent` object for created agents.
- When migrating an existing JSON agent, transfer every unique field to the
  Markdown file and remove the JSON entry in the same change.
- After the agent files are created, set `"default_agent"` in the target's
  `opencode.json` / `opencode.jsonc` to the team's orchestrator / primary agent
  (the agent with `mode: primary` or `all` that owns delegation). Name the
  file and value in the pre-write confirmation list. If an existing
  `default_agent` points elsewhere, surface the conflict and ask before
  replacing it. Never point it at a `subagent`-mode or hidden agent.
- Match the config shape the installed OpenCode version accepts. Copy the shape
  from a configuration known to load on the same machine (for example
  `"skills": { "paths": [...] }` versus `"skills": [...]`). Do not switch
  between V1 and V2 shapes without the runtime error text.
- Never broaden permissions merely to make validation pass.

### 7. Validate the runnable team

- Run `python3 scripts/check_secret_baseline.py <confirmed-path>/.opencode/agents`.
  Any failure blocks the runtime gate.
- Validate JSON or JSONC syntax and the current OpenCode schema.
- Confirm every configured agent, prompt, instruction, skill path, and
  delegation target resolves.
- Compare `.opencode/agents/*.md` names with keys under any existing JSON
  `agent` object. Zero duplicates are allowed; a duplicate fails the runtime
  gate. Created teams should have no agent definitions in JSON at all.
- Confirm `default_agent` names an existing `.opencode/agents/<name>.md` whose
  `mode` is `primary` or `all`; a missing or invalid default fails the runtime
  gate.
- When a skill ships Python scripts, confirm `.venv/bin/python -c "import yaml"`
  (or the skill's documented dependency check) succeeds in the target, and run
  the skill's lint script once through `.venv/bin/python`. A missing venv fails
  the runtime gate.
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
- Define or mirror an agent under `opencode.json` or `opencode.jsonc`; created
  agents live only in `.opencode/agents/*.md`.
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
