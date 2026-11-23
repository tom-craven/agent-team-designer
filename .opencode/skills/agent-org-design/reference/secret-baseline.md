# Secret-protection baseline

Mandatory for **every** agent the designer generates, installs, or approves in
an audit — whether or not the user mentions secrets. It can be tightened, never
relaxed. A request to relax it must be refused with the risk stated and status
`UNSAFE TO CONTINUE`.

Protection must hold on every disclosure route: read, edit, shell, Git history,
content search, delegation hand-offs, and the agent's own output.

Run `opencode --version` first and emit that major version's shape. V2 is the
native target; the V1 map below exists only for agents that must run on
OpenCode v1. Never mix the two shapes in one agent.

## 1. Path denials (`read` and `edit`)

### Native OpenCode V2 rules

V2 uses one ordered `permissions` list of `action` / `resource` / `effect`
rules, and the **last matching rule wins**. Place these denials after the broad
`read` allow and after the broad `edit` allow or ask.

```yaml
permissions:
  - action: read
    resource: "*"
    effect: allow
  - action: read
    resource: "*.env"
    effect: deny
  - action: read
    resource: "*.env.*"
    effect: deny
  - action: read
    resource: "*.pem"
    effect: deny
  - action: read
    resource: "*.key"
    effect: deny
  - action: read
    resource: "*.p12"
    effect: deny
  - action: read
    resource: "*.pfx"
    effect: deny
  - action: read
    resource: "*.jks"
    effect: deny
  - action: read
    resource: "*.keystore"
    effect: deny
  - action: read
    resource: "*id_rsa*"
    effect: deny
  - action: read
    resource: "*id_ed25519*"
    effect: deny
  - action: read
    resource: "*.npmrc"
    effect: deny
  - action: read
    resource: "*.pypirc"
    effect: deny
  - action: read
    resource: "*.netrc"
    effect: deny
  - action: read
    resource: "*settings.xml"
    effect: deny
  - action: read
    resource: "*gradle.properties"
    effect: deny
  - action: read
    resource: "*.tfvars"
    effect: deny
  - action: read
    resource: "*.tfstate"
    effect: deny
  - action: read
    resource: "*.tfstate.*"
    effect: deny
  - action: read
    resource: "*kubeconfig*"
    effect: deny
  - action: read
    resource: "*.kube/*"
    effect: deny
  - action: read
    resource: "*.aws/*"
    effect: deny
  - action: read
    resource: "*.azure/*"
    effect: deny
  - action: read
    resource: "*.docker/config.json"
    effect: deny
  - action: read
    resource: "*credentials*"
    effect: deny
  - action: read
    resource: "*secrets/*"
    effect: deny
```

Repeat the same denials with `action: edit`, after the broad `edit` rule.

**V2 path semantics:** `*` matches zero or more characters including `/`.
Do **not** write `**/` patterns. A leading `**/` does not match a root-level
file, so `**/.env` leaves `.env` readable. Use whole-path forms such as
`*.env`, `*settings.xml`, and `*.kube/*`, and verify them against real paths
(`.env`, `src/.env`, `gradle.properties`, `app/gradle.properties`,
`home/.kube/config`, `favicon.pem`).

Add an allow for `*.env.example` after the `*.env.*` denial only when the
project commits example files and reading them is required.

### Legacy V1 map (compatibility only)

For an agent that must run on OpenCode v1, express the same denials in the V1
`permission` map:

```yaml
permission:
  read:
    "*": allow
    "**/.env": deny
    "**/.env.*": deny
    "**/*.pem": deny
    "**/*.key": deny
    "**/*.p12": deny
    "**/*.pfx": deny
    "**/*.jks": deny
    "**/*.keystore": deny
    "**/id_rsa*": deny
    "**/id_ed25519*": deny
    "**/.npmrc": deny
    "**/.pypirc": deny
    "**/.netrc": deny
    "**/settings.xml": deny
    "gradle.properties": deny
    "**/gradle.properties": deny
    "**/*.tfvars": deny
    "**/*.tfstate": deny
    "**/*.tfstate.*": deny
    "**/kubeconfig*": deny
    "**/.kube/**": deny
    "**/.aws/**": deny
    "**/.azure/**": deny
    "**/.docker/config.json": deny
    "**/credentials*": deny
    "**/secrets/**": deny
```

The same keys become explicit denials in the V1 `edit` map. Do not carry these
`**/` keys into a V2 `permissions` list.

## 2. Content search

Deny content search unless the runtime is proven to enforce the `read` denials
for search results.

```yaml
# V2
- action: grep
  resource: "*"
  effect: deny
```

```yaml
# V1
grep: deny
```

## 3. Shell denials

When an agent has any shell allow, append these denials **after** its allows
(last match wins). In V2 they are `action: shell` rules; in V1 they are the
`bash` map.

```yaml
"env*": deny
"printenv*": deny
"set": deny
"export -p*": deny
"Get-ChildItem env:*": deny
"gci env:*": deny
"*cat *.env*": deny
"*type *.env*": deny
"*Get-Content *.env*": deny
"*gradle.properties*": deny
"*settings.xml*": deny
"*.tfvars*": deny
"*tfstate*": deny
"git log -p*": deny
"git log --patch*": deny
"git show*": deny
"git stash show*": deny
"terraform output*": deny
"terraform show*": deny
"terraform state*": deny
"kubectl get secret*": deny
"kubectl describe secret*": deny
"kubectl * -o yaml*": deny
"kubectl * -o json*": deny
"docker inspect*": deny
"docker history*": deny
"aws configure*": deny
"aws secretsmanager*": deny
"aws ssm get-parameter*": deny
"az keyvault secret*": deny
"gcloud secrets*": deny
"gh auth token*": deny
"gh secret*": deny
"mvn help:effective-settings*": deny
"*gradle* properties*": deny
"npm config list*": deny
"npm config get*": deny
```

Never allow an unrestricted `git diff` or a shell wildcard that could admit
extra Git options, refs, or pathspecs. A file-read denial does not filter Git
output: a content diff can disclose secrets in removed lines.

- **Directory-wide metadata:** an exact command may report status codes and
  paths for a named source directory, without file contents. For example,
  `git status --short -- src` or
  `git --no-pager diff --name-status --no-ext-diff --no-textconv -- src`.
  Use the trusted repository root as the working directory or a fixed Git
  `-C` argument. Keep the shell deny-by-default rule. Check that the exact
  metadata command is allowed and that content, staged and historical
  variants are not. Do not copy sensitive path names into reports.
- **Line-by-line changes:** allow only exact, working-tree commands for
  explicitly named, vetted non-sensitive files, with external diff drivers
  and text conversion disabled. For a directory-wide content review, use
  a separately sanitized artifact that excludes protected paths and redacts
  sensitive values in both added and removed lines. User approval does not
  override these protections.

V2 checks every segment of a compound command separately, so a
`cd <repo> && <script>` allow needs a separate exact `cd <repo>` allow. Prefer
non-compound commands.

## 4. Stack additions (from target-project analysis)

| Detected | Additional rule |
|---|---|
| Maven | Deny `settings.xml`, `~/.m2/*`, `mvn *deploy*`, `mvn *release*`, `mvn help:effective-settings*`. |
| Gradle | Deny `gradle.properties`; allow only named tasks; deny `properties`, `publish*`, `release*`. |
| npm/pnpm/yarn | Deny `.npmrc`, `npm publish*`, `npm config*`. |
| Terraform | Deny `*.tfvars`, `*.tfstate*`, `terraform output*`, `terraform state*`, `terraform show*`. |
| Kubernetes/Helm | Deny `kubeconfig*`, `kubectl get secret*`, `kubectl * -o yaml/json`, `helm get values*`. |
| Docker | Deny `.docker/config.json`, `docker inspect*`, `docker history*`, `docker push*`. |
| Cloud CLIs | Deny credential stores and secret-manager reads. |

## 5. Mandatory prompt clause

Every generated system prompt includes this, verbatim, under "What you never do":

```markdown
- Never read, print, log, commit, or pass to another agent any credential,
  token, private key, password, or connection string. If you encounter one,
  cite only the file and line, write `[REDACTED]` instead of the value, report
  it as a finding, and continue without using it.
- Never request, attempt, or suggest widening permissions to reach a
  secret-bearing file or command. Report `BLOCKED` instead.
```

Hand-off reports between agents follow the same redaction rule.

## 6. Verification

Run `python3 scripts/check_secret_baseline.py <path-to>/.opencode/agents` before
reporting completion (Windows: `py -3`) as one stand-alone shell command, never chained with `;`,
`&&`, `||`, pipes, or other checks (V2 permission-checks each segment, so one
unlisted segment denies the whole call). The checker accepts V1 maps and V2
rule lists; for V2 it probes realistic paths, so a `**/.env`-style regression
fails. A failure is a critical finding and blocks the runtime gate.
