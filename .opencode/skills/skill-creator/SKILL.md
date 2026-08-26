---
name: skill-creator
description: Create, improve, and optimize agent skills to fill capability gaps. Use whenever a skill is missing, weak, incomplete, or when the user asks to create/edit/optimize a skill for yourself or any agent you design. Always use this before inventing ad-hoc instructions that should be a reusable skill.
---

# Skill Creator

Create high-quality Agent Skills that fill real gaps.

**Reference:** https://www.skills.sh/anthropics/skills/skill-creator

## When to use
- A needed capability is missing
- An existing skill is weak or under-triggers
- Designing an agent that needs supporting skills
- User asks to create / improve / optimize a skill

## Never do
- Create a skill that duplicates an existing good skill on skills.sh without checking first
- Ship a skill with scripts without a security audit
- Write vague descriptions that under-trigger
- Put “when to use” only in the body — it belongs in the description

## Workflow

1. **Identify the gap** — What job fails without this skill? Who needs it?
2. **Search existing** — Use `find-skills-sh` before writing from scratch
3. **Draft SKILL.md**
4. **Draft and test** — Define positive and negative trigger prompts plus representative workflow checks
5. **Security audit** — Use `skill-security-audit` for scripts, executable content, dependencies, or network operations
6. **Place it** — `.opencode/skills/<name>/SKILL.md`
7. **Verify it** — Confirm frontmatter, paths, references, boundaries, and test evidence
8. **Wire it** — Add it only to agents whose declared capability requirements need it
9. **Iterate** — Tighten description and body from real failures

## Required structure

```
skill-name/
├── SKILL.md               # required
└── (optional)
    ├── scripts/
    ├── references/
    └── assets/
```

### Frontmatter

```yaml
---
name: skill-name
description: What it does AND when to use it. Be slightly pushy so it triggers reliably.
---
```

### Body quality bar
- Imperative, concise instructions
- Explicit boundaries
- < 500 lines ideal
- Detail → `references/` when large

## Output when creating/upgrading a skill

1. Full `SKILL.md`
2. Path
3. Which agent(s) should use it
4. Gap it fills
5. Test prompts (3 that should trigger, 2 that should not)
6. Verification evidence and security-audit verdict when required

Do not mark the skill ready or wire it into an agent until required tests and
security checks pass. If a required check cannot run, report `PARTIAL` or
`BLOCKED` rather than treating the skill as complete.
