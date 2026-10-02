---
name: software-knowledge
description: Document software intent as a typed knowledge graph next to the code — capabilities, flows, patterns, decisions, invariants, contracts, and type context. Use when adding class context files, AGENTS.md maps, ADRs, bounded-context docs, architecture knowledge, compiling knowledge/graph.yaml, scaffolding knowledge/, before editing a public type so invariants and decisions load first, and after any accepted change to harvest flows, patterns, and capabilities that would otherwise be buried in decisions.
metadata:
  version: "1.2"
  type: workflow
---

# Software Knowledge Graph

Turn a codebase into a durable intent graph. Code is the source of truth for *what*. Knowledge nodes are the source of truth for *why*, *constraints*, and *relationships*.

Classify the statement before anything else — see "Classify before you write". Read `references/ontology.md` before creating IDs or edges. Read `references/writing-guide.md` before drafting prose. Copy templates from `assets/`. Run scripts in `scripts/` instead of hand-writing catalogs.

## When this skill applies

- Scaffolding knowledge docs in a repo that has none
- Adding or updating a public type, module, API, or flow
- Answering "what may this depend on" or "why is it built this way"
- An agent about to edit code and needing the right context loaded
- Compiling or linting `knowledge/graph.yaml`
- After any accepted change, decision, or review — run the harvest workflow
- When `lint_knowledge.py` reports `coverage:` findings

Recording only decisions and invariants is a capture failure. A repository with
many decisions and no capabilities, flows, or patterns has buried them.

Do not create a node for private helpers or for facts the compiler already knows (signatures, imports, field lists).

## Default layout

```text
repo/
├── AGENTS.md
├── ARCHITECTURE.md
├── knowledge/
│   ├── index.yaml
│   ├── graph.yaml          # generated — do not hand-edit
│   ├── system.md
│   ├── contexts/
│   ├── capabilities/
│   ├── contracts/
│   ├── flows/
│   ├── decisions/
│   ├── invariants/
│   └── patterns/
└── src/<module>/
    ├── AGENTS.md
    ├── Foo.py
    └── Foo.context.md
```

Colocate type nodes. Name them `<Stem>.context.md` beside the source file. System-level nodes live under `knowledge/`.

## Retrieval protocol (before editing code)

Load in this order. Stop when the task is grounded. Do not dump the whole tree into context.

1. Root `AGENTS.md` (router only).
2. Sibling `<Stem>.context.md` of the file being changed.
3. Nearest directory `AGENTS.md`.
4. Owning `knowledge/contexts/<context>.md`.
5. One-hop neighbors from frontmatter — `decided_by`, `guarded_by`, `used_in`, `must_not_depend_on`.
6. Semantic search only if the graph does not resolve the question.

If those files are missing, create stubs (`status: evolving`) rather than inventing constraints.

Full rules — `references/retrieval.md`.

## Classify before you write

Most capture failures are classification failures, not writing failures. Do this
before opening any template.

### 1. Decompose the statement

A single sentence usually carries several claims. Split it before classifying.
"ChargeService is only called from checkout, and I'm not sure if refunds go
through it" is three claims, not one.

Never assume one statement means one node.

### 2. Map each claim to a kind

| Signal in the statement | Kind |
|---|---|
| Ordering, sequence, "when X then Y", "A calls B", a request path, a build or deployment sequence | `flow` |
| "must", "must never", "always", "only", a rule about all future code | `invariant` |
| "we chose", "we went with", "because", "don't reopen", names an ADR | `decision` |
| "same pattern as", "authored like every other", "we always shape X as", a reusable shape | `pattern` |
| "never do X again", a shape that was tried and failed | `anti_pattern` |
| "not sure", "undecided", "open question", "open item", "TBD" | keep the node it belongs to at `status: evolving`; if a real choice is pending, add a `decision` at `status: evolving` |
| "amended", "no longer holds", "replaces" | a new `decision` with `supersedes` |
| Ownership, team boundary, different domain language | `bounded_context` |
| A job the system does for a user; a new or changed endpoint/operation | `capability` (create, or link the existing one) |
| Consumed by another team or service | `contract` |
| "when it breaks, do X" | `runbook` |
| A public type, or one that is easy to misuse | `type` |

### 3. Apply the tie-breakers

- **A statement that names two or more participants and an order is a `flow`** —
  even when it also states a rule. Describing a path and constraining it are
  different jobs: create both, and link them.
- **`invariant` is the most over-matched kind.** Before writing one, ask whether
  the statement also describes a path, a decision, or an ownership boundary. If
  it does, that is a separate node.
- **Invariant nodes must not contain step lists.** If you are writing ordered
  steps inside an invariant, the flow node is missing.
- **`decision` vs `invariant`:** a decision could reasonably have gone the other
  way; an invariant must hold regardless of which way it went.
- **`decision` is the second most over-matched kind.** It is the easiest
  container, so flows, patterns, open questions, and amendments end up inside
  it. A decision records the choice and its consequences only; see the
  decision-split table in `references/writing-guide.md`.
- **Uncertainty is not a kind.** Do not withhold a node because part of the
  statement is unresolved. Create the node and mark it `evolving`.

### 4. Check back before you finish

Restate each claim from the original statement and name the node ID that now
carries it. Report any claim with no node. An unmapped claim is a capture
failure, not a judgement call.

## Workflows

### Install Python dependencies

The graph scripts require Python 3 and PyYAML. Install the dependency in the
repository's existing virtual environment rather than into the global Python
installation:

```bash
python -m pip install PyYAML
```

To run the regression tests, also install pytest:

```bash
python -m pip install pytest
```

If the repository has a dependency manifest or managed environment, add or
install `PyYAML` and `pytest` through that existing mechanism instead of using
ad-hoc global packages. Verify the installation before compiling:

```bash
python -c "import yaml; print(yaml.__version__)"
python -m pytest <this-skill>/tests
```

If a dependency cannot be installed, report compilation or tests as blocked or
skipped; do not describe them as successful.

### Scaffold a repo

From the repository root:

```bash
python <this-skill>/scripts/init_knowledge.py .
```

Then fill `knowledge/system.md` and `ARCHITECTURE.md`. Keep root `AGENTS.md` under ~120 lines. It is a map, not an essay.

Adoption sequence — `references/adoption.md`.

### Add or update a type node

1. Confirm the type is public or easy to misuse. If not, skip.
2. Copy `assets/type.context.md` to `<Stem>.context.md` beside the source. The template stays under the skill; compilation excludes the skill's `assets/` directory.
3. Set `id` as `type:<bounded-context>.<TypeName>` (see ontology).
4. Write Purpose, Non-goals, Invariants, Failure modes, How to change it.
5. Link edges — `depends_on`, `must_not_depend_on`, `used_in`, `decided_by`, `invariants`.
6. Recompile the graph.

Same PR as the code change. Stale nodes are worse than missing nodes.

### Add a decision, invariant, flow, capability, pattern, or anti-pattern

Copy the matching template in `assets/`. Give it a stable `id`. Point types at it; do not paste the same rule into every class file.

### Harvest after an accepted change (required)

Run this after every accepted change, before reporting completion. Classifying
what the user said is not enough; also classify what agents wrote.

1. List every artefact written or changed in the session, including new
   decisions and changed specs, schemas, or public types.
2. Re-run "Classify before you write" over each artefact's body, not only its
   title.
3. For each signal, create or update the node and link it:
   - an ordered list of steps or a request/build path → `flow`
   - "same pattern as", "like every other", a reusable shape → `pattern`
   - a rejected shape with a concrete failure → `anti_pattern`
   - a new or changed operation, endpoint, or public behaviour → `capability`
     linked by `realized_by` to its contract, flow, or types
   - open items → `decision` at `status: evolving`
   - amendments → new `decision` with `supersedes`
4. Slim the source decision to Context / Decision / Consequences / Status and
   replace moved content with node IDs.
5. **Verify against the source of truth.** Check every operational claim in a
   new or changed node — operation IDs, paths, tags, scopes, status codes, step
   order — against the code or spec, not against decisions. Decisions are
   history; later decisions may have renamed or moved what an earlier one
   describes. Name the source file in the node. Leave a claim you cannot verify
   as an open question rather than stating it.
6. **Propagate changed facts.** When a change renames, moves, or reverses
   something (a tag, path, scope, reference form, rule), search existing nodes
   for the old value and update or deprecate each one, including invariants and
   contexts. Add `supersedes` from the changing decision to every earlier
   decision it overrides, even if the earlier one does not mention it.
7. Compile, then lint with `--strict`. Resolve every `coverage:` finding or
   state why it is a false positive.
8. Report a harvest table: claim → node ID → created / updated / linked.

One agent owns the writing. Specialists flag candidates in their reports; the
knowledge owner (orchestrator or a dedicated curator) writes the nodes, so the
graph does not collect duplicates.

### Backfill an existing graph

When `coverage:` findings show buried knowledge, run the harvest workflow over
existing decisions oldest first. Read decisions to find *what* to extract, then
take operational detail from the current code or spec (harvest step 5). Create
extracted nodes at `status: evolving` until a human confirms them. Do not
delete or rewrite decision history; add links and `supersedes` edges. Check
existing invariants and contexts for rules that later decisions reversed.

### Compile and lint

```bash
python <this-skill>/scripts/compile_graph.py .
python <this-skill>/scripts/lint_knowledge.py .
python <this-skill>/scripts/lint_knowledge.py . --strict   # after harvest
```

`compile_graph.py` walks `**/*.context.md` and `knowledge/**/*.md`, reads YAML frontmatter, and writes `knowledge/index.yaml` plus `knowledge/graph.yaml`. It specifically excludes `.opencode/skills/software-knowledge/assets/`, so bundled templates such as `type.context.md` are not product nodes; real context nodes elsewhere remain discoverable.

`lint_knowledge.py` fails on broken IDs, missing `source` paths, unknown frontmatter keys or edge keys, invalid edge value shapes, unknown edge targets, and template markers left in `status: active` nodes. When adding an ontology edge, update the edge table in `references/ontology.md`, `EDGE_KEYS` in `scripts/compile_graph.py`, and its accepted metadata keys together.

The linter also compares the documented edge table with the compiler's `EDGE_KEYS` mapping. This prevents references from introducing a queryable edge such as `applies_to` without adding it to the ontology and compiler.

The linter also reports `coverage:` findings — knowledge captured under the wrong kind: no capability/flow/pattern nodes despite five or more decisions; a decision or invariant holding a 4+ step numbered list or an `A → B → C` chain without a linked flow; pattern language without a linked pattern; labelled amendments without a `supersedes` edge in either direction; labelled open items without an evolving decision; contracts without a capability; a decision whose `## Status` section disagrees with its frontmatter status. They warn by default and fail under `--strict`. A `status` outside `evolving | active | deprecated` is always an error.

### Keep the graph true

| Event | Action |
|---|---|
| New public type | Add `.context.md` in the same PR |
| Dependency direction changes | Update edges and `ARCHITECTURE.md` |
| Invariant changes | Update the invariant node; keep type files as pointers |
| Type removed | `status: deprecated` plus `superseded_by`; do not delete history |
| Unsure of a constraint | `status: evolving` and an open question — never a confident guess |
| New or changed operation / endpoint | Create or link its `capability` |
| Decision written | Run the harvest workflow before completion |

### Remove stale, duplicate, or superseded artefacts

An agent assigned this skill must have scoped edit access to `knowledge/**`,
including file deletion, without receiving shell deletion commands merely for
this workflow. Delete only when repository evidence proves that an artefact is
stale, an exact duplicate, or superseded with no historical value.

1. Identify the canonical replacement or document why no replacement is needed.
2. Search IDs, inbound references, and typed edges before deletion.
3. Redirect or remove affected edges while preserving still-valid intent.
4. Keep historical decisions as `status: deprecated` with `superseded_by`;
   supersession alone is not grounds for deletion. Delete one only when it is a
   proven duplicate.
5. Delete only within `knowledge/**` through scoped file-edit tooling.
6. Compile and lint the graph, then report each deleted path, its evidence, and
   all replacement or edge changes.

## ID and edge rules

- IDs are lowercase dotted names with a kind prefix — `type:billing.chargeservice`, `decision:0014`, `invariant:money-is-integer-minor-units`.
- Edges live in frontmatter lists, never only in prose.
- `must_not_depend_on` is an architectural constraint, not a current import list.
- `depends_on` lists allowed collaborators the reader must understand, not every import.

## Root AGENTS.md contract

Always-loaded. Keep it thin.

Must contain:

- How to build, test, and lint
- Hard invariants that apply everywhere
- Pointer table — if doing X, read Y
- Dependency direction in one short paragraph
- "Do not restate code in knowledge nodes"

Must not contain:

- Per-class essays
- Tool-personality text
- A catalog of every type

Module `AGENTS.md` files cover the local public surface and the first files to read.

## Quality bar

A type node is good if an agent can change the class without violating an invariant it would not have seen in the source. Delete sections that only restate the code. Prefer one linked invariant node over five copied bullet lists.
