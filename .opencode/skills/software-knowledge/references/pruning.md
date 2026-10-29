# Pruning the knowledge tree

Goal: make the tree smaller without losing its essence or any key information.
Pruning is a reviewed change, never an automatic clean-up.

## Principles

1. **Analyse, plan, approve, apply.** Nothing is changed before the user approves
   the plan. There are no automatic merges, not even for exact duplicates.
2. **Tombstone, do not delete, superseded knowledge.** The ID, status, and
   `superseded_by` stay, so edges still resolve and the ID cannot be reused
   (ontology: "Never reuse an ID after deprecation"). The bulk of the text goes.
3. **Every claim keeps a home.** Build an essence ledger before editing. An
   unmapped claim blocks the operation.
4. **Never remove an `evolving` node without explicit user confirmation**, however
   old it is. Age alone only raises a question.
5. **Prefer shrinking over deleting.** Delete only exact duplicates and nodes the
   user confirmed as dead.

## Roles

- The **knowledge owner** (the orchestrator by default) owns the plan: it
  presents it to the user, obtains approval, and reviews the result.
- A **curator**, if one is installed, may carry out the analysis and the approved
  edits. The orchestrator keeps oversight: it must see the plan before approval,
  and the report after application. A curator never starts a prune on its own
  authority, and never applies a plan the orchestrator and user have not approved.
- If there is no curator, the orchestrator does both.

## Analyse (read-only)

```bash
python <this-skill>/scripts/prune_knowledge.py .
python <this-skill>/scripts/prune_knowledge.py . --stale-days 90 --max-lines 120 --json
```

The script never writes. Defaults: stale after **90 days**, oversized above
**120** body lines, near-duplicate at **0.90** similarity. Categories:

| Category | Meaning | Typical operation |
|---|---|---|
| `superseded` | Deprecated and replaced, still long; or partially superseded and active | tombstone, or review-partial |
| `duplicate` | Same-kind nodes with identical or near-identical bodies | merge, review-merge |
| `dead` | Deprecated, no replacement, nothing references it | confirm removal with the user |
| `orphan` | No edges in or out | link, merge, or confirm removal |
| `stale` | `evolving` and not updated for the threshold | ask the user; never remove unasked |
| `oversized` | Body above the limit | refine: drop restated code, extract flows/patterns |

`system`, `bounded_context`, and `invariant` nodes are never offered for orphan,
stale, or oversized pruning. Invariants may only be merged by a human decision.

The script finds candidates; it cannot judge whether two nodes carry the same
claims. That judgement is the agent's, recorded in the ledger.

## Operations

### Tombstone a superseded node

1. Read the old node and its successor. List the old node's claims.
2. For each claim decide: still true (already in the successor or another node),
   still true but missing (add it to the right node), or no longer true (record
   only why it changed).
3. Add `## History` to the successor: one or two lines on what the earlier
   decision chose and why it was replaced. Keep decisions that explain a
   non-obvious reversal; drop narrative that explains nothing.
4. Redirect inbound `decided_by`, `guarded_by`, `used_in`, and similar edges from
   the old ID to the successor (the analyser lists them under `redirect=`).
5. Shrink the old node to a tombstone: frontmatter unchanged (`status:
   deprecated`, `superseded_by`), body of at most 8 non-blank lines:

   ```markdown
   ## Status
   Deprecated. Superseded by decision:0014.

   ## Summary
   One sentence: what this chose.

   ## Why it was replaced
   One sentence, or "See decision:0014 History."
   ```

   Keep the `## Status` wording consistent with the frontmatter, or the linter
   reports a status disagreement.

### Merge duplicates

1. Choose the survivor: the node with more inbound edges, the older ID, or the
   clearer text.
2. Copy any claim the survivor lacks. Do not copy claims verbatim twice.
3. Redirect every inbound edge to the survivor.
4. Delete the duplicate through scoped file tooling only when the claims are
   identical or fully absorbed and no edge still points at it. Otherwise
   tombstone it with `superseded_by: <survivor>`.

### Refine an oversized node

Remove text that restates code (signatures, imports, field lists), extract an
ordered path into a `flow`, a reusable shape into a `pattern`, and open items into
an `evolving` decision, each linked. Do not shorten by deleting constraints.

### Stale `evolving` nodes

Present each one to the user with its age and what it holds. For each, the user
chooses: keep, refresh (`updated` and review), resolve (make it `active` or
supersede it), or remove. Remove only on an explicit instruction naming that node.

## The plan

Present the plan to the user before any edit:

| Operation | Node(s) | Evidence | Saves (lines) | Redirects | Needs user confirmation |
|---|---|---|---|---|---|

followed by the **essence ledger**: for every source node, each claim and the node
ID that will carry it (a claim with `no longer true: <reason>` counts as carried
by the History line). Any claim with no destination stops that operation.

## Apply and verify

1. Apply only the approved operations, using scoped edit tooling in `knowledge/**`.
2. Compile, then lint with `--strict`. There must be no dangling edges.
3. Re-run the analyser and report before and after: node count, total bytes,
   candidates remaining.
4. Report every path changed or deleted, the evidence, and every edge redirected.
5. Declare anything not applied (for example stale nodes the user kept).

## Never prune

- An `invariant` (unless a human decides it duplicates another).
- An `active` decision that still constrains code.
- An `evolving` node holding an open question, without user confirmation.
- A type node whose `source` file still exists (merge exact duplicates only).
- The graph files `knowledge/index.yaml` and `knowledge/graph.yaml` (generated).
