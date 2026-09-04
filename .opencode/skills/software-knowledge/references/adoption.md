# Adoption

Do not document the whole system on day one.

## Week 1 — map and hottest path

- Root `AGENTS.md` router
- `ARCHITECTURE.md` with containers and dependency direction
- `knowledge/system.md`
- Type nodes only for public types on the hottest write path
- Run `init_knowledge.py` then fill stubs

## Week 2 — decisions and invariants

- Promote load-bearing choices to `knowledge/decisions/`
- Extract copied rules into `knowledge/invariants/`
- Add module `AGENTS.md` on packages agents already touch

## Week 3 — graph and habit

- Compile `graph.yaml` in CI or as a pre-commit check
- Fail lint on broken IDs and missing `source` paths
- Rule — public type change updates or adds the sibling context file in the same PR

## What good enough looks like

The agent can name:

- the bounded context it is in
- the types it must not import
- the invariant it must not break
- the ADR that forbids the "obvious" shortcut

Everything else can wait.

## CI sketch

```bash
python scripts/compile_graph.py .
python scripts/lint_knowledge.py .
```

Copy the two Python files from this skill into the repo under `scripts/` if the team wants CI without depending on the skill path. Keep the skill copy as the source of the workflow; keep the repo copy pinned.
