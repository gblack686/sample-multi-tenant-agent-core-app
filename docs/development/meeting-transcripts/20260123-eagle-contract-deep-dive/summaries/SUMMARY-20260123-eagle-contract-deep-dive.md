# EAGLE Contract Deep Dive

**Date:** January 23, 2026
**Duration:** ~1h 29m
**Type:** Technical Deep Dive / Contract Structure Analysis

> **Note:** The transcript for this meeting is incomplete. The automated transcription only captured fragments from the beginning (~0-1 min) and end (~1h 26m-1h 29m) of the meeting. This summary is based on available content only.

## Attendees

| Name | Role | Organization |
|------|------|--------------|
| Greg Black | Technical Lead / Developer | NIH/NCI [C] |
| Jitong "Ingrid" Li | Business Analyst | NIH/NCI [C] |
| Alvee Hoque | Team Member | NIH/NCI |

## Executive Summary

This meeting was a technical deep dive into EAGLE contract structure and data relationships. Key topics included:

1. **Contract Data Structure**: Discussion of REF (parent) and PIIT (child) relationships in Envision
2. **Vendor Invoice Issues**: Current problems with vendor information causing invoice submission failures
3. **Decision Tree Development**: Plan to create a decision tree for document generation and contract workflows
4. **AI Knowledge Base Integration**: Questions about how AI tool will leverage existing knowledge base beyond decision tree logic
5. **Architecture Documentation**: Plan to share architecture diagram with stakeholders (Renee)

## Key Discussion Points

### Contract Data Structure

- **REF** acts as parent contract identifier
- **PIIT** represents child records under each REF
- Contract information visible in Envision system
- Current issue: Vendor information is incorrect, causing invoice submission problems

### Decision Tree Approach

- Greg proposed creating a decision tree for:
  - Document generation workflows
  - Contract processing logic
  - Business rules understanding
- Purpose: Help team understand how the system worked historically and how it should work

### AI Knowledge Base Questions

Ingrid raised important questions about AI implementation:
- If the AI is limited to following the decision tree, will it venture outside to grab other information from the knowledge base?
- How will the trained model leverage existing materials?
- Greg confirmed the tree would be "loose" and "high level" - not overly restrictive

### Architecture & Documentation

- Greg to send architecture diagram to Renee
- All team members to be copied on documentation
- Recording and transcription notes to be shared with Ingrid

## Decisions Made

1. **Decision tree creation** to document contract processing business logic
2. **Architecture diagram** to be shared with Renee and team
3. **Team communication** - everyone to be copied on key documentation

## Action Items

| # | Action | Owner | Priority | Due Date |
|---|--------|-------|----------|----------|
| 1 | Create rough draft decision tree for contract processing | Greg | High | TBD |
| 2 | Send architecture diagram to Renee | Greg | High | Same day |
| 3 | Share recording and transcription with Ingrid | Greg | Medium | Same day |
| 4 | Analyze contract data and share findings | Ingrid | High | TBD |
| 5 | CC team on all architecture documentation | Greg | Medium | Ongoing |

## Technical Notes

### Contract Hierarchy in Envision
```
REF (Parent Contract)
├── PIIT (Child Order 1)
├── PIIT (Child Order 2)
└── PIIT (Child Order N)
```

### Current Issue
- Vendor information incorrect in system
- Causing invoice submission failures
- Requires data correction/analysis

## Risks & Blockers

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incomplete transcript | High | Request complete recording; schedule follow-up if needed |
| Vendor data issues | Medium | Ingrid analyzing; script development in progress |
| AI scope constraints | Medium | Decision tree will be loose/high-level to allow flexibility |

## Next Steps

1. Greg to distribute architecture diagram to team
2. Ingrid to complete contract data analysis
3. Review decision tree draft with Ryan in future meeting
4. Address vendor information issues

## Open Questions

- How will the AI tool balance decision tree guidance with broader knowledge base access?
- What is the scope of vendor data issues affecting invoice submissions?
- What additional analysis is needed from Ingrid's script?

---

*Transcribed by: Microsoft Teams (Automated)*
*Summarized by: Claude Code*
*Note: Partial transcript - middle portion of meeting not captured*
