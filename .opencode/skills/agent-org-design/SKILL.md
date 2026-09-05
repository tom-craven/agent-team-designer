---
name: agent-org-design
description: Design multi-agent team structures, reporting lines, and delegation rules. Use when creating more than one agent, setting up an orchestrator + specialists, defining who can call whom, or restructuring an agent team.
---

# Agent Org Design

Design clean multi-agent teams with clear ownership.

## Never do
- Create many overlapping primaries with no coordinator
- Give every specialist full edit/bash by default
- Leave delegation rules implicit
- Design roles without evidence from the target repository and its existing agents
- Leave hand-off inputs, outputs, or completion ownership undefined

## Patterns

**1. Simple**
- User ↔ one primary
- Occasional `@specialist`

**2. Orchestrator + Specialists (default recommendation)**
```
User
 └── Orchestrator (primary, edit/bash deny, task allow)
      ├── developer
      ├── pm
      ├── reviewer
      └── explore
```

When the team includes `software-knowledge`, the orchestrator is still
non-implementing for application code, but **must** be allowed to write
`knowledge/**` and run the skill compile/lint scripts so it can create and
maintain the knowledge graph. That exception is required, not optional.
Do not express it as `"*": deny` plus `knowledge/**`: allow — the catch-all
edit deny wins and blocks those writes. Deny `src/**`, `tests/**`, and
other application trees instead.

**3. Multiple primaries**
- User switches with Tab
- Only when user wants direct control of each role

## Design rules
1. Start from repository workflows, domains, constraints, and existing agents.
2. Confirm that one agent cannot safely and clearly perform the work first.
3. Use one clear orchestrator when using pattern 2.
4. Give each role one job and explicit non-responsibilities.
5. Apply least privilege per specialist.
6. Define an explicit delegation map and prevent undeclared lateral delegation.
7. Define each hand-off's trigger, required input, expected output, completion
   owner, and escalation path.
8. Add independent gates for risks that should not report through implementers.
9. Avoid too many chiefs.

## Required evidence

Before proposing the organisation, report:

- project instructions and configuration inspected;
- existing agents and skills that can be reused;
- recurring workflows or capability boundaries that justify each role;
- security, compliance, or infrastructure constraints;
- conflicts or assumptions that could change the structure.

## Required output

```markdown
## Recommended Team Structure

### Orchestrator
- Name + role

### Specialists
| Agent | Job | Mode | Key permissions |
|-------|-----|------|-----------------|

### Delegation rules
- Orchestrator may call: ...
- Specialists may call: ...

### Hand-off contracts
| From | To | Trigger | Required input | Expected output | Completion owner |
|------|----|---------|----------------|-----------------|------------------|

### Why this structure
- ...

### Repository evidence
- ...
```
