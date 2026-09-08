---
name: model-selection
description: Select the best model for an agent profile from the models available via the GitHub Copilot integration, using current benchmark evidence (coding, reasoning, speed, premium-request cost). Use whenever setting or changing an agent's model field, designing a new agent, or optimizing cost/performance.
---

# Model Selection (GitHub Copilot integration)

All agents in this workspace run through the **GitHub Copilot** provider.
Model IDs are therefore always of the form:

```
github-copilot/<model-id>
```

A model that is not enabled in the Copilot integration is **not selectable**, no
matter how well it benchmarks elsewhere.

## Never do
- Recommend a model that is not confirmed available in the Copilot catalogue
- Write a bare model ID without the `github-copilot/` prefix
- Pick a model without naming the ranking axis it wins on
- Assume the catalogue is static — Copilot adds and retires models frequently
- Ignore premium-request multipliers when a near-equal cheaper model exists

## Step 1 — Discover what is actually available (mandatory)

Never recommend from memory. Confirm the live catalogue first, in this order:

1. Check the workspace config for an explicit model list:
   - `opencode.json` / `opencode.jsonc` (`provider.github-copilot.models`)
   - existing agent files in `.opencode/agents/` (what is already in use)
2. Check the Copilot docs for the current supported model list:
   - https://docs.github.com/copilot/reference/ai-models/supported-models
3. Check premium request multipliers:
   - https://docs.github.com/copilot/concepts/billing/copilot-requests

Never read `auth.json` or any credential file to enumerate models.

If you cannot verify availability, say so and offer the closest confirmed option.

## Step 1b — Check the retirement table (mandatory)

Availability in the main supported-models table is **not** sufficient. On the same
page, check the **Model retirement history** table before recommending anything.

- A model can appear GA in the main table while already carrying a retirement date.
- Retirement rows may carry footnotes that preserve access for a narrow group only
  (for example, Claude Sonnet 4.6 retired 2026-09-01 but remains available to
  individual subscribers on annual plans).
- Also check for models restricted by default: pre-GA models, open-weight models,
  and models outside GitHub's data-retention agreement are disabled by default.

Report the retirement date and the vendor's suggested alternative whenever one
exists. Never recommend a model whose retirement date has passed unless the user
has confirmed in this conversation that a documented exemption applies to them.

When auditing existing agents, check their configured models against this table
too. A model that was valid when the agent was written may have been retired since.

## Step 2 — Pick the ranking axis

| Agent role | Primary axis | Copilot-family preference |
|------------|--------------|---------------------------|
| Senior engineer / coding | Coding benchmark (SWE-bench class) | Frontier Claude / GPT reasoning tier |
| Orchestrator / planner | Reasoning + instruction following | Frontier reasoning tier |
| Reviewer / security | Coding + careful reasoning | Frontier tier, low temperature |
| PM / writer / docs | General intelligence + long context | Mid tier is usually sufficient |
| Explorer / search / triage | Speed + low premium cost | Fast / included-tier model |
| High-volume, low-risk tasks | Cost per premium request | Lowest multiplier that passes |

Rule of thumb: use the **cheapest tier that reliably passes the job**, and
reserve frontier models for work where a wrong answer is expensive
(production code, security review, architecture).

## Step 3 — Cross-check quality evidence

Copilot does not publish its own benchmark ranking, so use external evidence for
relative model quality, then intersect it with the Copilot catalogue:

- https://openrouter.ai/rankings#benchmarks (coding index, intelligence, value)
- Vendor model cards for context window and tool-calling support

Only models present in **both** sets are valid recommendations.

## Step 4 — Required output format

```
Recommended: github-copilot/<model-id>
Availability: confirmed via <config file | Copilot supported-models docs>
Reason: <axis it wins + why it fits this role>
Cost: <premium request multiplier, or "included">
Cheaper alternative: github-copilot/<model-id>
Premium alternative: github-copilot/<model-id>
Checked: <YYYY-MM-DD>
Note: Copilot's catalogue changes; re-verify before locking this in.
```

## Notes
- Copilot enablement is org-controlled — a model may be listed by GitHub but
  disabled for the user's org. If a recommendation fails at runtime, fall back
  to the cheaper alternative and tell the user why.
- Prefer models with confirmed tool-calling support for any agent that uses
  `edit`, `bash`, or `task`.
- Keep temperature guidance separate from model choice: reviewers and security
  agents get low temperature (0.1–0.2) regardless of model.
- There is deliberately no cached catalogue snapshot in this skill. GitHub
  changes model availability frequently, and a stale list invites recommending
  a model that no longer exists. Always perform the live lookup in Step 1.

## Durable caveats (not a catalogue)

These hold across catalogue changes and must still be re-checked, not assumed:

- The Copilot docs table lists model **display names**, not slugs. Confirm the
  exact slug against `opencode.json` or a working agent file before relying on it.
- `claude-fable-5` has different data-retention terms — Anthropic retains prompts
  and outputs to operate safety classifiers — and requires explicit org
  enablement. Flag this before recommending it for sensitive code.
- Models marked *public preview* rather than GA should be avoided for production
  agents.
- Premium request multipliers are plan-dependent and published separately:
  https://docs.github.com/copilot/reference/copilot-billing/request-based-billing-legacy/model-multipliers-for-annual-plans
