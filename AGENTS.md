# Agent Team Designer Repository

This repository defines the `agent-team-designer` for GitHub Copilot CLI and
OpenCode. It designs and audits AI agents, prompts, permissions, models, skills,
and multi-agent team structures.

## Sources Of Truth

- [`docs/agent-team-designer-behavior.md`](docs/agent-team-designer-behavior.md)
  defines canonical runtime-neutral role behavior, safety boundaries, skill
  routing, recovery rules, and completion statuses.
- `.github/` contains GitHub Copilot-specific instructions, agent schema, tools,
  and generated skill-discovery adapters.
- `opencode.json` and `.opencode/` contain OpenCode-specific schema, permissions,
  models, agents, and canonical skill implementations.

Runtime-specific profiles may add narrower constraints but must not weaken the
canonical behavior. Do not assume that Copilot tools, approvals, models,
budgets, or delegation map one-for-one to OpenCode configuration.

## Maintenance

The five Copilot skill adapters under `.github/skills/` are generated from
canonical skills under `.opencode/skills/`. Do not edit those adapters directly.

After changing a canonical skill, regenerate and validate runtime files:

```bash
python3 scripts/sync_runtime_docs.py
```

For a non-writing validation, run:

```bash
python3 scripts/sync_runtime_docs.py --check
```

The `Runtime sync` workflow enforces this check when shared behavior, either
runtime's agents or skills, instructions, configuration, or the checker changes.

Do not add global configuration, credentials, session data, symbolic links, or
unrelated home-directory content to this repository.
