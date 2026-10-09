# Secret-protection baseline

Mandatory for **every** agent the designer generates, installs, or approves in
an audit — whether or not the user mentions secrets. It can be tightened, never
relaxed. A request to relax it must be refused with the risk stated and status
`UNSAFE TO CONTINUE`.

Protection must hold on every disclosure route: read, edit, shell, Git history,
content search, delegation hand-offs, and the agent's own output.

## 1. Universal path denials (`read` and `edit`)

Place these after `"*": allow` in `read`, and as explicit denials in `edit`:

```yaml
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

Add `"**/.env.example": allow` after the `.env.*` denial when the project uses
committed example files.

## 2. Content search

Set `grep: deny` unless the runtime is proven to enforce the `read` denials for
search results.

## 3. Shell denials

When an agent has any `bash` allow, append these denials **after** its allows
(last match wins):

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

Never allow bare `git diff*`. Allow only path-scoped forms such as
`git diff -- src/*`.

## 4. Stack additions (from target-project analysis)

| Detected | Additional rule |
|---|---|
| Maven | Deny `**/settings.xml`, `~/.m2/**`, `mvn *deploy*`, `mvn *release*`, `mvn help:effective-settings*`. |
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
reporting completion. A failure is a critical finding and blocks the runtime
gate.
