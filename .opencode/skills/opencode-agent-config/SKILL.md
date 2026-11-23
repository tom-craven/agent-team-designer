---
name: opencode-agent-config
description: Configure shared OpenCode settings (opencode.json instructions, the skills array or legacy skill paths, providers, MCP, defaults) and validate or audit Markdown agents under .opencode/agents/, including modes, models, steps, permissions, delegation, and stuck-agent recovery. Also migrates legacy JSON agents to Markdown. Use when creating or changing opencode.json for a team, auditing agent runtime behaviour, or diagnosing step limits and permission deadlocks.
---

# OpenCode Agent Configuration

Use this skill to configure shared OpenCode settings and validate Markdown agent
runtime behaviour. This team creates agents only as `.opencode/agents/*.md`.
Run `opencode --version` first: V2 (https://opencode.ai/v2/docs/) is the native
target, and V1 shapes are emitted only for a target that explicitly runs
OpenCode v1. The authoritative references are
https://opencode.ai/v2/docs/agents and https://opencode.ai/v2/docs/permissions;
re-check them when the schema or documented options may have changed.

## Instruction and skill source discovery

Every team creation or installation must inventory guidance before generating
configuration. The resulting configuration must preserve access to applicable
skills and instructions at both repository-local and global scopes. Treat the
following as input sources, in precedence order:

1. Target repository: applicable `AGENTS.md`, plus the repository roots
   `.agents/`, `.copilot/`, `.opencode/`, and `.github/`. Inspect their
   instructions, prompts, skills, agents, and existing OpenCode config.
2. Global roots: `~/.agents/`, `~/.copilot/`, `~/.config/opencode/`, and
   `~/.github/`, including global agents, instructions, prompts, skills, and
   configuration where present.
3. Global GitHub/Copilot: `~/.copilot/copilot-instructions.md`,
   `~/.copilot/instructions/`, `~/.copilot/prompts/`, and trusted global skill
   directories such as `~/.agents/skills/` when present.

Inspect the actual paths; do not assume they exist. Never read auth files,
tokens, session databases, private keys, or credential directories while
discovering sources. Do not include broad home-directory globs.

When producing a repository configuration:

- Preserve existing compatible settings instead of overwriting them.
- Merge applicable repository-local and global sources into `instructions` and
  the `skills` array (V1: `skills.paths`); do not configure only one scope when
  both are available.
- Prefer absolute paths for global sources and repository-relative paths for
  target-repository sources where supported by OpenCode.
- Include repository-local `.agents`, `.copilot`, `.opencode`, and `.github`
  guidance when applicable, while retaining compatible global sources. Before
  adding a skill source, compare path-derived V2 IDs across auto-discovered and
  explicit sources. A later source wins; never let a Copilot adapter shadow
  its canonical OpenCode skill. Confirm intentional canonical overrides and
  verify the selected definition, not just the presence of its ID.
- Report missing, omitted, conflicting, and included sources.
- Do not copy or vendor global/third-party skills unless explicitly requested;
  reference trusted paths instead.
- Apply repository-local guidance as the narrower rule when sources conflict.

The final audit must verify that every configured agent definition, instruction
path, skill path, and delegation target exists or is intentionally documented as
missing. It must also verify that the resulting configuration does not expose
secrets or unrelated private directories.

## Mandatory single source of truth

For every team created or modified by `agent-team-designer`:

- Define agents only in `.opencode/agents/<agent-name>.md`.
- Put the complete description, mode, model, steps, color, permissions, and
  prompt in the Markdown definition. In V2 the prompt is the body and any model
  variant is written into `model` as `provider/model#variant`.
- Do not add created agents to the top-level `agents` object (V1: `agent`) in
  `opencode.json` or `opencode.jsonc`.
- Reserve JSON/JSONC for shared settings: instructions, the `skills` array,
  providers, MCP servers, and repository-wide defaults.
- Inventory both sources before changes. If the same name exists in Markdown and
  JSON, treat it as a blocking duplicate. Migrate all unique JSON fields into
  Markdown, then remove the JSON entry in the same change.
- Do not rely on undocumented precedence or nested-object merge behaviour.

The JSON agent shape below is reference material for auditing legacy
configurations only; do not use it when creating a team.

### JSON agent shape (V2 reference)

Native V2 agents live under the top-level `agents` object; the agent key becomes
the agent name. File-based Markdown remains the required source of truth for
this team, so use this shape only to audit or migrate a JSON configuration.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "agents": {
    "agent-name": {
      "description": "One searchable sentence describing what this agent does and when to use it.",
      "mode": "subagent",
      "model": "provider/model-id#variant",
      "system": "The complete system prompt.",
      "steps": 30,
      "permissions": [
        { "action": "edit", "resource": "*", "effect": "allow" },
        { "action": "shell", "resource": "*", "effect": "ask" },
        { "action": "shell", "resource": "git status *", "effect": "allow" },
        { "action": "subagent", "resource": "*", "effect": "deny" },
        { "action": "skill", "resource": "*", "effect": "allow" }
      ],
      "color": "#2563EB"
    }
  }
}
```

V1 used the singular `agent` map with `prompt`, `permission`, `bash`, and
`task`. Read those only when auditing a legacy configuration; do not emit them
for a V2 target.

Use `steps`, not the deprecated `maxSteps`. If `steps` is omitted, the agent
continues until the model stops or the user interrupts. Set a finite value for
bounded workflows, but leave enough budget for inspection, implementation, and
verification. A step limit causes a summarisation response; it does not make an
unfinished task complete.

## Design procedure

1. Inspect the existing `opencode.json`/`opencode.jsonc`, `.opencode/agents/`, nearby prompt files,
   Markdown agents, project instructions, repository `.github` guidance, and
   configured global OpenCode/GitHub/Copilot sources before proposing changes.
2. Decide whether the agent is `primary`, `subagent`, or `all`.
   - `primary`: directly selectable main assistant.
   - `subagent`: callable by a primary agent or user mention.
   - `all`: usable in either role.
3. Give it one responsibility and a specific, discoverable description.
4. Select a model only after confirming provider availability and current evidence.
5. Keep the system prompt in the Markdown agent body. Do not split the same
   agent's configuration between Markdown and JSON.
6. Apply least-privilege permissions. Prefer explicit command patterns over an
   unrestricted shell allow (`shell: "*": "allow"` in V2, `bash: "allow"` in
   V1). When `software-knowledge` is configured for the team, the orchestrator /
   primary and every agent assigned that skill must have `edit` allow on
   `knowledge/*`. Verify a deletion-capable file tool separately. In V2 order that
   allow **after** the broad `edit` deny or ask; never use the V1 catch-all
   `"*": deny` map, where the catch-all wins. Every agent assigned the skill
   must also have shell allow for that skill's `compile_graph.py` and
   `lint_knowledge.py` scripts. Do not allow shell deletion commands solely for
   knowledge maintenance. Require prompts to limit deletion to proven stale,
   duplicate, or disposable superseded artefacts, check references, preserve
   historical decisions unless proven duplicate, compile and lint after
   deletion, and report deleted paths and rationale.
   For OpenCode V2, also grant `external_directory` allow for the skill's
   directory and `scripts/` directory in `<dir>/*` form and for the venv
   interpreter's canonical directories (from `.venv/pyvenv.cfg`). V2 checks
   each segment of a compound shell command separately, so a
   `cd <repo> && <script>` allow needs a separate exact `cd <repo>` allow.
7. Set `steps` based on the workflow. For implementation, reserve steps for
   repository inspection, edits, tests, and final reporting.
8. Validate that delegation targets named in `subagent` rules (V1:
   `permission.task`) actually exist.
9. Test the configuration with a representative prompt and verify the agent's
   final status, tool access, and handoff evidence.

Use this skill only after the organisation, agent definitions, model choices,
skill resolution, and design audit are complete when creating a team. OpenCode
configuration implements an approved design; it must not silently invent roles,
skills, delegation, or broader permissions to fill design gaps.

## Permissions

V2 uses one ordered `permissions` list of `action` / `resource` / `effect`
rules, and the **last matching rule wins**, so put broad rules first and
specific exceptions after. V1 groups effects by tool in a `permission` map.
Never mix the two shapes in one agent.

Effects are `allow`, `ask`, and `deny`; no matching rule means `ask`.

V2 actions for the built-in tools:

| Action | Resource |
|---|---|
| `read` | Path to read |
| `edit` | Target path for edit, write, and patch |
| `glob` | Requested glob pattern |
| `grep` | Requested regular expression, not the search path |
| `list` | Directory to list |
| `shell` | Scanner-produced command string |
| `subagent` | Target agent ID |
| `skill` | Skill ID |
| `question` | `*` |
| `webfetch` / `websearch` | URL / query |
| `external_directory` | External directory boundary, normally `<dir>/*` |
| `<server>_<tool>` | MCP tool |

`doom_loop` and `lsp` are not V2 permission actions.

V2 path matching: `*` matches zero or more characters **including `/`**, and
`?` matches one character. There is no `**` token. A `**/` prefix does not match
a root-level file, so `**/.env` leaves `.env` readable. Write whole-path
patterns (`*.env`, `*settings.xml`, `*.kube/*`) and probe realistic paths.

Two V2 defaults matter for least privilege:

- Every agent starts with a base allow policy; `.env` reads ask by default.
- `external_directory` is **allowed** by default, where V1 asked. Add
  `{ "action": "external_directory", "resource": "*", "effect": "ask" }` when
  the agent must not leave the project silently.

For `edit`, order matters. Place the broad `edit` rule first, then the
`knowledge/*` allow:

```yaml
- action: edit
  resource: "*"
  effect: deny
- action: edit
  resource: "knowledge/*"
  effect: allow
```

For every agent assigned `software-knowledge`, allow `knowledge/*` (and report
paths) and deny named application trees instead. The permission is necessary
but does not supply a tool. V2 `patch` supports deletion only where the selected
model exposes it; `edit` and `write` alone do not. If scoped deletion cannot be
verified, block the skill gate; do not grant shell deletion as a fallback.

For Gradle repositories, assume `gradle.properties` may contain credentials.
Every agent and the repository-wide configuration must deny both
`gradle.properties` and `*gradle.properties` through the `read` action and deny
edits to the same paths. Deny direct shell disclosure (`cat`, `type`,
`Get-Content`, `grep`, `rg`, and equivalents) and indirect disclosure through
unrestricted Git diff, log, or show commands. Do not allow unrestricted
content-search tools when they cannot enforce a path exclusion. Do not allow unrestricted
`gradlew *`; allow only named build and verification tasks, and deny publish,
release, push, and property-reporting operations after the allow rules so the
last match wins. A Gradle process may internally consume project properties, so
task allowlisting is required in addition to file-read denial.

```yaml
- action: shell
  resource: "*"
  effect: deny
- action: shell
  resource: "git status *"
  effect: allow
- action: shell
  resource: "npm test *"
  effect: allow
```

OpenCode V2 has no `doom_loop` permission action. Stuck-agent recovery is
governed entirely by the prompt-level completion protocol below, so never cite
a recovery permission as the safety net and never delete the protocol to hide
symptoms. V1 agents may still carry `doom_loop`; treat it as legacy when you
audit one.

Delegation is a `subagent` action in V2:

```yaml
- action: subagent
  resource: "*"
  effect: deny
- action: subagent
  resource: "backend-engineer"
  effect: allow
- action: subagent
  resource: "code-reviewer"
  effect: allow
```

A `subagent` deny removes the target from the delegation tool description. This
is useful for specialists that must not delegate. Direct user `@` mentions
remain possible, so prompt boundaries still matter.

## Doom-loop escalation report

A doom loop is a design signal, not just a runtime nuisance. It usually means
the agent is missing a capability, a permission, a delegation target, an
instruction, or a decision it is not allowed to make. Every agent prompt must
therefore require the agent to **stop and write a structured escalation report**
when it detects, or is told, that it is looping.

### Detection triggers

Require the agent to treat any of these as a doom loop:

- the same tool or command failing twice with the same error;
- repeating a search, read, or investigation without new information;
- being unable to proceed because a permission returns `deny` or repeatedly `ask`;
- a needed specialist, skill, model, or path being unavailable;
- oscillating between two approaches without converging;
- the agent noticing that it has issued the same call for the third time.

### Required behaviour on detection

1. Stop the current approach immediately; do not retry a third time.
2. Write the escalation report to a file rather than only printing it, so the
   user can hand it back to `agent-team-designer`.
3. Default path: `.opencode/reports/doom-loop-<agent-name>-<YYYYMMDD-HHMM>.md`
   inside the repository the agent is working in. If that directory cannot be
   created, report the content inline and say where it could not be written.
4. Finish the turn with status `BLOCKED` and name the report path.

The agent must therefore have `edit` access to its report directory, or the
configuration must document that reports will be returned inline only. In V2
place that allow after the broad `edit` rule.

### Report template

```markdown
# Doom Loop Escalation Report

- Agent: <agent-name>
- Repository: <absolute path>
- Timestamp: <ISO 8601>
- Detected by: <self-detected | user>

## Objective
<the task the agent was asked to complete>

## Where it stalled
<the precise step, file, command, or decision point>

## Loop evidence
<the repeated actions, with the identical error or identical result each time>

## Suspected root cause
Select all that apply and justify each:
- [ ] Missing skill or capability: <which capability, and what it would need to do>
- [ ] Missing or denied permission: <exact V2 action and resource, or V1 gate and pattern>
- [ ] Missing delegation target: <specialist that should exist or be allowed>
- [ ] Step budget exhausted: <steps configured vs. work required>
- [ ] Ambiguous or conflicting instructions: <which sources conflict>
- [ ] Missing project context: <instruction or documentation gap>
- [ ] Model limitation: <what the model failed to do reliably>
- [ ] External blocker: <credential, network, service, or environment>

## Requested change
<the smallest concrete configuration, permission, skill, or prompt change that
would unblock this work>

## Proposed configuration delta
<exact JSON or front-matter fragment, if known>

## Safety note
<anything that must not be granted, e.g. do not widen shell to "*": "allow">

## What was completed before stalling
<files changed, verified behaviour, and anything left in a partial state>
```

### Handback to agent-team-designer

The report is designed to be read by the `agent-team-designer` agent. When the report
identifies a missing capability, route it to `skill-creator` or `find-skills-sh`
plus `skill-security-audit`. When it identifies a permission, step, model, or
delegation problem, route it back through this skill. When it identifies
overlapping or ambiguous responsibilities, route it to `agent-audit` or
`agent-org-design`.

Never resolve a doom loop by granting blanket `shell: "*": "allow"`, removing
the prompt's completion protocol, or raising `steps` without evidence that step
exhaustion was the actual cause.

## Anti-stall requirements

Every agent prompt should define:

- the assigned objective and scope;
- when to ask a clarification question;
- a bounded retry rule for failed tools or commands;
- a rule against repeating the same investigation indefinitely;
- what to do when a dependency or specialist is unavailable;
- explicit statuses such as `COMPLETE`, `PARTIAL`, `BLOCKED`, and
  `UNSAFE TO CONTINUE`;
- doom-loop detection triggers and the requirement to write an escalation report
  instead of continuing to retry;
- exact verification evidence required before claiming completion.

Configuration can limit execution with `steps`, but it cannot replace these
prompt instructions. If an agent reaches its step limit, its output must be
treated as a handoff or partial result until the completion gates are checked.

## Audit checklist

- Is `description` present, specific, and searchable?
- Is the mode appropriate?
- Is the model ID valid for the configured provider, including any variant?
- Is the agent's `permissions` list (V2) or `permission` map (V1) complete and
  well-formed, with no mixed formats?
- Is `steps` finite and proportionate to the task?
- Are edit, shell, external-directory, skill, and subagent permissions
  least-privilege?
- Do ordered permission rules put the broad rule first and specific exceptions
  after?
- Are delegation targets real and non-overlapping?
- If the agent can be stuck, does the prompt define detection triggers and
  require a written escalation report at a stated path? (V2 has no `doom_loop`
  action; the prompt is the only recovery mechanism.)
- Can the agent actually write that report, or is inline-only fallback documented?
- Does the prompt define completion, blocker handling, and evidence requirements?
- Are deprecated `tools`, `maxSteps`, `temperature`, and `prompt` fields being
  avoided or migrated?
- Were repository `.agents`, `.copilot`, `.opencode`, and `.github`
  instructions and skills discovered and configured?
- Were global `~/.agents`, `~/.copilot`, `~/.config/opencode`, and `~/.github`
  sources discovered without reading credentials or session data?
- Are local/global precedence and any conflicts documented?
- Are all configured instruction and skill paths valid and appropriately scoped?
- Does the configuration match the approved organisation and complete agent definitions?
- Is every created agent defined exactly once under `.opencode/agents/`, with no
  same-name JSON entry and no agent fields split across representations?
- Did the design audit release the team for configuration with no unresolved critical findings?
- Do representative routing, delegation, denial, completion, and doom-loop cases behave as designed?

## Required output

When designing or changing an agent, provide:

1. the complete Markdown agent files and frontmatter;
2. any agent-body prompt changes;
3. the complete `instructions` and `skills` array changes (V1: `skills.paths`),
   with source precedence and included/omitted/missing paths;
4. permission and step-limit rationale;
5. migration notes for deprecated or conflicting settings;
6. the doom-loop escalation rule applied, including the report path and any
   permission needed to write it;
7. a verification prompt and expected completion behaviour.
8. runtime validation evidence for syntax/schema, path resolution, delegation,
   denied operations, completion, and recovery, or an explicit list of checks
   that could not be performed.

Never create or mirror agent definitions in JSON. Never silently edit
configuration. Never claim an agent is fixed without testing
the relevant permission, delegation, and completion paths.
