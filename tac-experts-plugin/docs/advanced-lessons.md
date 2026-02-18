# Advanced Lessons (9-14)

> Building on the 8 tactics, these lessons cover the meta-skills of agentic development.

---

## Lesson 9: Context Engineering

**The art of curating what goes into the agent's context window.**

- **CLAUDE.md**: The agent's persistent memory. Keep it lean, accurate, and up-to-date.
- **Expertise files**: Domain-specific knowledge the agent loads on demand via slash commands.
- **Spec files**: Task-specific plans created for a single workflow, consumed and archived.
- **Context budget**: Every token counts. Redundant content wastes context; missing content causes errors.
- **Hierarchy**: CLAUDE.md (always loaded) > expertise.md (loaded by command) > spec files (loaded per task).
- **Key principle**: Context engineering is the most important skill in agentic development. The agent is only as good as its context.

### Context Hierarchy

```
Always Loaded (Class 1)
├── CLAUDE.md           ← Project memory, conventions, constraints
├── .claude/settings.json  ← Model, permissions, tool config
└── Git config          ← .gitignore, .gitattributes

On Demand (Class 2)
├── .claude/commands/*.md     ← Slash commands
├── .claude/hooks/*.sh        ← Automated triggers
└── .claude/specs/*.md        ← Task plans

Expert Invocation (Class 3)
├── experts/{domain}/_index.md      ← Expert routing
├── experts/{domain}/expertise.md   ← Domain mental model
└── experts/{domain}/{action}.md    ← Expert commands
```

### Reduce / Delegate Framework

**Reduce**: Keep CLAUDE.md under 200 lines. Don't duplicate content. Don't inline diagrams. Each expert loads its context on invocation, not always-on.

**Delegate**: Domain questions go to experts. Architecture reference goes to docs. Agent definitions go to plugins. Implementation specs go to `.claude/specs/`.

---

## Lesson 10: Prompt Engineering

**Crafting effective prompts for agent system prompts, commands, and instructions.**

- **Be declarative, not procedural**: Tell the agent WHAT, not HOW. "Create a test that validates S3 operations" not "Open the file, go to line 200, add a function..."
- **Use structured formats**: Tables, checklists, and code blocks are parsed better than prose.
- **Constraints over instructions**: "Never modify files outside the test directory" is stronger than "Please be careful."
- **Role definition**: Start system prompts with a clear role. "You are an EAGLE SDK evaluation specialist."
- **Anti-patterns**: Vague instructions, implicit context, assuming the agent remembers previous conversations.

---

## Lesson 11: Specialized Agents

**Creating purpose-built agents for specific domains.**

- **Domain isolation**: Each agent owns one domain. Legal agent, test agent, deployment agent.
- **Skill files**: Encode domain expertise in structured markdown that the agent loads as system prompt.
- **Expert pattern**: The `.claude/commands/experts/` directory structure IS the specialization pattern.
- **Agent definition**: Name, model, system prompt, tools, and handoff rules.
- **Key insight**: A specialist agent outperforms a generalist on every domain-specific task.

---

## Lesson 12: Multi-Agent Orchestration

**Coordinating multiple specialized agents to complete complex workflows.**

- **Supervisor pattern**: One orchestrator agent delegates to specialist agents.
- **Handoff protocol**: Clear input/output contracts between agents.
- **Sequential vs parallel**: Use sequential for dependent tasks, parallel for independent tasks.
- **Context passing**: Each agent gets only the context it needs, not the full conversation.
- **Example**: Supervisor agent delegates to intake, legal, market, and tech review agents.

---

## Lesson 13: Agent Experts

**The expert system pattern for organizing agent knowledge.**

- **Structure**: `_index.md` (overview) + `expertise.md` (mental model) + command files (actions).
- **Commands**: question (read-only), plan (design), self-improve (learn), plan_build_improve (full workflow), maintenance (validate).
- **Self-improving**: Experts update their own expertise.md after completing tasks (ACT-LEARN-REUSE).
- **Composable**: Multiple experts can be invoked in sequence for cross-domain tasks.
- **Discovery**: `_index.md` lists available commands. Agents can discover expert capabilities.

### Standard Expert Files

| File | Purpose | Required |
|------|---------|----------|
| `_index.md` | Expert overview and command listing | Yes |
| `expertise.md` | Complete domain mental model | Yes |
| `question.md` | Read-only Q&A | Recommended |
| `plan.md` | Domain-aware planning | Recommended |
| `self-improve.md` | Expertise update (LEARN step) | Recommended |
| `plan_build_improve.md` | Full ACT-LEARN-REUSE workflow | Recommended |
| `maintenance.md` | Health validation | Recommended |
| `{domain-specific}.md` | Domain extensions (e.g., `cdk-scaffold`) | Optional |

### When to Create a New Expert

- You've asked the same domain question 3+ times
- A domain has non-obvious patterns that agents keep getting wrong
- You need accumulated knowledge across sessions (not just one-off context)

### Expert Golden Rules

1. Never edit expertise files manually — run `/experts:{domain}:self-improve`
2. Run self-improve after significant changes to that domain's code
3. Each expert validates its knowledge against the actual codebase, not assumptions

---

## Lesson 14: Codebase Singularity

**The end state where the codebase fully describes itself to the agent.**

- **Self-describing**: Every component has documentation the agent can find and understand.
- **Self-maintaining**: Experts self-improve, hooks auto-trigger, tests auto-run.
- **Self-extending**: The agent can add new experts, commands, and tests using existing patterns as templates.
- **Convergence**: As the codebase becomes more self-describing, agent performance asymptotically approaches human-level on all tasks.
- **Key insight**: The codebase singularity is not a destination, it's a direction. Every improvement moves you closer.
