# HR Recruiter

HR Recruiter is an OpenCode project for designing, auditing, restructuring, and
installing high-quality AI agents and runnable multi-agent teams.

It approaches agent design as organisational design: each role has one clear
job, explicit reporting lines, justified capabilities, least-privilege access,
and measurable completion criteria. It can work with software-engineering teams
and non-software teams such as research, operations, or content production.

## Primary agent

| Field | Value |
|---|---|
| Name | `hr-recruiter` |
| Mode | `primary` and project default |
| Model | `github-copilot/gpt-5.6-luna` |
| Temperature | `0.3` |
| Step budget | `40` |
| Colour | `#ec4899` |
| Edit access | `ask` |
| Bash access | Denied by default; read-only Git and confirmed directory creation only |
| Delegation | Denied |
| Skill access | Allowed |

Invoke it with `@hr-recruiter`, or start OpenCode in this directory:

```powershell
Set-Location E:\DEV\agentic-development\hr-recruiter
opencode
```

## Capabilities

HR Recruiter can:

- Analyse a target project before proposing roles.
- Inventory existing instructions, agents, prompts, skills, and OpenCode config.
- Design reporting lines, delegation rules, hand-off contracts, and review gates.
- Create complete OpenCode Markdown agent definitions.
- Select models from the live GitHub Copilot catalogue using current task-fit,
  benchmark, availability, and cost evidence.
- Derive skill requirements from each role rather than applying generic bundles.
- Reuse trusted local and global skills where appropriate.
- Search skills.sh before creating a replacement skill.
- Security-audit third-party skills before recommendation or installation.
- Create narrow local skills for genuine capability gaps.
- Audit agents and complete teams for overlap, prompt quality, model fit,
  permissions, step budgets, delegation, and recovery behaviour.
- Create or update `opencode.json`/`opencode.jsonc` so a team is runnable rather
  than merely documented.
- Preserve compatible repository and global guidance while excluding secrets,
  credentials, session data, and unrelated instructions.
- Validate paths, schema, model IDs, delegation, permission ordering, and
  representative completion and blocker scenarios.

## Gated team-creation lifecycle

End-to-end team work uses `agent-team-creation` to coordinate specialist skills.
Each stage must pass before the next begins.

```text
1. Analyse target project
   ↓ evidence gate
2. Design organisation
   ↓ organisation gate
3. Design each agent
   ↓ agent gate
4. Resolve and audit skills
   ↓ skill gate
5. Audit the complete team
   ↓ design release gate
6. Create OpenCode configuration
   ↓ runtime gate
7. Validate the installed team
```

### 1. Analyse the target project

The analysis identifies:

- Applicable `AGENTS.md` files and parent guidance.
- Repository `.agents/`, `.copilot/`, `.github/`, and `.opencode/` sources.
- Existing agents, prompts, skills, and OpenCode configuration.
- Applicable trusted global OpenCode and Copilot sources.
- Project workflows, technical domains, risks, constraints, and capability gaps.
- Conflicting, missing, included, and deliberately omitted guidance.

Credentials, private keys, authentication files, session databases, and broad
home-directory searches are excluded.

### 2. Design the organisation

The design first asks whether one agent is sufficient. If a team is justified,
it defines:

- One responsibility and explicit exclusions per role.
- A single orchestrator where coordination is needed.
- Reporting lines and permitted delegation targets.
- Hand-off triggers, inputs, outputs, completion ownership, and escalation.
- Independent gates for security, editorial, compliance, or delivery risk.

### 3. Design each agent

Each role receives:

- A searchable description and appropriate `mode`.
- A concise role-specific system prompt.
- A GitHub Copilot model selected from live evidence.
- A finite step budget.
- Ordered, least-privilege permission patterns.
- Only the skills required by its declared capabilities.
- Bounded retries, blocker handling, doom-loop recovery, and final statuses.

### 4. Resolve skills

Capabilities are resolved in this order:

```text
audited repository skill
→ trusted existing global skill
→ skills.sh candidate
→ security audit
→ new local skill only if a real gap remains
```

Popularity and publisher reputation help shortlist candidates but do not prove
security. Third-party skills require a security verdict before final
recommendation or installation.

### 5. Audit the team

The complete design is checked for:

- Duplicate or missing ownership.
- God-agents and vague personas.
- Invalid or circular delegation.
- Unavailable or unjustifiably expensive models.
- Missing or unaudited essential skills.
- Excessive edit, Bash, external-directory, task, or skill permissions.
- Inadequate step budgets, verification, completion, or recovery behaviour.

Unresolved critical findings block configuration.

### 6. Configure OpenCode

The generated configuration preserves compatible existing settings and wires:

- Agents and prompt sources.
- Models, modes, temperatures, and step budgets.
- Task delegation and ordered permission rules.
- Applicable local and global instructions.
- Trusted local and global skill paths.
- Doom-loop recovery without widening unsafe permissions.

### 7. Validate runtime behaviour

Validation confirms:

- JSON/JSONC syntax and current OpenCode schema compatibility.
- Every agent, prompt, instruction, skill path, and delegation target resolves.
- Markdown agent definitions agree with runtime configuration.
- Wildcard permission rules precede specific exceptions.
- Representative routing, denial, completion, and recovery paths behave as designed.
- Any check that could not be executed is explicitly reported.

## Specialist skills

| Skill | Responsibility |
|---|---|
| `agent-team-creation` | Coordinate the gated end-to-end lifecycle for a runnable team |
| `agent-org-design` | Design roles, reporting lines, delegation, hand-offs, and independent gates |
| `prompt-patterns` | Create concise role prompts with explicit purpose, workflow, and boundaries |
| `model-selection` | Select an available GitHub Copilot model using current task-fit and cost evidence |
| `find-skills-sh` | Discover third-party skills before creating duplicates |
| `skill-security-audit` | Review skills for injection, malicious code, secrets, excessive access, and supply-chain risk |
| `skill-creator` | Create or improve narrow reusable skills for confirmed gaps |
| `agent-audit` | Audit individual agents and assembled teams before release |
| `opencode-agent-config` | Define, migrate, audit, and validate runnable OpenCode agent configuration |

## Model-selection standard

Model choice starts with GitHub Copilot availability. A strong external
benchmark result is irrelevant if the model is unavailable through the Copilot
integration or disabled by organisation policy.

Every model recommendation reports:

- Recommended `github-copilot/<model-id>`.
- Availability evidence.
- The task-fit or ranking axis it wins on.
- Current cost or request multiplier where applicable.
- A cheaper alternative.
- A premium alternative.
- The date checked.
- Trade-offs and any runtime availability caveat.

OpenRouter adoption rankings are treated as usage evidence, not proof of quality.

## Workflow examples

### Audit an existing agent

```text
Audit .opencode/agents/backend-engineer.md. Check responsibility, description,
prompt, mode, model, permissions, steps, skills, recovery, and overlap. Do not
edit anything; give me severity-ordered findings and a concrete replacement.
```

Expected route: `agent-audit`, with `model-selection` only if the model field is
being assessed or changed.

### Design one agent

```text
Design a read-only Java security reviewer for a Spring Boot repository. It may
inspect diffs and run tests but must never edit, push, deploy, or expose secrets.
```

Expected result: a complete ready-to-use Markdown definition with model evidence
and least-privilege permission patterns.

### Analyse and install a software-engineering team

```text
Analyse E:\DEV\example-service, design the right engineering organisation,
resolve its skill requirements, audit the team, and install a runnable OpenCode
configuration.
```

Expected workflow:

1. Read-only repository and guidance analysis.
2. Evidence-based organisation proposal.
3. Per-agent model and capability design.
4. Skill reuse, discovery, security audit, or creation.
5. Complete-team audit.
6. Exact path report and user confirmation.
7. Installation and runtime validation.

### Restructure an existing team

```text
The backend agent currently owns Java, testing, CI, Docker, and infrastructure.
Analyse the repository and split responsibilities only where the workflows and
risk boundaries justify it. Preserve compatible existing configuration.
```

This typically routes through `agent-team-creation`, `agent-org-design`,
`agent-audit`, and `opencode-agent-config`.

### Create a non-software team

```text
Design a LinkedIn content team that analyses user-approved source code,
assesses professional value for recruiters and technical peers, creates
high-impact drafts, and independently checks disclosure risk. Drafts only;
no publishing or account access.
```

The same organisational standards apply: evidence ownership, strategy, content
production, independent review, explicit hand-offs, and least privilege.

### Discover and audit a third-party skill

```text
Find a maintained skill for pull-request review on skills.sh. Inspect the best
candidate, security-audit its complete contents and provenance, and recommend
installation only if the verdict is acceptable.
```

Expected route: `find-skills-sh` → `skill-security-audit`. An unaudited candidate
is labelled pending and is not approved for installation.

### Create a missing skill

```text
No suitable safe skill exists for converting approved source evidence into a
cited public-content brief. Create a narrow local skill with trigger tests,
boundaries, and a security assessment.
```

Expected route: `skill-creator` after existing-skill discovery has established a
real gap.

### Diagnose an OpenCode deadlock

```text
This orchestrator cannot delegate to qa-automation-engineer and repeatedly hits
the same permission error. Audit the config and propose the smallest safe fix.
```

Expected route: `opencode-agent-config`. The fix should correct the named task
pattern or target—not grant unrestricted task or Bash access.

### Handle a stuck-agent report

```text
Review .opencode/reports/doom-loop-backend-engineer-20260826-1030.md and decide
whether the root cause is a missing skill, permission, model, step budget,
instruction, or delegation target.
```

The report is routed to the owning specialist workflow rather than solved by
blanket permissions or arbitrary step increases.

## Installation safety

Agent, skill, and configuration installation is deliberately gated:

1. The user supplies a destination path.
2. HR Recruiter displays it back for confirmation.
3. The destination is analysed read-only.
4. Every exact directory and file to create, modify, or delete is reported.
5. The user confirms those paths.
6. Changes are installed only within the confirmed destination.
7. The result is validated and reported with named evidence.

HR Recruiter does not create global installations, global agent registrations,
or symbolic links. Agent files use kebab-case names under
`<confirmed-path>/.opencode/agents/`.

## Completion and recovery

Every task ends with exactly one status:

- `COMPLETE` — all requested work finished and verified.
- `PARTIAL` — useful work finished, with named remaining scope.
- `BLOCKED` — progress requires input, access, or an unavailable dependency.
- `UNSAFE TO CONTINUE` — proceeding would violate a security or permission boundary.

Repeated identical failures, permission deadlocks, unavailable dependencies,
oscillation, and OpenCode recovery prompts are treated as design signals. Agents
stop after bounded retries and produce a structured escalation instead of
looping or silently widening permissions.

## Project structure

```text
hr-recruiter/
├── AGENTS.md
├── README.md
├── opencode.json
└── .opencode/
    ├── agents/
    │   └── hr-recruiter.md
    └── skills/
        ├── agent-team-creation/
        ├── agent-org-design/
        ├── prompt-patterns/
        ├── model-selection/
        ├── find-skills-sh/
        ├── skill-security-audit/
        ├── skill-creator/
        ├── agent-audit/
        └── opencode-agent-config/
```
