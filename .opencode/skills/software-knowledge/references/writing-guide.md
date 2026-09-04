# Writing guide

Write for an agent that will edit the code tomorrow and a human who will review that edit.

## What a type node must answer

1. Why does this type exist?
2. What is it *not* responsible for?
3. Which facts must remain true after any change?
4. How does it fail, and who repairs the failure?
5. How should the next change be shaped?

If a section does not help those questions, delete it.

## What never belongs in a type node

- Method signatures, parameter lists, return types
- Full import lists
- Field-by-field data-model dumps
- Restated docstrings
- Style nits (line length, naming) unless they are domain rules
- Temporary sprint notes
- Agent personality or tool-specific hooks

## Section recipe (type)

**Purpose** — one short paragraph. Name the job and the boundary.

**Non-goals** — three bullets max. Point to the type that owns the excluded job.

**Invariants** — rules, not preferences. Prefer IDs that point at `knowledge/invariants/`. Local bullets only for rules unique to this type.

**Mental model** — one happy-path chain. No sequence diagrams unless the flow is the point of the node.

**Failure modes** — timeout, partial commit, duplicate command. Name the repair owner.

**How to change it** — extension joints. "Add an adapter, do not branch here."

**See also** — IDs, not URLs into wikis.

## Voice

- Present tense, imperative where it constrains ("do not import catalog").
- Concrete names (`command_id`, `ChargeSucceeded`), not "the relevant identifier."
- No filler ("robust", "flexible", "handles all cases").
- Mark uncertainty with `status: evolving` and an **Open questions** section.

## Length

- Type node body — under ~80 lines after frontmatter
- Root `AGENTS.md` — under ~120 lines
- ADR — context, decision, consequences; skip meeting narrative
- Invariant — rule, rationale, enforcement (test, type, lint, review)

## Decision nodes

Write the choice that still constrains code. If the decision is fully absorbed and no longer load-bearing, mark `deprecated` or leave it as history linked from the type.

Required sections: Context, Decision, Consequences, Status.

## Capability vs type vs flow

- Capability — outcome for a user ("charge a customer")
- Type — code entity that helps produce it
- Flow — ordered collaboration and consistency boundary

Do not make the class inventory the product story. Capabilities keep the graph from collapsing into files.

## Freshness

Update `updated:` when constraints change, not when you fix a typo. A node whose `source` path no longer exists must be deprecated or retargeted in the same change.
