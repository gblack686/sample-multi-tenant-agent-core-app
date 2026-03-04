# Plan: Skills vs Agents Routing Optimization

**Date**: 2026-03-02
**Task**: Optimize skill/agent dispatch to minimize token waste while preserving deep context for heavy tasks.

---

## Problem

All domain requests route to agents (full context window, expensive model). Simple questions and status checks waste tokens loading expertise.md + running on sonnet/opus when haiku + inline execution would suffice.

## Solution: Two-Tier Routing

### Tier 1 — Skills (inline, haiku, lazy-loaded)

For: question, maintenance, status checks

| Skill Type | Model | Why |
|------------|-------|-----|
| question | haiku | Read-only lookups, fast |
| maintenance | haiku | Status checks, simple bash |
| self-improve | haiku | Mechanical expertise update |

### Tier 2 — Agents (isolated context, sonnet/opus)

For: plan, build, plan_build_improve

Agent context isolation is valuable here — deep work needs full expertise loaded without polluting main conversation.

---

## Changes Required

### 1. Add `model: haiku` to all question + maintenance + self-improve skills

Files: `.claude/commands/experts/*/question.md`, `*/maintenance.md`, `*/self-improve.md`

```yaml
---
model: haiku
# ... existing frontmatter
---
```

### 2. Update CLAUDE.md routing table

Replace current flat routing with two-tier dispatch:

```
Question/status/maintenance → Skill (inline, haiku)
Plan/build/improve → Agent (isolated context, sonnet+)
```

### 3. Narrow agent descriptions

Change agent descriptions from broad keywords to build/plan-specific triggers:
- Before: "Invoke with 'frontend', 'nextjs', 'ui'"
- After: "Invoke for frontend plan, build, or improve tasks. NOT for simple questions — use /experts:frontend:question instead."

---

## Validation

1. `grep -r "^model:" .claude/commands/experts/` — All question/maintenance/self-improve have `model: haiku`
2. CLAUDE.md routing table has two tiers
3. Agent descriptions mention "plan/build" scope
