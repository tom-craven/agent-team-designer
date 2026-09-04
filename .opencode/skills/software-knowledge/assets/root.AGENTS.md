# Project map for agents

This file is a router. Do not add per-class essays here.

## Commands
```bash
# install, test, lint — replace with the real commands
```

## Hard rules
- Knowledge nodes record intent, not signatures.
- Update the sibling `.context.md` in the same change as a public type.
- Never invent an invariant. Use `status: evolving` when unsure.

## Dependency direction
Describe the allowed arrows in 3–6 lines. Point at `ARCHITECTURE.md` for the diagram.

## If you are doing X, read Y

| Task | Read first |
|---|---|
| Change a public type | sibling `.context.md`, then nearest `AGENTS.md` |
| Change money / auth / another sensitive path | matching `knowledge/invariants/` and ADRs |
| Add a feature | `knowledge/capabilities/`, owning context file |
| Change structure or dependencies | `ARCHITECTURE.md` |
| Compile the intent graph | `python scripts/compile_graph.py .` |

## Knowledge layout
- Type nodes — `<Stem>.context.md` beside source
- System nodes — `knowledge/`
- Generated catalog — `knowledge/index.yaml`, `knowledge/graph.yaml`
