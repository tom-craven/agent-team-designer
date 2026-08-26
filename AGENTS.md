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
| `opencode-agent-config` | Define and audit OpenCode agent configuration in `opencode.json` |
| `agent-team-creation` | Coordinate project analysis through organisation design, agent and skill creation, audits, OpenCode configuration, and validation |

## Working rules

- All agent design work goes through `@agent-team-designer`
- Prefer existing skills from skills.sh when possible
- Security-audit third-party skills before recommending install
- Least-privilege permissions
- One clear job per agent
- Use `skill-creator` when a capability gap appears
- Use `agent-team-creation` for end-to-end creation or restructuring of a runnable team
- Follow the gated lifecycle: analyse target project → design organisation →
  design each agent → resolve and audit skills → audit the complete team →
  create OpenCode configuration → validate runtime behaviour
- Do not advance past unresolved critical findings at any lifecycle gate
- When creating a multi-agent team, also create or update the team's OpenCode configuration (`opencode.json` or `opencode.jsonc`) so the agents, modes, models, prompts, permissions, and delegation settings are runnable—not just documented in Markdown.
- Before changing or creating OpenCode configuration, use the `opencode-agent-config` skill and verify the configuration against the generated agent definitions.

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
