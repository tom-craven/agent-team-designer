---
name: software-knowledge
description: Document software intent as a typed knowledge graph next to the code. Use when adding class context files, AGENTS.md maps, ADRs, bounded-context docs, architecture knowledge, compiling knowledge/graph.yaml, scaffolding knowledge/, or before editing a public type so invariants and decisions load first.
metadata:
  version: "1.0"
  type: workflow
---

# Software Knowledge Graph

Turn a codebase into a durable intent graph. Code is the source of truth for *what*. Knowledge nodes are the source of truth for *why*, *constraints*, and *relationships*.

Read `references/ontology.md` before creating IDs or edges. Read `references/writing-guide.md` before drafting prose. Copy templates from `assets/`. Run scripts in `scripts/` instead of hand-writing catalogs.

## When this skill applies

- Scaffolding knowledge docs in a repo that has none
- Adding or updating a public type, module, API, or flow
- Answering "what may this depend on" or "why is it built this way"
- An agent about to edit code and needing the right context loaded
- Compiling or linting `knowledge/graph.yaml`

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

## Workflows

### Scaffold a repo

From the repository root:

```bash
python <this-skill>/scripts/init_knowledge.py .
```

Then fill `knowledge/system.md` and `ARCHITECTURE.md`. Keep root `AGENTS.md` under ~120 lines. It is a map, not an essay.

Adoption sequence — `references/adoption.md`.

### Add or update a type node

1. Confirm the type is public or easy to misuse. If not, skip.
2. Copy `assets/type.context.md`.
3. Set `id` as `type:<bounded-context>.<TypeName>` (see ontology).
4. Write Purpose, Non-goals, Invariants, Failure modes, How to change it.
5. Link edges — `depends_on`, `must_not_depend_on`, `used_in`, `decided_by`, `invariants`.
6. Recompile the graph.

Same PR as the code change. Stale nodes are worse than missing nodes.

### Add a decision, invariant, flow, or capability

Copy the matching template in `assets/`. Give it a stable `id`. Point types at it; do not paste the same rule into every class file.

### Compile and lint

```bash
python <this-skill>/scripts/compile_graph.py .
python <this-skill>/scripts/lint_knowledge.py .
```

`compile_graph.py` walks `**/*.context.md` and `knowledge/**/*.md`, reads YAML frontmatter, and writes `knowledge/index.yaml` plus `knowledge/graph.yaml`.

`lint_knowledge.py` fails on broken IDs, missing `source` paths, unknown edge targets, and template markers left in `status: active` nodes.

### Keep the graph true

| Event | Action |
|---|---|
| New public type | Add `.context.md` in the same PR |
| Dependency direction changes | Update edges and `ARCHITECTURE.md` |
| Invariant changes | Update the invariant node; keep type files as pointers |
| Type removed | `status: deprecated` plus `superseded_by`; do not delete history |
| Unsure of a constraint | `status: evolving` and an open question — never a confident guess |

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
