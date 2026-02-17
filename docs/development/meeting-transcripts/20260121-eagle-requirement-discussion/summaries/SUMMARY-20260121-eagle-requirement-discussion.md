# EAGLE Requirement Discussion

**Date:** January 21, 2026
**Duration:** 1h 16m 18s
**Type:** Technical Requirements Discussion

## Attendees

| Name | Role | Organization |
|------|------|--------------|
| Ryan Hash | Product Owner / Government Lead | NIH/NCI [E] |
| Greg Black | Technical Lead / Developer | Contractor |
| Jitong "Ingrid" Li | Business Analyst | NIH/NCI [C] |
| Srichaitra "Lana" Valisetty | Project Support | NIH/NCI [C] |

## Executive Summary

This meeting focused on refining EAGLE's MVP requirements and technical approach. Key decisions included:

1. **Architecture Simplification**: Single agent with tools preferred over multi-agent system for POC
2. **Document Output**: Word/PDF export is a critical differentiator (currently only text output)
3. **Timeline**: Team has until May; MVP milestones being defined
4. **Scope Clarity**: System should guide CORs through acquisition process like a "contract specialist colleague"

Ryan emphasized that EAGLE should act like "Trish" - a senior contracting expert who intuitively knows what to do with any package handed to her, rather than requiring users to understand all branching logic upfront.

## Key Discussion Points

### Current System Limitations

- Research Optimizer outputs documents as **text only** - needs Word/PDF export
- System tends to "go on and on" rather than driving toward document completion
- Ryan: "It loves to fish, but it doesn't like catching fish. You need to boat the bass."
- Micro-purchases (<$15K) should be nearly automatic with minimal documentation

### Architecture Decisions

- Greg proposed **single agent with multiple tools** rather than multi-agent system
- Context windows are larger now; agents are smarter
- One agent can handle the workflow with proper tooling
- Will port to **Bedrock Agent Core** for production-grade observability and logging

### The "Trish Problem"

Ryan described the challenge using a former employee "Trish" as an example:
- Trish could handle any package handed to her correctly
- But she couldn't articulate all the branching logic that led to her decisions
- EAGLE needs to work the same way: "Here's what I have, what can I do with this?"
- System should pick apart the request and determine what applies

### MVP Priorities

Ingrid presented a requirements list from previous meetings. Ryan noted:
- Document export (Word/PDF) is critical but doesn't have to be first
- Team has until **May** (minimum)
- Focus on getting environment setup and core functionality working
- Pick and choose priorities based on what's achievable

### Production Readiness Concerns

Larry (not present) raised concerns about:
- Production ready scaling
- Handling load of 200+ potential users
- Isolated conversations per user
- Saved reports and conversation history

### Future Capabilities Discussed

- **Teams Integration**: EAGLE as a Teams user that can send messages
- Currently reactive (user must log in); could become proactive
- Example: "Hey, put this thing on the bid board, it's been 5 days"
- User could reply "Yeah, go ahead post it" and EAGLE would handle it

### Data Access Challenges

- **Envision** contains awarded contracts only (no denials)
- No direct tie between contracts and their documentation packages
- Political situation: 27 ICs used different contract management systems
- **Merlin** may become the standard system (speculation)
- Woodburn (contractor) no longer developing it

### Process Complexity

Ryan explained acquisition complexity:
- Simplified vs. negotiated contracts have different requirements
- Many "off-ramps and deviations on little tiny nuances"
- Current checklist system already handles most branching logic
- Core handbook loaded into system covers general process

## Decisions Made

1. **Single agent architecture** for POC (not multi-agent)
2. **Word/PDF export** is required but timing flexible
3. **Bedrock Agent Core** will be used for production features
4. **May deadline** for current team engagement
5. **Brian Park** (previous developer) can be contacted through proper channels if needed

## Action Items

| # | Action | Owner | Priority | Due Date |
|---|--------|-------|----------|----------|
| 1 | Port AI layer to Bedrock Agent Core | Greg | High | TBD |
| 2 | Implement Word/PDF document export | Greg | High | Before May |
| 3 | Review and prioritize requirements list | Ingrid/Ryan | High | Next meeting |
| 4 | Set up development environment | Greg | High | This week |
| 5 | Investigate Teams integration feasibility | TBD | Low | Future |
| 6 | Contact Brian Park (if needed) through Ryan | Greg/Ryan | Low | As needed |

## Technical Notes

### Current System State
- Research Optimizer has working chat interface
- S3 bucket contains templates under `supervisor-core`
- Checklist with FAR/HHSAR prescriptions already loaded
- Core handbook provides process guidance

### Proposed Architecture
```
Single EAGLE Agent
├── Knowledge Base (FAR, HHSAR, NIH policies)
├── Template Engine (Word/PDF generation)
├── Checklist Tool (requirements determination)
└── Document Generator (SOW, IGCE, AP, etc.)
```

### Key Thresholds Referenced
- **Micro-purchase**: Under $15,000 (minimal documentation)
- **Simplified Acquisition Threshold (SAT)**: $250,000
- **8A contracts**: Under $4 million

## Risks & Blockers

| Risk | Impact | Mitigation |
|------|--------|------------|
| Contract management system uncertainty | Medium | Focus on document generation, not integration |
| Brian Park availability | Low | Work from existing codebase; escalate through Ryan if needed |
| Multi-system political environment | Medium | Build standalone system first |
| User knowledge gaps about acquisition types | High | System must guide users, not assume knowledge |

## Next Steps

1. Greg to walk through implementation plan
2. Ingrid to finalize prioritized requirements list
3. Schedule follow-up meeting after environment setup
4. Define specific MVP1 vs MVP2 feature split

## Quotes of Note

> "It loves to fish, but it doesn't like catching fish. You need to boat the bass." - Ryan Hash

> "I kind of need the system to act like Trish." - Ryan Hash

> "We're in this really weird time with AI, where the systems aren't quite at the level that they could be at. But we feel like they are." - Brian Park (quoted by Ryan)

---

*Transcribed by: Srichaitra Valisetty*
*Summarized by: Claude Code*
