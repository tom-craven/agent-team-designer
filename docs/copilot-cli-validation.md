# Copilot CLI Validation

Validation date: 2026-09-07

This report records the local evidence used to add GitHub Copilot CLI
compatibility. Organization policies and the Copilot catalogue can change, so
repeat the runtime checks before relying on this snapshot.

## Environment

- Copilot CLI: `1.0.80`, reported by `copilot version`.
- OpenCode: `1.18.26`, reported by `opencode --version`.
- No global configuration, authentication data, session stores, or unrelated
  home-directory content was inspected or copied.

## Discovery

Before the Copilot files were added:

- `copilot plugins list --kind skill --kind instruction` reported that the
  `plugins` command was unavailable in this installed build.
- `copilot skill` documented repository discovery from `.github/skills/`,
  `.agents/skills/`, and `.claude/skills/`; it did not list `.opencode/skills/`.
- `copilot skill list --json` did not contain this repository's OpenCode skills.

The migration therefore uses `.github/skills/<name>/SKILL.md` adapters for only
the five required skills. Each adapter points to its canonical first-party
source under `.opencode/skills/`; the adapters are not independent copies.

Post-change discovery results are recorded in the final validation section.

## Model Recommendation

- Recommended Copilot CLI model: `gpt-5.6-terra`.
- OpenCode equivalent: `github-copilot/gpt-5.6-terra`.
- Availability evidence: CLI `1.0.80` lists `gpt-5.6-terra` in
  `copilot help config`; GitHub's supported-model table lists GPT-5.6 Terra as
  GA and available to Copilot CLI. A local invocation result is recorded below.
- Task-fit axis: GitHub describes Terra as the balanced general-purpose choice
  for everyday interactive and agentic coding. That better fits mixed agent
  design and audit work than the speed-optimised Luna tier.
- Cost: current usage-based list price is $2.00 per million input tokens, $0.20
  cached input, $2.50 cache writes, and $12.00 output at the default tier. At
  one AI credit per $0.01, those rates are 200, 20, 250, and 1,200 AI credits.
- Cheaper alternative: `gpt-5.6-luna`, at $0.20 input, $0.02 cached input,
  $0.25 cache writes, and $1.20 output per million default-tier tokens; use it
  for small, repetitive, or cost-sensitive audits. Those rates are 20, 2, 25,
  and 120 AI credits.
- Premium alternative: `gpt-5.6-sol`, at $4.00 input, $0.40 cached input,
  $5.00 cache writes, and $20.00 output per million default-tier tokens; use it
  for complex, long-running design work over large repositories. Those rates
  are 400, 40, 500, and 2,000 AI credits.
- Pricing model: GitHub moved to usage-based AI credits on 2026-06-01, where
  one AI credit equals $0.01. Legacy annual-plan request multipliers do not list
  the GPT-5.6 family and are not used for this recommendation.
- Organization caveat: documentation and local CLI recognition do not guarantee
  availability to every user. An organization or enterprise policy can disable
  Copilot CLI or individual models.

Sources checked on 2026-09-07:

- <https://docs.github.com/en/copilot/reference/ai-models/supported-models>
- <https://docs.github.com/en/copilot/reference/ai-models/model-comparison>
- <https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing>

## Final Validation

- `copilot plugins list --kind skill --kind instruction --json`: command still
  reported unavailable in CLI `1.0.80`; this version exposes help for the
  command but does not execute it for this account/build.
- `copilot skill list --json`: discovered `agent-audit`, `agent-org-design`,
  `model-selection`, `prompt-patterns`, and `skill-security-audit` with source
  `project` and paths under `.github/skills/`.
- `copilot --agent=agent-team-designer --model=gpt-5.6-terra ...`: selected the
  repository custom agent and invoked `gpt-5.6-terra` successfully. This
  verifies the bare CLI identifier and current account enablement.
- `copilot --agent=agent-team-designer ...` without a model override also ran
  successfully, verifying that the custom profile accepts its model field.
- A read-only audit named `.opencode/skills/agent-audit/SKILL.md` as the
  canonical workflow and identified `AGENTS.md` plus
  `.github/copilot-instructions.md` as governing instructions. The audit made no
  worktree changes.
- A two-agent design selected `agent-org-design`, produced explicit delegation
  and a hand-off contract, and made no worktree changes.
- An installation request without a supplied or confirmed destination stopped
  with `BLOCKED` and requested destination confirmation.
- A simulated required lookup failing identically twice stopped with `BLOCKED`
  rather than retrying indefinitely.
- The profile exposes only `read`, `search`, and `web`; it has no `edit`,
  `execute`, or `agent` tool and explicitly forbids delegation around that
  boundary.
- YAML parsing confirmed only `name`, `description`, `model`, and `tools` are in
  the profile frontmatter. The full file is below the 30,000-character limit.
- `opencode debug config` loaded `AGENTS.md`, `.opencode/skills`, and the
  unchanged `agent-team-designer` definition with its original permissions.
- `git diff --check` completed without errors.

The `plugins list` discrepancy is retained as explicit evidence rather than
treated as a successful check. `copilot skill list` and live agent invocations
provide the supported discovery and behavioral evidence for this installed CLI.
