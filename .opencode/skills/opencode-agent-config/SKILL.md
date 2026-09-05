---
name: opencode-agent-config
description: Define, audit, and migrate OpenCode agents in opencode.json, including modes, prompts, models, steps, permissions, task delegation, visibility, and stuck-agent recovery. Use whenever configuring agents in JSON rather than Markdown files or diagnosing agent execution limits and permission deadlocks.
---

# OpenCode Agent Configuration

Use this skill for agent definitions stored in `opencode.json` or `opencode.jsonc`.
The authoritative reference is https://opencode.ai/docs/agents. Re-check it when
the configuration schema or documented options may have changed.

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
  `skills.paths`; do not configure only one scope when both are available.
- Prefer absolute paths for global sources and repository-relative paths for
  target-repository sources where supported by OpenCode.
- Include repository-local `.agents`, `.copilot`, `.opencode`, and `.github`
  sources explicitly when they exist, while retaining global sources from
  `~/.agents`, `~/.copilot`, `~/.config/opencode`, and `~/.github`.
- Report missing, omitted, conflicting, and included sources.
- Do not copy or vendor global/third-party skills unless explicitly requested;
  reference trusted paths instead.
- Apply repository-local guidance as the narrower rule when sources conflict.

The final audit must verify that every configured prompt path, instruction path,
skill path, and delegation target exists or is intentionally documented as
missing. It must also verify that the resulting configuration does not expose
secrets or unrelated private directories.

## Configuration shape

Agents are configured under the top-level `agent` object. The agent key becomes
the agent name.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "agent-name": {
      "description": "One searchable sentence describing what this agent does and when to use it.",
      "mode": "subagent",
      "model": "provider/model-id",
      "prompt": "{file:./prompts/agent-name.txt}",
      "temperature": 0.2,
      "steps": 30,
      "permission": {
        "edit": "allow",
        "bash": {
          "*": "ask",
          "git status *": "allow"
        },
        "task": "deny",
        "skill": "allow"
      },
      "color": "#2563EB"
    }
  }
}
```

Use `steps`, not the deprecated `maxSteps`. If `steps` is omitted, the agent
continues until the model stops or the user interrupts. Set a finite value for
bounded workflows, but leave enough budget for inspection, implementation, and
verification. A step limit causes a summarisation response; it does not make an
unfinished task complete.

## Design procedure

1. Inspect the existing `opencode.json`/`opencode.jsonc`, nearby prompt files,
   Markdown agents, project instructions, repository `.github` guidance, and
   configured global OpenCode/GitHub/Copilot sources before proposing changes.
2. Decide whether the agent is `primary`, `subagent`, or `all`.
   - `primary`: directly selectable main assistant.
   - `subagent`: callable by a primary agent or user mention.
   - `all`: usable in either role.
3. Give it one responsibility and a specific, discoverable description.
4. Select a model only after confirming provider availability and current evidence.
5. Use a prompt file for substantial prompts; use an inline prompt only when it
   is short and stable. The `{file:...}` path is relative to the config file.
6. Apply least-privilege permissions. Prefer explicit command patterns over
   unrestricted `bash: "allow"`. When `software-knowledge` is configured for
   the team, the orchestrator / primary must have `edit` allow on
   `knowledge/**` and bash allow for that skill's `compile_graph.py` and
   `lint_knowledge.py` scripts. Do not keep a blanket `edit: deny` or
   `"*": deny` on `edit` for that orchestrator — the catch-all deny wins
   and blocks knowledge-graph writes.
7. Set `steps` based on the workflow. For implementation, reserve steps for
   repository inspection, edits, tests, and final reporting.
8. Validate that delegation targets named in `permission.task` actually exist.
9. Test the configuration with a representative prompt and verify the agent's
   final status, tool access, and handoff evidence.

Use this skill only after the organisation, agent definitions, model choices,
skill resolution, and design audit are complete when creating a team. OpenCode
configuration implements an approved design; it must not silently invent roles,
skills, delegation, or broader permissions to fill design gaps.

## Permissions

Permission values are `allow`, `ask`, or `deny`. Supported gates include
`read`, `edit`, `glob`, `grep`, `list`, `bash`, `task`, `external_directory`,
`todowrite`, `webfetch`, `websearch`, `lsp`, `skill`, `question`, and
`doom_loop`.

For `bash` and `task`, use ordered pattern objects. The **last matching
rule wins**, so put the wildcard first.

For `edit`, do **not** use `"*": deny` plus later path allows. A catch-all
`edit` deny wins and blocks Write/StrReplace even when `knowledge/**` is
listed as allow. Allow `knowledge/**` (and report paths) and deny named
application trees instead.

```json
"bash": {
  "*": "deny",
  "git status *": "allow",
  "npm test *": "allow"
}
```

Use `doom_loop` deliberately. It controls recovery prompts when OpenCode
detects that an agent appears stuck. Do not disable it merely to hide symptoms.
Instead, combine it with a prompt-level completion protocol:

```json
"permission": {
  "doom_loop": "allow",
  "task": {
    "*": "deny",
    "backend-engineer": "allow",
    "code-reviewer": "allow"
  }
}
```

When `task` is `deny`, the subagent is removed from the Task tool description.
This is useful for specialists that must not delegate. Direct user `@` mentions
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
- the OpenCode doom-loop recovery prompt firing.

### Required behaviour on detection

1. Stop the current approach immediately; do not retry a third time.
2. Write the escalation report to a file rather than only printing it, so the
   user can hand it back to `agent-team-designer`.
3. Default path: `.opencode/reports/doom-loop-<agent-name>-<YYYYMMDD-HHMM>.md`
   inside the repository the agent is working in. If that directory cannot be
   created, report the content inline and say where it could not be written.
4. Finish the turn with status `BLOCKED` and name the report path.

The agent must therefore have `edit` access to its report directory, or the
configuration must document that reports will be returned inline only.

### Report template

```markdown
# Doom Loop Escalation Report

- Agent: <agent-name>
- Repository: <absolute path>
- Timestamp: <ISO 8601>
- Detected by: <self-detected | doom_loop recovery prompt | user>

## Objective
<the task the agent was asked to complete>

## Where it stalled
<the precise step, file, command, or decision point>

## Loop evidence
<the repeated actions, with the identical error or identical result each time>

## Suspected root cause
Select all that apply and justify each:
- [ ] Missing skill or capability: <which capability, and what it would need to do>
- [ ] Missing or denied permission: <exact permission gate and pattern needed>
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
<anything that must not be granted, e.g. do not widen bash to "*": "allow">

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

Never resolve a doom loop by granting blanket `bash: "*": "allow"`, removing
`doom_loop`, or raising `steps` without evidence that step exhaustion was the
actual cause.

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
- Is the model ID valid for the configured provider?
- Is the prompt path correct and available?
- Is `steps` finite and proportionate to the task?
- Are edit, Bash, external-directory, skill, and task permissions least-privilege?
- Do Bash and task patterns have the wildcard first and specific exceptions after?
- Are delegation targets real and non-overlapping?
- Is `doom_loop` available for recovery without masking a broken workflow?
- Does the prompt define doom-loop detection triggers and require a written
  escalation report at a stated path?
- Can the agent actually write that report, or is inline-only fallback documented?
- Does the prompt define completion, blocker handling, and evidence requirements?
- Are deprecated `tools` or `maxSteps` fields being avoided or migrated?
- Were repository `.agents`, `.copilot`, `.opencode`, and `.github`
  instructions and skills discovered and configured?
- Were global `~/.agents`, `~/.copilot`, `~/.config/opencode`, and `~/.github`
  sources discovered without reading credentials or session data?
- Are local/global precedence and any conflicts documented?
- Are all configured instruction and skill paths valid and appropriately scoped?
- Does the configuration match the approved organisation and complete agent definitions?
- Did the design audit release the team for configuration with no unresolved critical findings?
- Do representative routing, delegation, denial, completion, and doom-loop cases behave as designed?

## Required output

When designing or changing an agent, provide:

1. the complete JSON fragment under `agent`;
2. any prompt file contents or path changes;
3. the complete `instructions` and `skills.paths` changes, with source
   precedence and included/omitted/missing paths;
4. permission and step-limit rationale;
5. migration notes for deprecated or conflicting settings;
6. the doom-loop escalation rule applied, including the report path and any
   permission needed to write it;
7. a verification prompt and expected completion behaviour.
8. runtime validation evidence for syntax/schema, path resolution, delegation,
   denied operations, completion, and recovery, or an explicit list of checks
   that could not be performed.

Never silently edit configuration. Never claim an agent is fixed without testing
the relevant permission, delegation, and completion paths.
