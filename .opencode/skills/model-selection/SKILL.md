---
name: model-selection
description: Select the best model for an agent profile from the models available via the GitHub Copilot integration, using current benchmark evidence (coding, reasoning, speed, per-token cost). Use whenever setting or changing an agent's model field, designing a new agent, or optimizing cost/performance.
---

# Model Selection (GitHub Copilot integration)

All agents in this workspace run through the **GitHub Copilot** provider.
Model IDs are therefore always of the form:

```
github-copilot/<model-id>
```

A model that is not enabled in the Copilot integration is **not selectable**, no
matter how well it benchmarks elsewhere.

**One sanctioned exception: local Ollama models** (`ollama/<tag>`), governed by
the "Local Ollama models" section below. The user has enabled the Ollama provider
in their global OpenCode configuration and approved it for the roles listed
there. No other non-Copilot provider is approved.

## Never do
- Recommend a model that is not confirmed available in the Copilot catalogue
  (except an approved `ollama/<tag>` under the Local Ollama rules)
- Write a bare model ID without a provider prefix (`github-copilot/` or `ollama/`)
- Pick a model without naming the ranking axis it wins on
- Assume the catalogue is static — Copilot adds and retires models frequently
- Ignore per-token price when a near-equal cheaper model exists
- Quote premium-request multipliers as the cost basis. Copilot moved to
  usage-based billing on 2026-06-01; multipliers apply only to legacy annual
  Pro / Pro+ plans (see Durable caveats)

## Step 1 — Discover what is actually available (mandatory)

Never recommend from memory. Confirm the live catalogue first, in this order:

1. Check the workspace config for an explicit model list:
   - `opencode.json` / `opencode.jsonc` (`provider.github-copilot.models`)
   - existing agent files in `.opencode/agents/` (what is already in use)
2. Check the Copilot docs for the current supported model list:
   - https://docs.github.com/copilot/reference/ai-models/supported-models
3. Check per-token pricing (1 AI credit = $0.01 USD; prices are per 1M tokens):
   - https://docs.github.com/copilot/reference/copilot-billing/models-and-pricing
   - Record input, cached input, and output price, the model category
     (Lightweight / Versatile / Powerful), and any long-context tier with its
     token threshold. Note promotional prices and their expiry dates.
   - Only for users on a legacy annual Pro / Pro+ plan, also check the
     request-based multipliers (see Durable caveats).

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

## Step 1c — Local Ollama models (approved exception)

Model IDs take the form `ollama/<tag>` where `<tag>` is exactly the name shown by
`ollama list` (for example `ollama/qwen3.8:latest`). Pinned tags are preferred
over `:latest`; if `:latest` is used, record the model ID hash so a silent
re-pull is detectable.

**Approved roles:** `junior-engineer` (default, user-approved with
`ollama/qwen3.8`). Other low-risk roles (explorer, summariser, docs writer) may
use an Ollama model only after the user confirms it in this conversation.
**Never** use an Ollama model for the orchestrator, senior engineer, reviewer, or
any security role unless the user explicitly overrides this after being shown the
tool-calling and context risks.

**Availability evidence (replaces catalogue checks for these IDs):**
1. The user's global OpenCode config enables the `ollama` provider. Confirm from
   the user, or from `~/.config/opencode/opencode.json(c)` `provider.ollama`
   without reading any credential-bearing field.
2. The tag appears in `ollama list` output supplied by the user. If the shell is
   denied, ask the user to run it. Never guess a tag.
3. `ollama show <tag>` reports `tools` under capabilities. No tool support means
   the model is invalid for any agent using `edit`, `bash`, or `task`.
4. The provider config declares the model with a context limit and
   `num_ctx` raised above Ollama's small default, sized to fit available VRAM.
   Without it prompts truncate silently.

**Cost:** there is no per-token price. Report it as hardware and time cost
(GPU/VRAM or RAM, tokens per second) and judge the saving by the measured
escalation rate, not by assumption.

**Quality evidence:** external rankings may not cover a local tag. Do not invent
benchmark numbers. State that quality is unverified and apply the pilot gate:
track first-pass success, escalation rate, and tool-call errors; if escalation
exceeds about 25–30% or tool-call errors recur, fall back to the Copilot
alternative.

**Always name a Copilot fallback** (cheapest Lightweight/Versatile model that
passes) for the same role, and keep the senior engineer on a Copilot model.

**Privacy:** local inference keeps prompts on the machine, but the secret
baseline applies unchanged.

## Step 2 — Pick the ranking axis

| Agent role | Primary axis | Copilot-family preference |
|------------|--------------|---------------------------|
| Senior engineer / coding | Coding benchmark (SWE-bench class) | Frontier Claude / GPT reasoning tier |
| Orchestrator / planner | Reasoning + instruction following | Frontier reasoning tier |
| Reviewer / security | Coding + careful reasoning | Frontier tier, low temperature |
| PM / writer / docs | General intelligence + long context | Mid tier is usually sufficient |
| Explorer / search / triage | Speed + low per-token price | Lightweight-category model |
| High-volume, low-risk tasks | Input + output price per 1M tokens | Cheapest model that passes |
| Junior engineer (simple, briefed tasks) | Per-token price + instruction following + tool-call reliability | Cheapest Lightweight/Versatile model that passes a representative brief; low or no reasoning effort. **Local option:** `ollama/qwen3.8` when Step 1c checks pass, with a Copilot fallback |

For the junior tier, pick on cost first. Reject a cheaper model if its tool-call
reliability is weak, because retries and escalations cancel the savings. Set the
reasoning/thinking variant to the lowest available level.

Cost reasoning under usage-based billing:
- Compare models on **blended price**, not input alone. Agent loops are
  input-heavy but cached input is far cheaper, so weigh input, cached input and
  output together for the expected workload.
- Higher reasoning levels and the long-context tier consume more tokens and
  credits. Default to regular context and reasoning; raise them only for tasks
  that need it.
- Stay under a model's long-context threshold where possible, since prices
  roughly double above it.
- When two models are within a few points on the quality benchmark, prefer the
  one with the lower price; state the point gap and the price ratio.

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
Cost: <$ input / cached input / output per 1M tokens, category, long-context
       threshold if any, promo expiry if any>
Cheaper alternative: github-copilot/<model-id>
Premium alternative: github-copilot/<model-id>
Checked: <YYYY-MM-DD>
Note: Copilot's catalogue changes; re-verify before locking this in.
```

For an Ollama recommendation use this variant instead:

```
Recommended: ollama/<tag>
Availability: ollama provider in global config + `ollama list` + tools capability
Reason: <cost saving for this role>
Cost: hardware/time only (GPU/VRAM, tokens/sec); no per-token price
Quality: unverified; pilot gate = escalation rate <~25-30%, no recurring tool errors
Copilot fallback: github-copilot/<model-id>
Context: num_ctx = <value>
Checked: <YYYY-MM-DD>
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
- Billing is usage-based (per token, converted to AI credits) for current plans.
  Premium-request multipliers are a legacy concept that applies only to Copilot
  Pro / Pro+ users who stayed on an annual request-based plan, and that table
  omits newer models. Use it only when the user confirms such a plan:
  https://docs.github.com/copilot/reference/copilot-billing/request-based-billing-legacy/model-multipliers-for-annual-plans
- Allowances differ by plan (individual vs pooled Business / Enterprise); state
  which plan assumption a cost comparison uses.
- Promotional prices expire (for example a stated end date on a model's row).
  Report the expiry and the post-promo price if known, because a cost-based
  choice can flip.
