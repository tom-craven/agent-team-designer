---
name: find-skills-sh
description: Discover and recommend existing agent skills from https://www.skills.sh before creating new ones. Use when a capability might already exist, when designing agents that need skills, or when the user asks for skills to install.
---

# Find Skills from skills.sh

Prefer reuse over reinvention.

**Directory:** https://www.skills.sh  
**Install pattern:** `npx skills add <owner/repo>`

## Never do
- Recommend a skill without checking popularity/publisher reputation when possible
- Give a final install recommendation for any third-party skill before a security audit
- Invent a new skill when a strong existing one fits
- Treat install count, recency, or publisher reputation as security proof

## Process
1. Identify the needed capability
2. Search/browse https://www.skills.sh (leaderboard + search)
3. Shortlist using functional fit, maintenance, installs, and publisher signals
4. Inspect the candidate's complete contents and source provenance
5. Run `skill-security-audit` before a final recommendation or installation
6. Recommend only candidates whose verdict is acceptable for the intended use

## Recommendation format

```markdown
**Recommended skill:** `name`
**Source:** owner/repo
**Why it fits:** ...
**Install:**
```bash
npx skills add owner/repo
```
**Security note:** (audit status / caution)
```

If an audit has not completed, label the candidate `Pending security audit` and
do not provide it as an approved installation recommendation.

## Publisher signals
Strong defaults to check first: `anthropics`, `getsentry`, `vercel-labs`, high-activity maintainers on the leaderboard.
