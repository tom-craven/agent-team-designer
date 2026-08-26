---
name: prompt-patterns
description: Apply proven system-prompt patterns when writing or improving agent prompts. Use whenever creating an agent system prompt, rewriting a weak prompt, or standardizing prompts across roles (engineer, reviewer, orchestrator, PM, writer, explorer).
---

# Prompt Patterns

Reusable structures for high-quality agent system prompts.

## Never do
- Write long, fluffy prompts
- Omit “never do” boundaries for high-risk roles
- Mix multiple jobs into one prompt

## Core pattern (default)

```markdown
You are a [precise role].

Your sole purpose is to [one job].

### What you do
- ...

### What you never do
- ...

### How you work
1. ...
2. ...

### Output style
- ...
```

## Role patterns

**Engineer / Implementer**
- Clean code, tests, follow project conventions
- Summarize changes
- Never drive-by refactors

**Reviewer / Auditor**
- Read-only mindset
- Severity-ordered findings
- Never edit unless explicitly asked

**Orchestrator**
- Plan → Delegate → Review → Synthesize
- List specialists it may call
- Never implement itself

**PM / Requirements**
- User value, acceptance criteria, prioritization
- Structured tickets
- Never write code

**Writer / Docs**
- Clarity, structure, examples
- Match existing docs tone

**Explorer / Researcher**
- Thorough but concise
- Cite sources (files/paths)
- Clear “searched X, found Y”

## Quality rules
- One job only
- Short imperative sentences
- Explicit boundaries for risky roles
- Prefer < 400–500 words unless complexity demands more
