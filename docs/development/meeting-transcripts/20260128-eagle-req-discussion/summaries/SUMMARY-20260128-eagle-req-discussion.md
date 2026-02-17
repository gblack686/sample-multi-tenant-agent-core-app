# EAGLE Requirements Discussion

**Date:** January 28, 2026
**Duration:** ~1h 11m
**Type:** Requirements Gathering / Use Case Definition / Technical Demo

## Attendees

| Name | Role | Organization |
|------|------|--------------|
| Greg Black | Technical Lead / Developer | NIH/NCI [C] |
| Ryan Hash | Subject Matter Expert / Former CO | NIH/NCI [E] |
| Lawrence Brem | Project Manager / Stakeholder | NIH/NCI [E] |
| Jitong "Ingrid" Li | Business Analyst | NIH/NCI [C] |
| Srichaitra Valisetty | Team Member | NIH/NCI [C] |

## Executive Summary

This meeting focused on requirements gathering, use case identification, and a demo of the acquisition package prototype UI. Key topics included:

1. **Eagle vs Research Optimizer**: Clarification that "Eagle" is the agent persona trained within Research Optimizer (Claude with extended tools)
2. **Prototype Demo**: Greg demonstrated the guided acquisition package intake UI with document checklist sidebar
3. **Agent Architecture**: Discussion of supervisor agent, compliance agent, and when sub-agents are invoked
4. **Use Cases**: Extensive brainstorming of high-priority use cases beyond just new acquisitions
5. **Requirements Focus**: Larry emphasized need to move from background discussion to formal use case documentation
6. **FFRDC Context**: Ryan provided background on the Frederick National Laboratory contract complexity

## Key Discussion Points

### Eagle Architecture Clarification

- **Research Optimizer**: Claude with extended tools from GitHub, Ryan's personal workspace
- **Eagle**: The agent persona trained within Research Optimizer using role-play methodology
- **Current Implementation**: Supervisor reads a file (00 supervisor) and has full knowledge base access
- **Sub-agents**: Called only when needed (compliance, tech, legal, etc.)
- **Compliance Agent**: Most frequently used - knows FAR, clauses, Part 13 vs Part 15 decisions

### Prototype Demo Feedback

Greg demonstrated the acquisition package UI with:
- Guided form walkthrough for requirements collection
- Document checklist sidebar with status indicators
- Timeline and funding collection forms

**Ryan's Feedback:**
- Add "I don't know" option to every question - prevent analysis paralysis
- Document checklist should be dynamic - some items become N/A based on dollar value
- Most questions can be answered by the agent once context is collected
- Acquisition Plan (AP) has very few unique questions - mostly summary information

**Larry's Feedback:**
- Need escape hatch for users who panic at required questions
- Make it clear questions are optional - system moves on if unanswered

### Agent Invocation Logic

Ryan explained when sub-agents should be called:
- **When user doesn't know**: As soon as someone says "I don't know" or asks a question
- **For document review**: Tech agent reviews SOW for inconsistencies
- **For compliance checks**: Compliance agent validates FAR applicability
- **Most acquisitions**: Can be handled by supervisor alone if information is complete
- **Document generation**: Only pull templates when ready to generate

### Use Cases Identified

**High Priority - Core Workflows:**
1. New acquisition package (full workflow)
2. Option exercise package preparation
3. Contract modification requests
4. Low-dollar micro-purchases ($14K quote → purchase request)

**CO Workflows:**
5. Package review and findings generation
6. Address supervisor findings
7. Solicitation development for SAM.gov

**Administrative:**
8. Contract close-outs (tedious, often neglected)
9. Government shutdown notification emails (thousands in 4 hours)
10. Technical score sheet consolidation after solicitation

**Policy & Compliance:**
11. Policy analysis for new executive orders
12. Clause compliance verification
13. Self-training and knowledge base improvement (Librarian agent)

**FFRDC-Specific:**
14. Modifications and awards on sole-source contracts
15. Conforming mods to sync with base contract changes

### Requirements Discussion

Larry emphasized the need to move from background discussions to formal requirements:
- Use cases need to be defined with actors, prerequisites, steps, and alternate paths
- Multiple actors: Core (requester), CO (processor), Leadership (oversight)
- Need mock-ups for each use case
- Scope management critical - potential scope is huge

### FFRDC Background (Frederick National Lab)

Ryan provided context on the FFRDC contract:
- $25-27 million invoices every two weeks
- 25-year contract just awarded
- Part 35 of FAR - "closer than usual" relationship
- SOW written collaboratively with contractor
- Faster processing than competitive acquisitions
- Same base structure - mostly modifications and task orders

### Ethical Considerations

Ryan highlighted an important adoption challenge:
- Eagle refused to generate sole source justification without valid reasoning
- This is correct behavior but may create organizational friction
- Solution: Focus on core users first - catch problems before they reach CO
- System should identify "slop" before it enters the contract shop

## Decisions Made

1. **Focus on core workflow first** for MVP - prevents ethical concerns at CO level
2. **Ingrid to develop formal use cases** with Ryan's input
3. **Greg to continue building prototype** with happy path focus
4. **Every question needs "I don't know" option** - prevent user abandonment
5. **Document checklist should be dynamic** based on acquisition type/value

## Action Items

| # | Action | Owner | Priority | Due Date |
|---|--------|-------|----------|----------|
| 1 | Create formal use cases from today's discussion | Ingrid | High | 1/29/2026 |
| 2 | Schedule use case review with Ryan | Ingrid | High | 1/29/2026 |
| 3 | Continue building acquisition package prototype | Greg | High | Ongoing |
| 4 | Add "I don't know" options to all forms | Greg | Medium | TBD |
| 5 | Get workflow matrix from Ingrid | Greg | High | TBD |
| 6 | Share architecture visuals regularly | Greg | Medium | Ongoing |

## Technical Notes

### Agent Hierarchy
```
Supervisor (00 supervisor file)
├── Compliance Agent (FAR, clauses, laws)
├── Tech Agent (SOW review, animal welfare)
├── Legal Agent (contract law questions)
├── Librarian Agent (knowledge base maintenance)
└── Analyst Agent (usage pattern analysis)
```

### Document Generation Philosophy
- Documents are "views" of a single data corpus
- Same information spreads across multiple documents
- Don't pull files until ready to generate
- Agent should know what questions to ask without reading templates

### Key Insight: Information Reuse
> "Think of the entire corpus of knowledge of your acquisition... each one of these documents is just a view of that data." - Ryan Hash

## Risks & Blockers

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Focus on acquisition package MVP first |
| AWS access pending | Medium | Continue with local development |
| Government shutdown | High | Eagle knowledge base can answer questions in Ryan's absence |
| User analysis paralysis | Medium | Add "I don't know" options throughout |
| Ethical friction on AI findings | Medium | Target core users first, catch issues before CO |

## Next Steps

1. Ingrid and Ryan to meet 1/29 for use case refinement
2. Greg to continue building prototype with happy path focus
3. Goal: Demo-ready simple + complex acquisition in ~2 weeks
4. Weekly "fireside chats" with Ryan to extract domain knowledge

## Quotable Moments

> "The answer to every question in contracts... is 'it depends.'" - Ryan Hash

> "If I'm giving something to the contract shop that looks like slop and the system can identify it as slop... then they don't have an ethical concern." - Ryan Hash

> "I can go to sleep with a healthy conscience." - Ryan Hash on 15 years without a protest

> "We need a fireside chat once a week to get all the really rich stories out of Ryan so we can feed the Eagle." - Greg Black

---

*Transcribed by: Microsoft Teams (Automated)*
*Summarized by: Claude Code*

---

## Appendix: Detailed Use Cases from Discussion

The following use cases were explicitly discussed during the meeting, organized by actor and priority.

### UC-01: New Acquisition Package (Core User)
**Actor:** Core (Requester)
**Priority:** High (MVP)
**Description:** Core has a need for a particular item that can only be obtained through acquisitions. They enter data into Eagle, which queries and gathers information, then creates the required artifacts.

**Prerequisites:**
- Core has identified a need
- Need cannot be fulfilled through existing contracts

**Basic Flow:**
1. Core accesses Eagle tool
2. Eagle identifies intent as acquisition package
3. Guided walkthrough collects requirements (item, timeline, funding, urgency)
4. System builds document checklist dynamically based on dollar value
5. Agent asks clarifying questions as needed
6. Documents are generated and assembled into package
7. Package sent to CO for review

**Alternate Paths:**
- User doesn't know answer → "I don't know" option, agent assists or skips
- Low dollar value → Simplified flow, fewer documents required
- User has existing package to reuse → Upload and modify previous package

---

### UC-02: Low-Dollar Micro-Purchase
**Actor:** Core (Requester)
**Priority:** High
**Description:** Very simple acquisition for items under micro-purchase threshold (~$14K).

**Basic Flow:**
1. User provides quote
2. System identifies as micro-purchase
3. Minimal questions asked
4. Purchase request generated for credit card person
5. Done in seconds

**Quote from Ryan:** "For some people, it's just as simple as 'here's my $14,000 quote, this is the thing I need' and then it just kind of makes a purchase request for you."

---

### UC-03: Option Exercise Package Preparation
**Actor:** Core/CO
**Priority:** High
**Description:** Annual exercise of contract options requiring documentation package.

**Context:** Recurring work - "here's my entire package from three years ago, I need to redo it for this year"

**Basic Flow:**
1. User provides previous package files
2. System ingests and understands context
3. User answers tuning/configuration questions
4. Updated package generated with current year information

---

### UC-04: Contract Modification Request
**Actor:** Core/CO
**Priority:** High
**Description:** Add money, time, or scope to existing contract.

**Basic Flow:**
1. Identify existing contract
2. Specify modification type (funding, period of performance, scope)
3. System generates modification package
4. CO reviews and processes

**Quote from Ryan:** "A modification to a contract is a very strong use case."

---

### UC-05: CO Package Review and Findings
**Actor:** Contracting Officer (CO)
**Priority:** Medium
**Description:** CO receives package from Core and needs to review for completeness and compliance.

**Basic Flow:**
1. Package submitted by Core
2. Eagle analyzes package against requirements
3. System generates list of findings/questions
4. CO addresses findings
5. If issues found, feedback sent to Core
6. Clean package proceeds to solicitation

**Quote from Larry:** "The core provides me with all the documentation. I need to make the documentation, get it out to SAM.gov and get a solicitation."

---

### UC-06: Address Supervisor Findings
**Actor:** CO
**Priority:** Medium
**Description:** CO receives findings from supervisor review and needs to address them.

**Basic Flow:**
1. Supervisor provides findings on package
2. Eagle helps CO understand and address each finding
3. Responses documented
4. Updated package submitted

---

### UC-07: Contract Close-Out
**Actor:** CO
**Priority:** Medium (High value, often neglected)
**Description:** Close out completed contracts - tedious work that piles up.

**Basic Flow:**
1. Upload all files from existing contract
2. System creates list of actions needed for close-out
3. Identifies who needs to approve/review
4. Tracks completion of close-out steps

**Quote from Ryan:** "It's one of those jobs that people just go 'I can't worry about close out... it just piles up and you hope someone forgets about it.'"

**Quote from Larry:** "That's what AI is really good at - doing those tedious tasks."

---

### UC-08: Government Shutdown Notification
**Actor:** CO
**Priority:** High (Time-critical when needed)
**Description:** During government shutdown, notify all contractors of their contract status.

**Constraints:**
- Thousands of emails needed
- Must be done within 4 hours of shutdown
- Cannot be prepared in advance ("you're not shut down, why waste the money?")

**Basic Flow:**
1. Shutdown announced
2. System identifies all active contracts
3. Determines status for each (fixed price with funding → continue, others → stop work)
4. Generates appropriate email for each contractor
5. CO reviews and sends

**Quote from Ryan:** "Thousands of emails that need to be written, drafted, reviewed and sent out... and they tell you to do it all within four hours."

---

### UC-09: Technical Score Sheet Consolidation
**Actor:** CO
**Priority:** Medium
**Description:** After solicitation, consolidate reviewer feedback on proposals.

**Problem:**
- Large solicitations may have 9 reviewers × 20 proposals = 180 score sheets
- Need to identify duplicate questions
- Need to consolidate into single question sheet per contractor
- Need summary report for file

**Basic Flow:**
1. Upload all technical score sheets
2. System identifies themes and duplicates
3. Consolidates into unified question list per contractor
4. Generates summary report

**Quote from Ryan:** "FFRDC... we had 1300 questions. How many of those questions were duplicate?"

---

### UC-10: Policy Analysis for New Executive Orders
**Actor:** Policy/CO
**Priority:** Medium
**Description:** When new executive orders or policy changes occur, analyze impact.

**Example:** "Trump puts out a new executive order prioritizing commercial first on all acquisitions."

**Basic Flow:**
1. Input new policy/executive order
2. System analyzes requirements
3. Determines what documentation changes are needed
4. Suggests template or checklist updates
5. Identifies affected ongoing acquisitions

---

### UC-11: Knowledge Base Maintenance (Librarian Agent)
**Actor:** System/Admin
**Priority:** Low (Future)
**Description:** Continuously maintain and improve the knowledge base.

**Functions:**
- Read through entire knowledge base
- Ensure consistency and correctness
- Update based on policy changes
- Flag outdated information

---

### UC-12: Usage Pattern Analysis (Analyst Agent)
**Actor:** System/Admin
**Priority:** Low (Future)
**Description:** Analyze system usage to improve processes.

**Example from Ryan:** "Read through all the risk analyses that every single CO filled out... see the same questions coming up again and again... maybe we should change our process in Eagle."

---

### UC-13: FFRDC Modifications and Awards
**Actor:** CO (FFRDC)
**Priority:** Medium
**Description:** Specialized workflow for sole-source FFRDC contracts.

**Context:**
- Single contractor (Frederick National Lab)
- Part 35 FAR - closer than usual relationship
- $25-27M invoices every two weeks
- All work off one base contract

**Basic Flow:**
1. Identify task order or modification need
2. Collaborative drafting with contractor (different from competitive)
3. Generate modification/award documents
4. Process through approvals

---

### UC-14: Conforming Modifications
**Actor:** CO (FFRDC)
**Priority:** Medium
**Description:** When base contract language changes, update all task orders.

**Problem:** "When they change one of the language... then they need to clean up everything."

**Basic Flow:**
1. Base contract updated
2. System identifies all affected task orders
3. Generates conforming modification for each
4. Tracks sync status across portfolio

---

### UC-15: Leadership Dashboard
**Actor:** Leadership
**Priority:** Medium
**Description:** Management visibility into acquisition pipeline.

**Questions to answer:**
- How many things are in the queue?
- What's going on?
- Who's assigned to what?
- Status of key acquisitions?

---

### UC-16: Solicitation Question Processing
**Actor:** CO
**Priority:** Medium
**Description:** Process incoming questions from potential offerors during solicitation.

**Problem (from FFRDC example):**
- 1300 questions received
- Many duplicates
- Some answerable by "read the RFP"
- Some need Core input
- Some require RFP changes

**Basic Flow:**
1. Ingest all questions
2. Categorize and de-duplicate
3. Route to appropriate party (Core, CO, policy)
4. Track responses
5. Generate amendment if RFP changes needed

---

### Use Case Priority Matrix

| Use Case | Actor | Complexity | MVP? | Value |
|----------|-------|------------|------|-------|
| UC-01: New Acquisition | Core | High | Yes | High |
| UC-02: Micro-Purchase | Core | Low | Yes | High |
| UC-03: Option Exercise | Core/CO | Medium | Yes | High |
| UC-04: Contract Mod | Core/CO | Medium | Yes | High |
| UC-05: Package Review | CO | Medium | Phase 2 | High |
| UC-06: Address Findings | CO | Low | Phase 2 | Medium |
| UC-07: Close-Out | CO | Medium | Phase 2 | High |
| UC-08: Shutdown Notify | CO | High | Phase 2 | Critical (when needed) |
| UC-09: Score Consolidation | CO | High | Phase 3 | Medium |
| UC-10: Policy Analysis | Policy | Medium | Phase 3 | Medium |
| UC-11: KB Maintenance | System | High | Future | Medium |
| UC-12: Usage Analysis | System | High | Future | Medium |
| UC-13: FFRDC Mods | CO | Medium | Phase 2 | High (for FFRDC) |
| UC-14: Conforming Mods | CO | High | Phase 3 | Medium |
| UC-15: Leadership Dashboard | Leadership | Medium | Phase 2 | Medium |
| UC-16: Solicitation Q&A | CO | High | Phase 3 | High |
