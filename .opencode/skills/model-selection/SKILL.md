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

No other provider is approved. Do not recommend local or third-party provider
models; the cheapest suitable Copilot model is the cost-saving option.

## Never do
- Set `temperature` in an agent file. Reasoning models in the catalogue often
  report `capabilities.temperature: false` (as of 2026-11-18: Claude Sonnet,
  Opus and Haiku 5.5 and GPT-6.1 Sol), and the API rejects the call with
  `Unsupported parameter: 'temperature' is not supported with this model`,
  which makes every subagent start fail. GPT-6.1 Terra is listed as supporting
  it but failed at runtime, so the catalogue flag is not proof. Omit the field
  unless the user explicitly requests it and a working run proves it is
  accepted; control behaviour with `reasoningEffort` or the model variant
- Recommend a model that is not confirmed available in the Copilot catalogue
- Write a bare model ID without the `github-copilot/` provider prefix
- Pick a model without naming the ranking axis it wins on
- Assume the catalogue is static — Copilot adds and retires models frequently
- Recommend any model without first retrieving its pricing (see Pricing gate);
  if pricing cannot be retrieved, alert the user instead of proceeding silently
- Skip the benchmark attempt. Every recommendation requires a real attempt to
  retrieve benchmark data (see Benchmark gate); never finish after the
  catalogue and pricing steps alone
- Label evidence `EVIDENCE PARTIAL` unless a retrieval was actually attempted
  and the attempt is described; "partial" means attempted-but-incomplete,
  never "not tried"
- Justify a model only by tier, name, or price when benchmark data was
  retrievable
- Ignore per-token price when a near-equal cheaper model exists
- Treat Copilot Fusion as a model with a benchmark score, invent a Fusion slug,
  or assume it is available in OpenCode because it is in Copilot CLI (Step 1c)
- Recommend Fusion for an agent with `edit` or `shell` (V1: `bash`) allowed, or for the
  orchestrator, senior engineer, reviewer or security roles, without an explicit
  user-accepted override
- Quote the Fusion paid-plan discount without its expiry date
- Quote premium-request multipliers as the cost basis. Copilot moved to
  usage-based billing on 2026-06-01; multipliers apply only to legacy annual
  Pro / Pro+ plans (see Durable caveats)

## Pricing gate (critical, non-skippable)

Pricing is a mandatory input to every recommendation. Before writing any
`model:` value you MUST retrieve and record, for the exact model, from
https://docs.github.com/copilot/reference/copilot-billing/models-and-pricing :
input, cached input and output price per 1M tokens, the model category, any
long-context threshold, and any promotional price with its expiry.

- Fetch the pricing page explicitly. Do not infer price from the model name,
  tier, memory, or the supported-models page.
- If the page is large or truncated, search or read the saved output (Read/Grep
  tools) until the specific model's row is found. Truncation is not a reason to
  skip the check.
- Retry at most twice with a changed approach (alternate URL path, saved-output
  search). Never repeat the same failing call a third time.
- **If pricing cannot be retrieved or the model's row is not found, ALERT THE
  USER** with a prominent line at the top of the response:
  `PRICING NOT VERIFIED for <model-id>: <reason>`. State what was tried, then
  give the recommendation only as provisional, name a cheaper confirmed
  alternative if any, and ask the user to confirm or supply pricing before the
  model is written to any file.
- Never write a `model:` field to disk, and never report model selection as
  `COMPLETE`, while pricing is unverified (the same applies to unverified
  benchmarks; see Benchmark gate). Use `PARTIAL` or `BLOCKED`.
- Never write "Cost: n/a", leave cost blank, or fall back to premium-request
  multipliers to hide a failed lookup.

## Benchmark gate (critical, non-skippable)

Benchmark evidence is a mandatory input to every recommendation, alongside
availability and pricing. Before writing or recommending any `model:` value you
MUST attempt to retrieve benchmark data for the shortlisted models and record
the outcome. The attempt itself is not optional, even when the choice looks
obvious, the repository is small, or the catalogue/pricing steps hit problems.

Required attempt, in order (see "Evidence stack" in Step 3):
1. `webfetch` the Artificial Analysis LLM Leaderboard
   https://artificialanalysis.ai/leaderboards/models . It renders a full table
   (Intelligence Index, cost per task, time per task, time to first answer
   token, context window) for each model at each reasoning level. If the saved
   output is truncated, read it with Read/Grep until each shortlisted model's
   rows are found; retry the fetch at most once.
2. Optional cross-check: `webfetch` the llm-stats coding leaderboard
   https://llm-stats.com/leaderboards/best-ai-for-coding . Its composite is
   arena-weighted (see Step 3), so treat it as supporting only.
3. If the scores are still not retrievable, ask the user to paste the relevant
   rows (index, cost per task, reasoning level) with the date.

Rules:
- A problem in an earlier step (truncated docs, denied shell, pricing
  difficulty) never cancels this gate. Finish or report each gate separately.
- Record per model: index name, score, source URL, retrieval date, and the
  score gap and price ratio between the top candidates.
- If retrieval fails after the steps above, put a prominent line at the top of
  the response: `BENCHMARKS NOT VERIFIED for <model-id>: <what was tried and
  the result>`. Mark the recommendation provisional, state "category claim
  only, quality unverified", and ask the user to confirm or supply data.
- Never write a `model:` field to disk, and never report model selection as
  `COMPLETE`, while benchmarks are unverified. Use `PARTIAL` or `BLOCKED`.
- Only benchmark scores count. Usage-share rankings (for example OpenRouter Top
  Models, Leaderboard, Market Share, Programming, Domain, Context Length) are
  never quality evidence (see Step 3).
- Sources found unusable on 2026-11-13 and removed from the stack: the
  Artificial Analysis Coding Agent Index pages (no per-model values rendered),
  the llm-stats Tool Calling and Reasoning pages (top three models only),
  OpenRouter Benchmarks (API key required), the Aider polyglot leaderboard
  (no current models), and SWE-bench, Terminal-Bench and LiveBench (rows not
  retrievable by `webfetch`). Use them only if the user pastes their data.
- Re-audits of existing agents also run this gate; do not approve a model on
  the strength of its current configuration.

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
  (illustrative, as of 2026-10-29: Claude Sonnet 4.6 retired 2026-09-01 but
  remained available to individual subscribers on annual plans; re-verify).
- Also check for models restricted by default: pre-GA models, open-weight models,
  and models outside GitHub's data-retention agreement are disabled by default.

Report the retirement date and the vendor's suggested alternative whenever one
exists. Never recommend a model whose retirement date has passed unless the user
has confirmed in this conversation that a documented exemption applies to them.

When auditing existing agents, check their configured models against this table
too. A model that was valid when the agent was written may have been retired since.

## Step 1c — Copilot Fusion check (mandatory only when Fusion is considered)

Copilot Fusion is a runtime router and orchestrator selected in the model picker,
not a model. Per prompt it chooses an execution pattern (Single, Cascade,
Critique), a reasoning effort, and the models that run it. Source:
https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/models/copilot-fusion
(read 2026-10-29; re-read on the check date, because patterns, effort tiers and
the model pool change).

1. **Runtime exposure.** Confirm the target runtime exposes Fusion. The docs list
   GA in VS Code, Copilot CLI, the Copilot app and JetBrains, and do not mention
   OpenCode. For OpenCode confirm the exact slug from `opencode models` output,
   `opencode.json(c)`, or a working agent file; never infer it. If unconfirmed
   report `FUSION NOT VERIFIED in <runtime>: <what was tried>` and use a pinned
   model.
2. **Plan and policy.** Ask the user for their plan and effort tier (Standard is
   on all plans; High and Max are not on Free or Student) and whether org policy
   restricts the model pool. Do not read credentials.
3. **Pricing.** Fusion has no price of its own; each underlying model bills at its
   standard rate, and High and Max can use more than one model. Apply the Pricing
   gate to the underlying models and state "per-model rates; mix varies per
   prompt". Paid plans receive a 30% discount on model costs through 2026-11-30;
   report the expiry and that cost comparisons can flip afterwards.
4. **Quality.** No benchmark exists for Fusion as a unit. Mark `Quality:
   unverified` and apply the pilot gate; never reuse underlying-model scores as
   Fusion's.
5. **Known limits.** Fusion does not start subagents; discarded drafts can leave
   workspace edits in place; its context window is the smallest among the models
   it uses.

**Role eligibility.** Candidate (Standard, High only where justified): explorer,
triage, summariser, docs writer, PM, high-volume low-risk, and the junior
engineer after user confirmation. Not by default: orchestrator, senior engineer,
reviewer, security, or any agent with `edit` or `shell` (V1: `bash`). Always name a pinned
Copilot fallback and never place Fusion on a role without one.

**Pilot gate.** Compare with the best pinned alternative on first-pass success,
cost per completed task, wall time, rework from discarded drafts, and tool-call
errors. Fall back if cost is not lower, success is lower, or unexpected edits
recur; re-run after the discount ends.

Fusion output variant:

```
Recommended: github-copilot/<confirmed-fusion-slug>
Availability: slug confirmed via <opencode models | config>; plan and policy confirmed by user
Effort tier: Standard | High | Max
Cost: per-model rates, no Fusion surcharge; 30% paid-plan discount until 2026-11-30
Quality: unverified; pilot gate
Pinned fallback: github-copilot/<model-id>
Known risks: discarded drafts leave edits; per-prompt model variation
Checked: <YYYY-MM-DD>
```

## Step 2 — Pick the ranking axis

| Agent role | Primary axis | Copilot-family preference |
|------------|--------------|---------------------------|
| Senior engineer / coding | Intelligence Index per cost per task (llm-stats coding cross-check) | Frontier Claude / GPT reasoning tier |
| Orchestrator / planner | Intelligence Index + instruction following | Frontier reasoning tier |
| Reviewer / security | Intelligence Index + careful reasoning | Frontier tier, no `temperature` |
| PM / writer / docs | General intelligence + long context | Mid tier is usually sufficient |
| Explorer / search / triage | Speed + low per-token price | Lightweight-category model |
| High-volume, low-risk tasks | Input + output price per 1M tokens | Cheapest model that passes |
| Junior engineer (simple, briefed tasks) | Per-token price + instruction following + tool-call reliability | Cheapest Copilot Lightweight/Versatile model that passes a representative brief; lowest reasoning level. Name a slightly stronger Copilot fallback |

For the junior tier, pick on cost first, using the GitHub pricing page for price
and the Artificial Analysis cost per task at the low or medium reasoning level
for token efficiency. Reject a cheaper model if its tool-call
reliability is weak, because retries and escalations cancel the savings. Set the
reasoning/thinking variant to the lowest available level. Apply a pilot gate:
track first-pass success, escalation rate, and tool-call errors; if escalation
exceeds about 25–30% or tool-call errors recur, move to the named fallback.

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

## Step 3 — Cross-check quality evidence (mandatory; see Benchmark gate)

Copilot does not publish its own benchmark ranking, so use external evidence for
relative model quality, then intersect it with the Copilot catalogue.

### Evidence stack (use in this order)

1. **Eligibility and cost: Copilot catalogue, retirement table, GitHub
   pricing** (Steps 1, 1b and the Pricing gate). These decide which models are
   valid and what they cost. They are required regardless of any benchmark.
2. **Primary quality and efficiency evidence: Artificial Analysis LLM
   Leaderboard** https://artificialanalysis.ai/leaderboards/models .
   Record, per shortlisted model and per reasoning level (max, xhigh, high,
   medium, low, non-reasoning): Intelligence Index, cost per task, time per
   task and time to first answer token. Rows are separate per reasoning level,
   and the same model can score 55 at max and 31 at medium, so always name the
   level compared and the level the agent will actually run at.
   Cost per task reflects token usage, not just list price: two models with
   identical per-token prices can differ several times over in cost per task.
   Use the Intelligence Index / cost-per-task pair for every role and apply the
   price tie rule in Step 2.
3. **Supporting cross-check: llm-stats Coding leaderboard**
   https://llm-stats.com/leaderboards/best-ai-for-coding . Do not rely on its
   composite score alone: it is weighted heavily towards arena votes on
   front-end, game and SVG generation, which says little about backend work.
   Per-benchmark columns (SWE-bench Verified, Terminal-Bench, SWE-Bench Pro) may
   render without headers; use them only when the column can be identified.
   Ignore the generic capsule prose; use the numbers only.
4. **Supporting only:** vendor model cards for context window and tool-calling
   support.

**Never use as quality evidence:** usage or adoption rankings (OpenRouter Top
Models, Leaderboard, Market Share, Programming, Domain, Context Length). They
rank tokens or requests processed, not quality.

Caveats to state in every recommendation:
- The Intelligence Index is a general-intelligence composite, not a coding-agent
  or language-specific score. It does not measure tool-call reliability, Java or
  Spring Boot quality, or behaviour in an OpenCode loop; say so, and use the
  pilot gate for roles where those matter.
- Third-party prices and cost per task use vendor API prices, not Copilot
  prices. Cost in the output must come from the GitHub pricing page; use cost
  per task only to compare token efficiency.
- Reasoning level availability through Copilot and OpenCode may differ from the
  levels listed; confirm what the agent will run at before relying on a row.
- Name each source's page update date. If a leaderboard page is more than a few
  weeks old relative to the check date, say so.

Rules:
- Only models present in **both** the Copilot catalogue and the external data
  are valid recommendations. External slugs differ from Copilot slugs; match by
  model and confirm the Copilot slug from config.
- Artificial Analysis and llm-stats are partly client-rendered, and `webfetch`
  can return the page frame without values. If values do not render, retry
  once; then ask the user to paste the rows, mark the evidence
  `EVIDENCE PARTIAL`, and keep the recommendation provisional. Never fill
  missing numbers from memory.
- Cite each source (Artificial Analysis or llm-stats) with the URL, retrieval
  date, reasoning level, and the index and score used.
- When scores are within a few points, apply the price tie rule in Step 2.
- Copilot catalogue and retirement (Step 1b) decide which models are eligible;
  the benchmark data decides between them. Run the Benchmark gate even if Step 1
  or 1b is incomplete; report each gate's outcome separately.
- If no benchmark evidence is retrievable after the required attempt, do not
  claim a quality tier; state "category claim only, quality unverified" and
  raise `BENCHMARKS NOT VERIFIED`.

## Step 4 — Required output format

```
Recommended: github-copilot/<model-id>
Availability: confirmed via <config file | Copilot supported-models docs>
Reason: <axis it wins + why it fits this role>
Cost: <$ input / cached input / output per 1M tokens, category, long-context
       threshold if any, promo expiry if any>
Cheaper alternative: github-copilot/<model-id>
Premium alternative: github-copilot/<model-id>
Pricing source: <URL + date retrieved>; or `PRICING NOT VERIFIED: <reason>`
Benchmarks: <Intelligence Index score and cost per task per shortlisted model,
            with reasoning level; gap between top candidates; price ratio>
Benchmark source: <URL + date retrieved>; or `BENCHMARKS NOT VERIFIED: <what
                  was tried and the result>`
Checked: <YYYY-MM-DD>
Note: Copilot's catalogue changes; re-verify before locking this in.
```

The `Cost`, `Pricing source`, `Benchmarks` and `Benchmark source` lines are
mandatory. A recommendation without a retrieved price must carry the
`PRICING NOT VERIFIED` alert. A recommendation without retrieved benchmark data
must carry the `BENCHMARKS NOT VERIFIED` alert. Either alert makes the
recommendation provisional.

## Notes
- Copilot enablement is org-controlled — a model may be listed by GitHub but
  disabled for the user's org. If a recommendation fails at runtime, fall back
  to the cheaper alternative and tell the user why.
- Prefer models with confirmed tool-calling support for agents using `edit`,
  `shell`, or `subagent` (V1: `edit`, `bash`, or `task`). If a role requires
  file deletion, verify that its chosen model exposes a deletion-capable file
  tool under the target runtime; general tool-calling support is not sufficient.
- Reviewers and security agents rely on explicit checklists and a suitable
  `reasoningEffort`, not a `temperature` value (see "Never do").
- There is deliberately no cached catalogue snapshot in this skill. GitHub
  changes model availability frequently, and a stale list invites recommending
  a model that no longer exists. Always perform the live lookup in Step 1.

## Durable caveats (not a catalogue)

These hold across catalogue changes and must still be re-checked, not assumed:

- The Copilot docs table lists model **display names**, not slugs. Confirm the
  exact slug against `opencode.json` or a working agent file before relying on it.
- `claude-fable-5` (as of 2026-10-29; re-verify) has different data-retention terms — Anthropic retains prompts
  and outputs to operate safety classifiers — and requires explicit org
  enablement. Flag this before recommending it for sensitive code.
- Models marked *public preview* rather than GA should be avoided for production
  agents.
- Billing is usage-based (per token, converted to AI credits) for current plans
  (as of 2026-10-29; the switch from request-based billing was 2026-06-01).
  Premium-request multipliers are a legacy concept that applies only to Copilot
  Pro / Pro+ users who stayed on an annual request-based plan, and that table
  omits newer models. Use it only when the user confirms such a plan:
  https://docs.github.com/copilot/reference/copilot-billing/request-based-billing-legacy/model-multipliers-for-annual-plans
- Allowances differ by plan (individual vs pooled Business / Enterprise); state
  which plan assumption a cost comparison uses.
- Promotional prices expire (for example a stated end date on a model's row).
  Report the expiry and the post-promo price if known, because a cost-based
  choice can flip.
