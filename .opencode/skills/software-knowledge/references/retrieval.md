# Retrieval protocol

Goal — enough intent to edit safely, not the whole corpus.

## Always

Read root `AGENTS.md` if it exists. It is the router.

## When changing a source file

1. Sibling `<Stem>.context.md`
2. Directory `AGENTS.md` walking upward until the module boundary
3. `bounded_context` file listed in the type frontmatter
4. Nodes referenced by `decided_by`, `invariants` / `guarded_by`, `used_in`, `must_not_depend_on`
5. Stop. Do not preload every type in the module.

## When adding a feature

1. Matching `knowledge/capabilities/` node, or create one
2. Matching `knowledge/flows/` node if more than one type collaborates
3. Owning context file for language and ownership
4. Relevant ADRs

## When answering an architecture question

Query `knowledge/graph.yaml` first (or compile it). Useful walks:

- dependents of a type about to be deleted
- all nodes `guarded_by` an invariant
- types `used_in` a flow
- decisions that `applies_to` a module

Fall back to semantic search only for questions the graph cannot name.

## When context is missing

- Do not invent invariants.
- Create `status: evolving` stubs with **Open questions**.
- Say which nodes were absent.

## Budget

| Item | Load |
|---|---|
| Root AGENTS.md | always |
| One type node | when that file is in play |
| One-hop neighbors | when edges exist |
| ARCHITECTURE.md | structural or dependency changes |
| Full knowledge/ tree | never |

If a file is more than ~150 lines, read frontmatter plus the section the task names. Suggest splitting that node.
