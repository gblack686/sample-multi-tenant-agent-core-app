# EAGLE POC Implementation Plan

## Executive Summary

This plan outlines the implementation of the EAGLE (Enhanced Acquisition Guidance Learning Engine) Proof of Concept. The POC demonstrates two end-to-end workflows for NCI Office of Acquisitions: simple product acquisition (<$250K) and complex product acquisition (≥$250K).

**Architecture Decision:** Single agent with structured report output (Option C) rather than 8 separate specialist agents.

**Target Demo:**
1. "I need to buy lab equipment for $50K" → Simple workflow → 3 documents
2. "I need IT services for $500K over 3 years" → Complex workflow → 6+ documents
3. Download all documents as Word files

---

## Phase 1: Foundation (Prerequisites)

### 1.1 Environment Access
| Task | Owner | Status |
|------|-------|--------|
| PIV card / VPN access | IT/Security | [ ] |
| Access to dev environment | IT/Security | [ ] |
| PostgreSQL database access | DevOps | [ ] |
| S3 bucket `rh-eagle` access | DevOps | [ ] |

### 1.2 Data Collection (Blocked on OA Team)
| Task | Owner | Status |
|------|-------|--------|
| Obtain FAR/HHSAR documents (or confirm S3 location) | OA Team | [ ] |
| Obtain NIH acquisition policy documents | OA Team | [ ] |
| Obtain document templates (SOW, IGCE, AP) | OA Team | [ ] |
| Confirm product database access (if available) | OA Team | [ ] |
| List of approved product search sources | OA Team | [ ] |

### 1.3 Architecture Confirmation (Blocked on Ryan)
| Decision | Options | Status |
|----------|---------|--------|
| Multi-agent vs structured report | Option C recommended | [ ] Awaiting confirmation |
| Essential specialist sections for POC | 4 proposed (Compliance, Financial, Technical, Summary) | [ ] Awaiting confirmation |
| Scope: Products only or include services? | Products recommended | [ ] Awaiting confirmation |

---

## Phase 2: Core Infrastructure

### 2.1 Verify Existing EAGLE Agent
**Location:** `server/services/schema.js:607-707`

```javascript
// Existing configuration
{
  id: 3,
  name: "EAGLE",
  promptId: 3,
  tools: ["search", "browse", "code", "editor", "think", "data"]
}
```

**Tasks:**
| Task | Estimate | Status |
|------|----------|--------|
| Verify EAGLE agent loads correctly at `/tools/chat-v2?agentId=3` | - | [ ] |
| Verify S3 bucket `rh-eagle` exists and is accessible | - | [ ] |
| Audit KB folder contents (8 folders) | - | [ ] |
| Test `data` tool can retrieve files from `rh-eagle` | - | [ ] |

### 2.2 Knowledge Base Audit
**S3 Bucket:** `rh-eagle`

| Folder | POC Essential | Files Present | Status |
|--------|---------------|---------------|--------|
| `supervisor-core/` | Yes | [ ] TXT [ ] DOCX | [ ] |
| `compliance-strategist/` | Yes | [ ] TXT [ ] DOCX | [ ] |
| `financial-advisor/` | Yes | [ ] TXT [ ] DOCX | [ ] |
| `technical-translator/` | Yes | [ ] TXT [ ] DOCX | [ ] |
| `market-intelligence/` | Maybe | [ ] TXT [ ] DOCX | [ ] |
| `legal-counselor/` | Defer | [ ] TXT [ ] DOCX | [ ] |
| `public-interest-guardian/` | Defer | [ ] TXT [ ] DOCX | [ ] |
| `shared/` | Yes | [ ] TXT [ ] DOCX | [ ] |

---

## Phase 3: Structured Report Template

### 3.1 Define Report Structure

**Simple Acquisition Report (<$250K SAT):**
```markdown
# Acquisition Package Report
## Request Summary
- Requested Item: [from user input]
- Estimated Value: $XX,XXX
- Acquisition Type: Simplified Acquisition
- Threshold: Below SAT ($250,000)

## 1. Compliance Review
- Applicable FAR citations
- HHSAR requirements
- NIH policy compliance

## 2. Financial Analysis (IGCE)
- Cost breakdown
- Price reasonableness
- Market comparison

## 3. Technical Requirements (SOW)
- Scope of work
- Deliverables
- Performance standards

## 4. Recommendation Summary
- Recommended approach
- Contract type
- Next steps for COR

## Generated Documents
- [ ] Statement of Work (SOW)
- [ ] Independent Government Cost Estimate (IGCE)
- [ ] Acquisition Plan (Basic)
```

**Complex Acquisition Report (≥$250K):**
```markdown
# Acquisition Package Report
## Request Summary
- Requested Item: [from user input]
- Estimated Value: $XXX,XXX
- Acquisition Type: Negotiated Contract
- Threshold: Above SAT ($250,000)

## 1. Compliance Review
- Applicable FAR citations
- HHSAR requirements
- NIH policy compliance
- Competition requirements

## 2. Financial Analysis (IGCE)
- Cost breakdown by CLIN
- Price reasonableness analysis
- Historical pricing data
- Should-cost analysis

## 3. Technical Requirements (SOW/PWS)
- Scope of work
- Deliverables
- Performance standards
- Quality assurance

## 4. Market Research Summary
- Market conditions
- Available sources
- Contract vehicles

## 5. Recommendation Summary
- Recommended approach
- Contract type
- Evaluation factors
- Next steps for COR

## Generated Documents
- [ ] Statement of Work (SOW)
- [ ] Acquisition Plan (Full)
- [ ] Independent Government Cost Estimate (IGCE)
- [ ] Market Research Report
- [ ] Source Selection Plan
- [ ] D&F (if T&M contract type)
```

### 3.2 Implementation Tasks
| Task | Priority | Status |
|------|----------|--------|
| Create report template markdown structure | High | [ ] |
| Add threshold detection logic ($250K branch) | High | [ ] |
| Implement section-by-section generation | High | [ ] |
| Add FAR citation validation | High | [ ] |
| Create "Generate Documents" action | High | [ ] |

---

## Phase 4: Document Generation

### 4.1 Word Document Export (Critical Blocker)

**Current State:** Text/HTML output only
**Required:** Downloadable .docx files

**Approach:** Adapt Consent Crafter pattern using mammoth.js

**Reference Implementation:** `client/pages/tools/consent-crafter/`

| Task | Priority | Status |
|------|----------|--------|
| Study Consent Crafter DOCX generation pattern | High | [ ] |
| Create SOW template (.docx with placeholders) | High | [ ] |
| Create IGCE template (.docx with placeholders) | High | [ ] |
| Create Acquisition Plan template (.docx) | High | [ ] |
| Implement placeholder replacement engine | High | [ ] |
| Add download button/action to UI | High | [ ] |
| Test document generation end-to-end | High | [ ] |

### 4.2 Template Placeholder Syntax
**Pattern from lay-person-abstract:**
```
{{variable_name}}
{{FOR item IN list_variable}}
- {{$item}}
{{END-FOR item}}
```

**SOW Template Placeholders:**
```
Project Title: {{project_title}}
Period of Performance: {{pop_start}} to {{pop_end}}
Total Estimated Value: {{total_value}}

1. BACKGROUND
{{background_text}}

2. SCOPE
{{scope_text}}

3. DELIVERABLES
{{FOR deliverable IN deliverables}}
- {{$deliverable}}
{{END-FOR deliverable}}
```

---

## Phase 5: Adaptive Questioning Flow

### 5.1 Simple Workflow Questions
```
1. What do you need to acquire? [free text]
2. What is the estimated cost? [number]
   → If < $250K: Simple workflow
   → If ≥ $250K: Complex workflow
3. When do you need it? [date]
4. Any specific requirements? [free text]
→ Generate Simple Report + 3 Documents
```

### 5.2 Complex Workflow Questions
```
1. What do you need to acquire? [free text]
2. What is the estimated cost? [number] → ≥$250K detected
3. Is this a new requirement or follow-on? [choice]
4. What is the period of performance? [date range]
5. Are there any incumbent contractors? [yes/no + text]
6. What contract type is preferred? [FFP/T&M/Cost-Plus]
7. Are there small business set-aside requirements? [choice]
8. Any sole source justification needed? [yes/no]
→ Generate Complex Report + 6 Documents
```

### 5.3 Implementation Tasks
| Task | Priority | Status |
|------|----------|--------|
| Implement threshold detection ($250K branch) | High | [ ] |
| Create question flow state machine | High | [ ] |
| Store answers in session context | High | [ ] |
| Map answers to template placeholders | High | [ ] |
| Add "back" navigation for corrections | Medium | [ ] |

---

## Phase 6: Integration & Testing

### 6.1 End-to-End Test Scenarios

**Test 1: Simple Product Acquisition**
```
Input: "I need to buy a centrifuge for $45,000"
Expected:
- Threshold detected: Simple (<$250K)
- Questions: 3-4 basic questions
- Report: 4 sections generated
- Documents: SOW, IGCE, Basic AP downloadable as .docx
```

**Test 2: Complex Product Acquisition**
```
Input: "I need IT services for $500,000 over 3 years"
Expected:
- Threshold detected: Complex (≥$250K)
- Questions: 8-10 detailed questions
- Report: 5 sections generated
- Documents: SOW, Full AP, IGCE, Market Research, SSP downloadable as .docx
```

### 6.2 Validation Checklist
| Test | Expected Result | Status |
|------|-----------------|--------|
| Agent loads at correct URL | `/tools/chat-v2?agentId=3` works | [ ] |
| KB query works | `data` tool retrieves from `rh-eagle` | [ ] |
| Threshold detection | $50K → Simple, $500K → Complex | [ ] |
| FAR citations accurate | No fabricated citations | [ ] |
| Simple report generates | 4 sections complete | [ ] |
| Complex report generates | 5 sections complete | [ ] |
| SOW downloads as .docx | Valid Word file | [ ] |
| IGCE downloads as .docx | Valid Word file | [ ] |
| AP downloads as .docx | Valid Word file | [ ] |
| Full workflow <5 minutes | User can complete in reasonable time | [ ] |

---

## Phase 7: Demo Preparation

### 7.1 Demo Script
```
DEMO 1: Simple Acquisition (2-3 minutes)
─────────────────────────────────────────
[Open EAGLE at /tools/chat-v2?agentId=3]

User: "I need to buy a laboratory centrifuge for about $45,000"

[EAGLE asks 3-4 clarifying questions]

[EAGLE generates Acquisition Package Report]
- Shows Compliance Review with FAR 13 citations
- Shows IGCE breakdown
- Shows SOW draft

[User clicks "Download Documents"]
- Downloads SOW.docx, IGCE.docx, AP-Basic.docx

DEMO 2: Complex Acquisition (4-5 minutes)
─────────────────────────────────────────
User: "I need IT managed services for $500,000 over 3 years"

[EAGLE detects ≥$250K threshold, switches to complex flow]

[EAGLE asks 8-10 detailed questions about:
 - Contract type preference
 - Small business requirements
 - Incumbent information
 - Evaluation factors]

[EAGLE generates full Acquisition Package Report]
- Shows all 5 sections with detailed analysis
- Cites FAR 15 for negotiated contracts

[User clicks "Download Documents"]
- Downloads 6 Word documents
```

### 7.2 Demo Environment Checklist
| Item | Status |
|------|--------|
| EAGLE accessible via PIV | [ ] |
| Test data cleared from previous sessions | [ ] |
| S3 bucket populated with KB content | [ ] |
| Templates uploaded and tested | [ ] |
| Network stable for live demo | [ ] |
| Backup screenshots if demo fails | [ ] |

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Obtain environment access
- [ ] Verify EAGLE agent configuration
- [ ] Audit S3 knowledge base
- [ ] Confirm architecture with Ryan

### Week 2: Core Development
- [ ] Implement structured report template
- [ ] Add threshold detection
- [ ] Create question flow

### Week 3: Document Generation
- [ ] Implement Word export (critical path)
- [ ] Create document templates
- [ ] Test placeholder replacement

### Week 4: Integration & Polish
- [ ] End-to-end testing
- [ ] Fix bugs
- [ ] Prepare demo environment

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| S3 bucket empty/inaccessible | High | Verify access in Phase 1 |
| Word export complexity | High | Prototype early, use mammoth.js pattern |
| FAR citations inaccurate | High | Validate against KB, never hallucinate |
| Scope creep to services | Medium | Confirm products-only scope |
| Multi-agent complexity | Medium | Use structured report (Option C) |
| PIV access delayed | High | Escalate to IT early |

---

## Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                     BLOCKED ON                              │
├─────────────────────────────────────────────────────────────┤
│ OA Team:                                                    │
│ - FAR/HHSAR documents                                       │
│ - NIH policy documents                                      │
│ - Document templates (SOW, IGCE, AP)                        │
│ - Product database access                                   │
│                                                             │
│ Ryan/Team:                                                  │
│ - Architecture confirmation (Option C)                      │
│ - Essential specialist sections                             │
│ - Scope confirmation (products only)                        │
│                                                             │
│ IT/Security:                                                │
│ - PIV access                                                │
│ - Dev environment access                                    │
│ - S3 bucket permissions                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

The POC is successful when:

1. **Functional:** User can complete simple and complex acquisition workflows end-to-end
2. **Accurate:** All FAR citations are valid (no hallucinations)
3. **Deliverable:** User can download Word documents for all generated content
4. **Usable:** Workflow completes in <5 minutes for simple, <10 minutes for complex
5. **Demonstrable:** Live demo to stakeholders without critical failures

---

*Document created: January 2026*
*Owner: Development Team*
*Status: Draft - Pending Architecture Confirmation*
