# Ontology

Typed nodes and edges. Every knowledge file is one node. Frontmatter is the graph. Prose is the explanation.

## Node kinds

| Kind | ID prefix | Typical path | Create when |
|---|---|---|---|
| system | `system:` | `knowledge/system.md` | Once per product |
| bounded_context | `context:` | `knowledge/contexts/<name>.md` | Domain language or ownership splits |
| capability | `capability:` | `knowledge/capabilities/<name>.md` | A job the system does for a user |
| module | `module:` | `src/<pkg>/AGENTS.md` or `knowledge` | A deployable or package boundary |
| type | `type:` | `<Stem>.context.md` beside source | Public type, or a type agents misuse |
| contract | `contract:` | `knowledge/contracts/<name>.md` | API, event, or schema other teams consume |
| flow | `flow:` | `knowledge/flows/<name>.md` | Cross-type request path with a consistency story |
| decision | `decision:` | `knowledge/decisions/<nnnn>-<slug>.md` | A choice that still constrains code |
| invariant | `invariant:` | `knowledge/invariants/<slug>.md` | A rule that must survive refactors |
| pattern | `pattern:` | `knowledge/patterns/<slug>.md` | Recurring design we want repeated |
| anti_pattern | `anti_pattern:` | `knowledge/patterns/<slug>.md` | Recurring design we want forbidden |
| runbook | `runbook:` | `knowledge/runbooks/<slug>.md` | Failure and repair, not happy-path design |

One file, one node. If a source file holds several public types, split context files (`Foo.Bar.context.md`) or extract the type.

## ID grammar

```
<kind>:<bounded-context>.<name>
```

Exceptions: `decision:0014`, `system:<product>`, kinds that are already unique without a context.

Rules:

- Lowercase.
- Dots separate context and name.
- Hyphens inside the name segment only.
- Stable. Rename the type in code? Keep the ID and add `name:` plus `source:`.
- Never reuse an ID after deprecation.

Examples:

- `type:billing.chargeservice`
- `context:billing`
- `capability:charge-customer`
- `flow:checkout`
- `decision:0014`
- `invariant:money-is-integer-minor-units`
- `contract:payments.charge-command`

## Required frontmatter

Every node:

```yaml
id: kind:name
kind: type
name: ChargeService
status: active          # evolving | active | deprecated
updated: YYYY-MM-DD
```

Type nodes also need:

```yaml
source: path/relative/to/repo
bounded_context: billing
owners: [billing]
```

Optional but expected on types: `implements`, `depends_on`, `must_not_depend_on`, `used_in`, `decided_by`, `invariants`, `tags`.

## Edge kinds

Store as ID lists in frontmatter. Direction is from the current node to each listed ID.

| Key | Meaning |
|---|---|
| `owns` | Module or context owns this type |
| `implements` | Type fulfills a contract |
| `depends_on` | Allowed collaborator the reader must understand |
| `must_not_depend_on` | Forbidden dependency, even if not currently imported |
| `collaborates_with` | Runtime partner that is not a hard compile dependency |
| `emits` / `consumes` | Events or commands |
| `guarded_by` / `invariants` | Rules that constrain this node |
| `decided_by` | ADRs that justify the design |
| `used_in` | Flows this type participates in |
| `realized_by` | Capability implemented by these types/flows |
| `supersedes` / `superseded_by` | Evolution |

Do not encode the full import graph. Extractors can do that from source. Intent edges are the ones an agent would otherwise get wrong.

## Status

- `evolving` — stub or incomplete; safe to refine; do not treat invariants as final
- `active` — constraints are current
- `deprecated` — keep the file; point `superseded_by` at the replacement

## Graph artifacts

`scripts/compile_graph.py` emits:

- `knowledge/index.yaml` — catalog of nodes (id, kind, path, status, source)
- `knowledge/graph.yaml` — `{nodes, edges}` with `from`, `type`, `to`

Hand-edit source nodes. Do not hand-edit `graph.yaml`.
