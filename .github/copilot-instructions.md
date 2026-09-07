# Agent Team Designer

This repository defines and validates the `agent-team-designer`, which designs
and audits AI agents, prompts, permissions, model choices, skills, and team
structures. Follow `AGENTS.md` as the canonical repository behavior.
Follow `docs/agent-team-designer-behavior.md` as the canonical runtime-neutral
agent behavior. Copilot profiles may narrow, but must not weaken, those rules.

## Runtime Boundaries

- `.github/` contains GitHub Copilot configuration.
- `opencode.json` and `.opencode/` contain OpenCode configuration. Do not assume
  that Copilot tools, approvals, models, or delegation map to OpenCode settings.
- Use least privilege. Do not silently edit agent, skill, or runtime
  configuration.
- Before any installation, obtain the destination, display every exact path
  that would change, and wait for confirmation.
- Do not create global installations or symbolic links.
- Do not inspect credentials, tokens, authentication/session stores, or
  unrelated home-directory content.
- Do not claim validation without naming the command, file, or observed runtime
  behavior that provides the evidence.

End each task with exactly one status: `COMPLETE`, `PARTIAL`, `BLOCKED`, or
`UNSAFE TO CONTINUE`.
