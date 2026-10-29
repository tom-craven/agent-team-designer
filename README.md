# Agent Team Designer

*Recruiting the right roles, skills, and models for governed AI agent teams.*

Agent Team Designer is a GitHub Copilot CLI and OpenCode project for designing,
auditing, restructuring, and installing high-quality AI agents and runnable
multi-agent teams.



It approaches agent design as organisational design: each role has one clear
job, explicit reporting lines, justified capabilities, least-privilege access,
and measurable completion criteria. It can work with software-engineering teams
and non-software teams such as research, operations, or content production.

## Getting started with GitHub Copilot CLI

Copilot CLI is a validated co-primary runtime for the repository's read-only
agent-design and audit workflows. The initial Copilot profile cannot edit files,
execute commands, or delegate work.

### 1. Install and authenticate

Follow the [official installation
guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli).
For example, on macOS or Linux with Homebrew:

```bash
brew install --cask copilot-cli
```

An active Copilot subscription is required. Launch `copilot`, then run `/login`
and follow the prompts if authentication is requested. See the [official
authentication guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli)
for other supported methods.

### 2. Start this project

From the repository root, launch Copilot CLI and select the custom agent:

```bash
copilot
```

```text
/agent agent-team-designer
```

For non-interactive use:

```bash
copilot --agent=agent-team-designer --prompt "Audit the existing agent definitions."
```

### 3. Inspect discovery

Use `/instructions`, `/skills`, and `/env` in an interactive session. On CLI
versions that expose the corresponding commands non-interactively, use:

```bash
copilot plugins list --kind skill --kind instruction
copilot skill list
```

The ten Copilot skill manifests under `.github/skills/` are discovery adapters.
Their canonical content remains under `.opencode/skills/` so the two runtimes do
not maintain independently edited copies.

### Keeping runtimes synchronized

Existing instructions, the OpenCode agent, and OpenCode skills remain canonical
and are not rewritten for Copilot. Copilot CLI reads `AGENTS.md` directly. The
files under `.github/` adapt the existing OpenCode agent and selected skills to
Copilot's different schema and discovery paths.

`AGENTS.md` instructs maintainers using either runtime to check for drift before
changing an adapted source. Skill changes still land in the canonical
`.opencode/skills/` file. Copilot can review or propose those changes, but an
editing-capable workflow must apply them there and then regenerate the
corresponding Copilot discovery adapter. The thin adapters are never
reverse-synchronized into the canonical skill.

After changing any canonical skill used by Copilot, regenerate the discovery
adapters. Commands below use `python3`; on Windows use `py -3` instead (bare
`python`/`python3` may be the Microsoft Store alias). See
[Development prerequisites](#development-prerequisites).

```bash
python3 scripts/sync_copilot_adapters.py
```

When `.opencode/agents/agent-team-designer.md` changes, review and adapt the
Copilot profile, then record the reviewed source version:

```bash
python3 scripts/sync_copilot_adapters.py --accept-agent-source
```

Before committing, run the non-writing check:

```bash
python3 scripts/sync_copilot_adapters.py --check
```

The `Copilot adapters` GitHub Actions workflow runs the same check for pull
requests, plus the adapter and secret-baseline tests and
`check_secret_baseline.py .opencode/agents`. It fails when generated skill
adapters are stale, the OpenCode agent
changes without review of its Copilot translation, the Copilot profile no
longer uses its read-only schema and tool set, or an agent loses the secret
baseline.

## Development prerequisites

Maintaining this repository (not just using the agent) needs:

- **Python 3.** Check with `py -3 --version` (Windows) or `python3 --version`.
  The scripts under `scripts/` use only the standard library; no virtual
  environment is needed for them.
- **pytest**, used by `tests/test_check_secret_baseline.py`:

  ```bash
  # Windows
  py -3 -m pip install pytest
  # macOS / Linux
  python3 -m pip install pytest
  ```

Run the checks and tests (Windows form shown; use `python3` elsewhere):

```bash
py -3 scripts/sync_copilot_adapters.py --check
py -3 scripts/check_secret_baseline.py .opencode/agents
py -3 -m unittest discover -s tests -p test_sync_copilot_adapters.py
py -3 -m pytest tests/test_check_secret_baseline.py
```

On Windows, two adapter tests create symbolic links and fail with
`WinError 1314` unless Developer Mode is on or the shell is elevated. They pass
on Linux CI.

Teams that the designer installs and that ship Python skills (for example
`software-knowledge`) use their own `.venv` with PyYAML and pytest; that is
separate from the requirements above.

## Runtime ownership

| Runtime | Configuration |
|---|---|
| Shared repository behavior | `AGENTS.md` |
| GitHub Copilot CLI | `.github/copilot-instructions.md`, `.github/agents/`, `.github/skills/` |
| OpenCode | `opencode.json`, `.opencode/agents/`, `.opencode/skills/` |

Copilot's tools and approval controls do not reproduce OpenCode's permission
patterns, model prefixes, step budgets, or delegation settings. OpenCode remains
fully supported during the migration.

## Getting started with OpenCode

Complete these steps before using the Agent Team Designer project.

### 1. Install OpenCode

Use the [official OpenCode installation documentation](https://opencode.ai/docs/)
for the latest installation options. On Windows, OpenCode recommends [Windows
Subsystem for Linux (WSL)](https://opencode.ai/docs/windows-wsl) for the best
experience.

For WSL, macOS, or Linux, install OpenCode with the official installer:

```bash
curl -fsSL https://opencode.ai/install | bash
```

On Windows, you can also install the native binary with Chocolatey or Scoop:

```powershell
choco install opencode
# or
scoop install opencode
```

If Node.js and npm are already installed, npm is another supported option:

```bash
npm install -g opencode-ai
```

Check that the installation is available from a new terminal:

```bash
opencode --version
```

### 2. Connect an LLM provider

OpenCode requires an LLM provider account and API key. From the OpenCode
interface, run `/connect`, choose a provider, and follow its authentication
steps. See the [provider documentation](https://opencode.ai/docs/providers/) for
available providers. [OpenCode Zen](https://opencode.ai/docs/zen/) is the
recommended starting point if you do not already have a provider configured.

### 3. Start this project

From the project directory, launch OpenCode:

```text
# Windows (PowerShell)
Set-Location <path-to-this-repository>
# macOS / Linux / WSL
cd <path-to-this-repository>
opencode
```

OpenCode loads the repository's `opencode.json`, `AGENTS.md`, agent definition,
and local skills automatically. The project default is
`agent-team-designer`; you can also invoke it explicitly with
`@agent-team-designer`.

> Replace `<path-to-this-repository>` with the directory containing this
> `README.md`.

### 4. Try the agent

Start with a read-only request, for example:

```text
Audit the existing agents in E:\DEV\example-project for responsibility overlap,
permission risks, model fit, and delegation problems. Do not edit anything.
```

For an overview of the project workflow and safety gates, read
[`AGENTS.md`](AGENTS.md) before asking the agent to create or install anything.

## Primary agent

| Field | Value |
|---|---|
| Name | `agent-team-designer` |
| Mode | `primary` and project default |
| Model | `github-copilot/claude-sonnet-5.5` (the Copilot profile uses `gpt-5.6-sol`) |
| Temperature | `0.3` |
| Step budget | `60` |
| Colour | `#ec4899` |
| Edit access | `ask`; `.opencode/reports/**` allowed; secret paths denied |
| Bash access | Denied by default; named Git, OpenCode, Ollama, directory, script, and test commands only; secret-disclosure commands denied |
| Delegation | Denied |
| Skill access | Allow-list of its ten skills; all others denied |

Invoke it with `@agent-team-designer`, or start OpenCode in the repository
directory (see "Start this project" above).

## Capabilities

Agent Team Designer can:

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

Skills are referenced in place and never copied. Local `.opencode/skills` and
`.github/skills` are added to `skills.paths` only when they exist. During
installation the designer always asks whether to include additional skill
repositories (for example your global skills or a shared team repository) and
asks for their paths. Each path is confirmed back to you, you choose the skills,
each is security-audited, and each is allowed individually in the agents' `skill`
permissions. For `software-knowledge` it asks which folder holds the skill.

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
| `opencode-agent-config` | Configure shared `opencode.json` settings and validate Markdown agents |
| `software-knowledge` | Document software intent as a typed knowledge graph; includes a `prune` workflow (analyse, plan, approve, tombstone superseded decisions) to keep the tree small; optional for generated teams |

## Model-selection standard

Model choice starts with GitHub Copilot availability. A strong external
benchmark result is irrelevant if the model is unavailable through the Copilot
integration or disabled by organisation policy.

Every model recommendation reports:

- Recommended `github-copilot/<model-id>`.
- Availability evidence.
- The task-fit or ranking axis it wins on.
- Current per-token cost from the GitHub pricing page (usage-based billing),
  not premium-request multipliers.
- A cheaper alternative.
- A premium alternative.
- The date checked.
- Trade-offs and any runtime availability caveat.

Quality evidence comes from the Artificial Analysis Coding Agent Index, cross-checked
with llm-stats. OpenRouter adoption rankings are treated as usage evidence, not
proof of quality.

Copilot Fusion is a router, not a model. It is considered only after the Fusion
check in `model-selection` (runtime exposure, plan, pricing, unverified quality)
and is not used by default for write-capable or high-risk roles.

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
2. Agent Team Designer displays it back for confirmation.
3. The destination is analysed read-only.
4. Every exact directory and file to create, modify, or delete is reported.
5. The user confirms those paths.
6. Changes are installed only within the confirmed destination.
7. The result is validated and reported with named evidence.

Agent Team Designer does not create global installations, global agent registrations,
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
agent-team-designer/
├── .github/
│   ├── agents/
│   │   └── agent-team-designer.agent.md
│   ├── skills/                  # generated adapters for the ten skills below
│   ├── workflows/
│   │   └── copilot-adapters.yml
│   └── copilot-instructions.md
├── AGENTS.md
├── README.md
├── opencode.json
├── docs/                        # demos, presentations, proposals
├── scripts/
│   ├── sync_copilot_adapters.py
│   └── check_secret_baseline.py
├── tests/
│   ├── test_sync_copilot_adapters.py
│   └── test_check_secret_baseline.py
└── .opencode/
    ├── agents/
    │   └── agent-team-designer.md
    ├── reports/                 # doom-loop escalation reports
    └── skills/
        ├── agent-audit/
        ├── agent-org-design/
        ├── agent-team-creation/
        ├── find-skills-sh/
        ├── model-selection/
        ├── opencode-agent-config/
        ├── prompt-patterns/
        ├── skill-creator/
        ├── skill-security-audit/
        └── software-knowledge/
```

The `.opencode/skills/` folder may also hold other skills that are not part of
the designer's allow-list.
