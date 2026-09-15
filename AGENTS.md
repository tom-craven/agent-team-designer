# AGENTS.md

This project is dedicated to the **Agent Team Designer** agent.

## Purpose

The sole agent is `agent-team-designer`.
It designs, audits, and structures high-quality AI agents and multi-agent teams.

## Skills (upgraded via skill-creator)

| Skill | Purpose |
|-------|---------|
| `skill-creator` | Create/improve skills to fill capability gaps |
| `agent-audit` | Audit agents for quality, overlap, permissions |
| `prompt-patterns` | Proven system-prompt structures |
| `model-selection` | Best model via OpenRouter rankings |
| `agent-org-design` | Multi-agent team structures |
| `find-skills-sh` | Discover skills from skills.sh |
| `skill-security-audit` | Security-scan skills before adoption |
| `opencode-agent-config` | Configure shared OpenCode settings and validate Markdown agents |
| `agent-team-creation` | Coordinate project analysis through organisation design, agent and skill creation, audits, OpenCode configuration, and validation |

## Working rules

- All agent design work goes through `@agent-team-designer`
- Prefer existing skills from skills.sh when possible
- Security-audit third-party skills before recommending install
- Least-privilege permissions
- Treat `gradle.properties` as secret-bearing in every generated team: deny
  `gradle.properties` and `**/gradle.properties` through `read`, block direct
  shell reads, deny content-search tools that cannot enforce path exclusions,
  block indirect Git diff/history disclosure, and never grant
  unrestricted Gradle execution. Allow only named build and verification tasks,
  with publish, release, push, and property-reporting operations denied. Deny
  edits to the same paths as defense in depth.
- One clear job per agent
- Use `skill-creator` when a capability gap appears
- Use `agent-team-creation` for end-to-end creation or restructuring of a runnable team
- When the user requests `software-knowledge` on a new team, grant the
  orchestrator / primary and every agent assigned that skill edit access to
  `knowledge/**` (including deletion of proven stale, duplicate, or disposable
  superseded artefacts), plus the skill compile / lint scripts, even if that
  agent otherwise has `edit: deny`. Do not put
  `"*": deny` on `edit` in the same object — it wins over `knowledge/**`
  allow and blocks Write/StrReplace. Deny named application paths instead.
  Do not install the skill without a working `knowledge/` write permission.
  Require reference checks before deletion, preserve historical decisions via
  deprecation and `superseded_by` unless they are proven duplicates, compile and
  lint after deletion, and report every deleted path and rationale. Do not grant
  shell deletion commands merely to provide this capability.
- Follow the gated lifecycle: analyse target project → design organisation →
  design each agent → resolve and audit skills → audit the complete team →
  create OpenCode configuration → validate runtime behaviour
- Do not advance past unresolved critical findings at any lifecycle gate
- Define every created agent exactly once under `.opencode/agents/<agent-name>.md`.
  The Markdown frontmatter and body are the complete runtime definition. Never
  mirror or split agent configuration under `opencode.json` or `opencode.jsonc`.
- Create or update `opencode.json` or `opencode.jsonc` only for shared OpenCode
  settings such as instructions, skill paths, providers, MCP servers, and
  repository-wide defaults.
- Before changing or creating OpenCode configuration, use the `opencode-agent-config` skill and verify the configuration against the generated agent definitions.
- Fail validation if any agent name exists both under `.opencode/agents/` and a
  JSON/JSONC top-level `agent` object. Migrate all unique fields to Markdown and
  remove the JSON entry; do not rely on precedence or merge behaviour.

## Cross-runtime adapter maintenance

These rules apply whether the repository is being maintained with OpenCode or
GitHub Copilot:

- Treat `.opencode/skills/**/SKILL.md` as the canonical skill source. Files
  under `.github/skills/` are generated Copilot discovery adapters; never edit
  them directly or use them to overwrite the canonical OpenCode skill.
- Before changing the canonical agent or a canonical skill with a Copilot
  adapter, run `python3 scripts/sync_copilot_adapters.py --check` to detect
  existing drift.
- When a Copilot agent changes skill behavior, it must make the change in the
  canonical `.opencode/skills/**/SKILL.md` file, then run
  `python3 scripts/sync_copilot_adapters.py` to update the Copilot adapter.
- When an OpenCode agent changes a canonical skill with a Copilot adapter, it
  must run `python3 scripts/sync_copilot_adapters.py` to update the Copilot
  adapter.
- After changing `.opencode/agents/agent-team-designer.md` in either runtime,
  review and adapt `.github/agents/agent-team-designer.agent.md`, then run
  `python3 scripts/sync_copilot_adapters.py --accept-agent-source`.
- Before completion, run `python3 scripts/sync_copilot_adapters.py --check` and
  include any generated Copilot adapter changes in the same change.
- If the active profile cannot edit files or execute the script, report the
  required maintenance as `BLOCKED`; do not claim the runtimes are synchronized.

## OpenCode team creation context

When creating or installing a team into a software repository, configure the
team to consume the repository's existing guidance rather than replacing it.
The generated OpenCode configuration must retain access to applicable
instructions and skills at both repository-local and global scopes. Before
writing the team's OpenCode configuration, discover and classify all available
instruction and skill sources:

1. **Target repository**
   Inspect repository roots `.agents/`, `.copilot/`, `.opencode/`, and
   `.github/`, including their instructions, prompts, skills, agents, and
   configuration files.
   - `AGENTS.md` files in the repository and applicable parent directories.
   - `.github/instructions/` and `.github/copilot-instructions.md`.
   - `.github/skills/*/SKILL.md` and any other repository-local skill manifests.
   - Existing `opencode.json`, `opencode.jsonc`, `.opencode/agents/`,
     `.opencode/skills/`, and prompt files.
2. **Global OpenCode**
   Also inspect global roots `~/.agents/`, `~/.copilot/`,
   `~/.config/opencode/`, and `~/.github/` when they exist.
   - `~/.config/opencode/opencode.json` or `opencode.jsonc`.
   - `~/.config/opencode/agents/` and `~/.config/opencode/skills/`.
   - Any global `instructions` and `skills.paths` configured there.
3. **Global GitHub/Copilot**
   - `~/.copilot/copilot-instructions.md` when present.
   - `~/.copilot/instructions/` and `~/.copilot/prompts/` when present.
   - `~/.agents/skills/` and installed Copilot skill/plugin locations when
     explicitly exposed by configuration; do not read credentials or session
     databases.

The generated `opencode.json` or `opencode.jsonc` must preserve compatible
existing configuration and include applicable repository and global sources in
its `instructions` and `skills.paths` settings, retaining access to both local
and global scopes. Use absolute paths for global
sources when they are known. Use repository-relative paths only when OpenCode
resolves them from the target repository. Do not blindly include every path:
exclude secrets, credentials, session data, private keys, and unrelated
application directories. Report every source included, omitted, or found
missing.

Repository-local guidance has precedence for repository work; global guidance
provides defaults. If sources conflict, preserve the narrower repository rule
and surface the conflict to the user. Skills remain subject to security audit
before recommendation or installation. Do not copy or modify third-party or
global skills merely to make them available; reference existing trusted paths
unless the user explicitly requests vendoring.
