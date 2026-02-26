# EAGLE Feature Requirements Document

**Date:** January 2026
**Type:** Technical Requirements & Feature Specification
**Document:** EAGLE (Enhanced Acquisition Guidance Learning Engine)

## Executive Summary

EAGLE is an AI-powered acquisition assistance tool designed to automate and streamline the Acquisition Planning (AP) process at NCI. The system uses a multi-agent architecture with 6 specialist agents coordinated by a supervisor agent to guide CORs through complex procurement workflows and generate compliant acquisition documentation.

### Objectives

1. **MVP (Objective 1)**: Build initial requirements for EAGLE application enabling CORs to generate acquisition plans and submit to OA Intake
2. **Agentic Workflow (Objective 2)**: Design an autonomous AI workflow that automates the entire AP process until completion

## Technical Architecture

### Current Infrastructure

| Component | Technology |
|-----------|------------|
| UI Framework | SolidJS |
| Backend | NodeJS REST API (Docker containerized) |
| Hosting | NCI CloudOne (AWS) |
| Infrastructure | AWS CDK |
| AI Model | AWS Bedrock - Claude |
| Database | RDS PostgreSQL with pgvector |
| Storage | S3 (6 folders for agent roles + knowledge bases) |

### AWS Services Used
- API Gateway
- Elastic Container Registry
- Elastic Container Service
- Simple Storage Service (S3)
- RDS PostgreSQL with pgvector extension
- AWS Bedrock

### Key URLs
- **GitHub**: https://github.com/CBIIT/nci-webtools-ctri-arti
- **Site**: https://researchoptimizer-dev.cancer.gov

## Multi-Agent Architecture

### Agent Roles (6 Specialists + 1 Supervisor)
1. **Compliance Agent** - FAR/HHSAR/NIH policy compliance
2. **Legal Agent** - Legal review and risk assessment
3. **Financial Agent** - Cost estimation and IGCE validation
4. **Market Agent** - Market research and commercial analysis
5. **Technical Agent** - Technical requirements review
6. **Public Interest Agent** - Small business and public interest considerations
7. **Supervisor Agent** - Orchestrates activities and manages handoffs

### Cost Consideration
- Multi-agent collaboration costs 10x tokens vs single agent
- Strategic invocation system needed to manage costs

## Feature Categories (25 Total)

### Core System Architecture (Features 1-3)
| # | Feature | Description |
|---|---------|-------------|
| 1 | Multi-Agent AI Framework | Supervisor + 6 specialists with context sharing |
| 2 | Knowledge Base Integration | S3-based vector database, 8 specialized knowledge bases |
| 3 | Authentication & Access Control | PIV card auth, role-based access (COR/CO vs Policy Group) |

### User Interface & Experience (Features 4-6)
| # | Feature | Description |
|---|---------|-------------|
| 4 | Adaptive Questioning Engine | Progressive discovery, context-aware questions, validation |
| 5 | Document Generation System | 25+ document types, template hierarchy, multi-document generation |
| 6 | Template Management | Version control, compliance validation, update notifications |

### Intelligent Analysis (Features 7-10)
| # | Feature | Description |
|---|---------|-------------|
| 7 | Cross-Document Consistency | Automated inconsistency detection, bidirectional updates |
| 8 | Existing Vehicle Detection | Search NIH contracts, ceiling checking, recommendations |
| 9 | Commercial-First Analysis | EO 14275 compliance, commercial solution identification |
| 10 | Cost Estimation Coaching | Industry benchmarks, labor mix analysis, IGCE generation |

### Regulatory Compliance (Features 11-13)
| # | Feature | Description |
|---|---------|-------------|
| 11 | Regulatory Intelligence | Real-time FAR compliance, threshold monitoring, auto D&F detection |
| 12 | Timeline Validation | Complexity assessment, milestone generation, FY deadline warnings |
| 13 | Regulatory Boundary Management | Problem detection, CO escalation paths, GAO protest risk |

### Integration & Data Management (Features 14-16)
| # | Feature | Description |
|---|---------|-------------|
| 14 | NIH System Integrations | NVision, Teams, SharePoint, ServiceNow, Active Directory |
| 15 | Data Intelligence Layer | Historical contract data, vendor database, past acquisition analysis |
| 16 | Document Import/Analysis | Parse existing documents, extract mission impact, analyze quotes |

### Workflow & Collaboration (Features 17-19)
| # | Feature | Description |
|---|---------|-------------|
| 17 | Acquisition Package Assembly | Checklist generation, HHS Board prep, PAA package assembly |
| 18 | User Guidance System | Context-sensitive help, educational content, decision frameworks |
| 19 | Quality Control Features | Pre/post generation validation, CO feedback loop |

### Advanced Features (Features 20-22)
| # | Feature | Description |
|---|---------|-------------|
| 20 | Performance Standards & Monitoring | Adoption metrics, response time, success rates |
| 21 | Change Management | Regulatory update notifications, template cascade updates |
| 22 | Crisis Acquisition Support | Accelerated workflows, bridge contracts, alternative vehicles |

### Technical Infrastructure (Features 23-25)
| # | Feature | Description |
|---|---------|-------------|
| 23 | AWS Bedrock Configuration | Claude 4 Opus/Sonnet, extended thinking, token optimization |
| 24 | Security & Compliance | FedRAMP, FIPS 199 MODERATE, CUI handling, audit logging |
| 25 | Scalability Requirements | 600+ CORs, 200+ COs, concurrent sessions, response time SLAs |

## Document Types Supported (25+)

- Statement of Work (SOW)
- Acquisition Plan (AP)
- Independent Government Cost Estimate (IGCE)
- Request for Quotation (RFQ)
- Request for Proposal (RFP)
- Determination & Findings (D&F)
- Justification for Other than Full and Open Competition (JOFOC)
- Market Research Reports
- Source Selection Plans
- And more...

## Implementation Phases

| Phase | Timeline | Features |
|-------|----------|----------|
| **MVP** | 6 months | Features 1-6, 11, 17 (core architecture, basic Q&A, document generation, regulatory compliance) |
| **Advanced** | 12 months | Features 7-10, 14-16 (consistency engine, vehicle detection, system integrations) |
| **Full** | 18 months | Features 18-25 (AI learning, performance optimization, full collaboration) |

## Action Items

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 1 | Confirm Objective 1 & 2 scope | Ryan Hash | Immediate |
| 2 | Design strategic agent invocation to minimize costs | Dev Team | High |
| 3 | Implement S3-based knowledge base system | Dev Team | High |
| 4 | Set up PIV card authentication | Dev Team | High |
| 5 | Build adaptive questioning engine | Dev Team | High |
| 6 | Implement 25+ document type templates | Dev Team | Medium |
| 7 | Integrate with OA Intake API | Dev Team | MVP |
| 8 | Future: Integrate with Merlin and other systems | Dev Team | Future |

## Key Decisions

1. **Knowledge Base**: AWS S3-based vector database (not OpenSearch)
2. **Authentication**: PIV card only (federal employees)
3. **Two-tier Access**: COR/CO interface vs Policy Group interface
4. **Template Hierarchy**: Agency-specific -> HHS -> NIH -> generic FAR-compliant
5. **Cost Management**: Strategic invocation to manage 10x multi-agent token costs

## Pain Points to Address

1. Minimize inference calls and token length to reduce costs
2. Design for scale (600+ CORs, 200+ COs)
3. Handle FAR 2.0 regulatory updates
4. Ensure FedRAMP and FIPS 199 MODERATE compliance

## API Integration

```
POST https://researchoptimizer-dev.cancer.gov/api/model
```

Payload structure:
```json
{
  "model": "us.meta.llama4-maverick-17b-instruct-v1:0",
  "messages": [
    {
      "role": "user",
      "content": [{"text": "..."}]
    }
  ],
  "system": "..."
}
```

---

*Source: EAGLE (Enhanced Acquisition Guidanc.txt*
*Summarized by: Claude Code*
