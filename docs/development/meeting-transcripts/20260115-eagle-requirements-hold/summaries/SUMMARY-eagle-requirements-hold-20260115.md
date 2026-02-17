# EAGLE Requirements Kickoff Meeting

**Date:** January 15, 2026
**Duration:** 57m 23s
**Type:** Project Kickoff

## Attendees

| Name | Role | Organization |
|------|------|--------------|
| Lawrence Brem | Manager, Software Development | NIH/NCI [E] |
| Ryan Hash | Product Visionary, Former CO | NIH/NCI [E] |
| Greg Black | AI Expert (New) | NIH/NCI [C] |
| Shan Liang | OA Systems Lead | NIH/NCI [E] |
| Jitong "Ingrid" Li | Business Analyst | NIH/NCI [C] |
| Tony Fu | Technical Program Manager | NIH/NCI [C] |
| Rene Pineda | Environment Setup | NIH/NCI [C] |
| Srichaitra Valisetty | APM | NIH/NCI [C] |

## Executive Summary

EAGLE is an AI-powered acquisition assistance tool designed to help NCI's Office of Acquisitions (OA) streamline the contract documentation process. The project aims to bridge the knowledge gap between CORs (Contracting Officer Representatives) who need to acquire products/services and COs (Contracting Officers) who execute the purchases legally.

### Problem Statement
- OA staff reduced from 800 to 200 people (75% reduction)
- Still responsible for 800 people worth of work
- Current process involves extensive back-and-forth between CORs and COs
- CORs lack contracting expertise; they "went to school to cure cancer"
- Document preparation takes weeks to months

### Solution Vision
- AI system that guides CORs through the acquisition process
- Generates complete acquisition packages (acquisition plans, SOWs, IGCEs, etc.)
- Reduces "ping-ponging" between CORs and COs
- Eventually acts as an agent to submit packages and track progress

## Key Technical Details

### Current Prototype
- Built on **Research Optimizer** platform
- Uses **Claude on AWS Bedrock**
- Multi-agent architecture with specialized agents:
  - Contracting Officer agent
  - Lawyer agent
  - Small Business Association agent
  - Ethics Officer agent
  - Supervisor agent
- Knowledge base: 250+ curated documents (FAR, NIH policies, best practices)
- Reads agent scripts from S3 bucket

### Identified Issues
- Cache bleeding between Research Optimizer and EAGLE
- Documents render as text only (need Word/PDF)
- Need conversation isolation per acquisition
- Need admin vs. user role separation

## Business Impact

| Metric | Value |
|--------|-------|
| Estimated FTE hours saved | 70 FTE |
| Annual cost savings | ~$14 million |
| Operating cost estimate | ~$2 million |

## Action Items

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 1 | Get Greg AWS account access | Srichaitra (Lata) | Immediate |
| 2 | Set up dev and production environments | Rene Pineda | Immediate |
| 3 | Review Research Optimizer codebase | Greg Black | This week |
| 4 | Fork codebase and create NCI version | Greg + Rene | Next |
| 5 | Implement Word/PDF document generation | Greg Black | High |
| 6 | Implement conversation isolation per acquisition | Greg Black | High |
| 7 | Add admin role with different guardrails | Greg Black | Medium |
| 8 | Prepare demo for Olga (NIH Head of Contracting) | Team | ASAP |
| 9 | Document requirements from this meeting | Ingrid Li | Ongoing |

## Key Decisions

1. **MVP Definition**: Working chat interface with document generation in Word/PDF format
2. **Primary Users**: CORs (for initial demo)
3. **Demo Target**: Olga (Head of NIH Contracting Activity) + 5-10 key COs
4. **Technology**: AWS Bedrock with Claude, Python codebase
5. **Management Style**: Agile/research-focused initially

## Risks & Considerations

- System must work flawlessly for first demo ("can't break first time out the door")
- Need to handle sensitive contract data (moderate security space required)
- FAR regulations changing rapidly (Revolutionary FAR Overhaul - RFO)
- Must prevent system from learning bad habits from untrained users

## Next Steps

1. Greg to review code at provided GitHub link
2. Environment setup by Rene
3. Regular sync meetings to track progress
4. No firm deadline, but "yesterday" is the target

---

*Transcribed by: Srichaitra Valisetty*
