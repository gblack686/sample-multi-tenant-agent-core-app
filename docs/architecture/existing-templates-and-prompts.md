# Existing Templates and System Prompts Reference

This document catalogs all existing templates, system prompts, and agent configurations in the codebase that could potentially be used or adapted for EAGLE.

---

## System Prompts

### 1. Ada (Main Chat Agent) - `client/pages/tools/chat/config.js`

**Location:** `client/pages/tools/chat/config.js:177-363`

**Purpose:** Primary chat agent for Research Optimizer (Ada)

**Key Characteristics:**
- Colleague-like personality (not service bot)
- NCI-focused context
- Tool-equipped (search, browse, code, editor, think, data)
- Memory management via workspace.txt
- Academic citation requirements
- Critical evaluation stance

**Relevant for EAGLE:**
- Tool definitions pattern (search, browse, code, think, data)
- Memory/context injection pattern: `${context.main}`
- Professional tone guidelines
- Accuracy requirements for health/law/research

**Code Reference:**
```javascript
export function systemPrompt(context) {
  return `The assistant is Ada, created by Anthropic for the National Cancer Institute...

  <memory>
  ${context.main}
  </memory>
  ...
```

---

### 2. Bedrock Template Agent - `client/templates/bedrock.js`

**Location:** `client/templates/bedrock.js:48-56`

**Purpose:** Default agent for Bedrock template (minimal)

**System Prompt:**
```
"You are honest. When you are uncertain about something, or if your tools
aren't working right, you let the user know. You write in brief, artistic
prose, without any *markdown*, lists, bullet points, emojis or em-dashes (—)."
```

**Tools:** `["code", "think"]`

**Relevant for EAGLE:**
- Minimal agent pattern
- Tool configuration via array
- IndexedDB storage pattern for agents/threads/messages

---

### 3. Chat-v2 Agent System - `client/pages/tools/chat-v2/hooks.js`

**Location:** `client/pages/tools/chat-v2/hooks.js:286-420`

**Purpose:** Multi-agent chat system with dynamic agent loading

**Key Features:**
- Agents loaded by `agentId` from URL parameter
- System prompts stored per-agent in PostgreSQL (via ServerAdapter)
- Fallback to IndexedDB for offline/development
- Dynamic tool loading per agent

**Database Schema (Server-side):**
```javascript
{
  agents: { id, userId, promptId, name, tools },
  prompts: { id, name, version, content },
  threads: { agentId, name },
  messages: { agentId, threadId, role, content }
}
```

**Relevant for EAGLE:**
- Pattern for multiple specialized agents
- Agent-specific system prompts
- Thread/conversation isolation per agent

---

### 4. EAGLE System Prompt - `server/services/schema.js` ⭐ **ALREADY EXISTS**

**Location:** `server/services/schema.js:607-707`

**Purpose:** Federal acquisition specialist agent for NCI Office of Acquisitions

**Agent Configuration (Seed Data):**
| Field | Value |
|-------|-------|
| Agent ID | 3 |
| Name | EAGLE |
| Prompt ID | 3 (eagle-system-prompt) |
| Tools | `["search", "browse", "code", "editor", "think", "data"]` |

**Full Name:** Expert Acquisition Guidance and Learning Environment

**Knowledge Base Structure (S3 bucket: `rh-eagle`):**
| Folder | Purpose |
|--------|---------|
| `compliance-strategist/` | FAR guidance, HHSAR, NIH policies, PMR checklists |
| `financial-advisor/` | Appropriations law, cost analysis, IGCE guidance |
| `legal-counselor/` | GAO decisions, case law, protest guidance, IP/data rights |
| `market-intelligence/` | Market research guides, small business programs, contract vehicles |
| `public-interest-guardian/` | Ethics guidance, transparency requirements |
| `supervisor-core/` | Checklists, core procedures, essential templates |
| `technical-translator/` | SOW/PWS examples, agile contracting |
| `shared/` | Cross-cutting reference documents |

**Dual-Format Approach:**
- **TXT files** - For answering questions (optimized for retrieval)
- **DOCX/XLSX/PDF files** - For document generation (official templates)

**Key Prompt Sections:**
- Mission: Support NIH/NCI acquisition professionals
- Tools: data, code, search, browse, editor, think
- Workflow: Query KB → Cite FAR/HHSAR → Generate documents
- Personality: Knowledgeable colleague (no service language)
- Accuracy: Never fabricate FAR citations

**System Prompt Snippet:**
```javascript
const eagleSystemPrompt = `The assistant is EAGLE (Expert Acquisition Guidance
and Learning Environment), created by Anthropic for the National Cancer Institute.
EAGLE is a federal acquisition specialist that helps contracting professionals
navigate FAR/HHSAR regulations, NIH policies, and acquisition procedures.
...
EAGLE NEVER fabricates FAR citations, policy references, or regulatory requirements.
If uncertain, EAGLE states limitations and recommends verification with the
Contracting Officer or OGC.
...`;
```

**URL:** `https://researchoptimizer-dev.cancer.gov/tools/chat-v2?agentId=3`

---

### 5. FedPulse System Prompt - `server/services/schema.js`

**Location:** `server/services/schema.js:525-605` (approximate)

**Agent Configuration:**
| Field | Value |
|-------|-------|
| Agent ID | 2 |
| Name | FedPulse |
| Prompt ID | 2 (fedpulse-system-prompt) |
| Tools | `["search", "browse", "code", "editor", "think"]` |

**Purpose:** Federal executive order and regulatory monitoring

---

## Document Templates

### 6. Lay Person Abstract Template

**Location:** `client/templates/lay-person-abstract/`

**Files:**
| File | Purpose |
|------|---------|
| `lay-person-abstract-template.docx` | Word template with placeholders |
| `lay-person-abstract-template.txt` | Text version showing placeholder syntax |
| `adult-affected-patient.txt` | System prompt for patient abstracts |
| `adult-family-member.txt` | System prompt for family member abstracts |
| `adult-healthy-volunteer.txt` | System prompt for healthy volunteer abstracts |

**Template Syntax:**
```
Project Title: {{study_title}} ({{nct_number}})
Principal Investigators: {{investigator_names}}
...
{{FOR item IN who_can_participate}}
- {{$item}}
{{END-FOR item}}
```

**Relevant for EAGLE:**
- Word document template pattern
- Placeholder syntax (`{{variable}}`, `{{FOR}}...{{END-FOR}}`)
- Could adapt for SOW, IGCE, AP templates

---

### 7. NIH Clinical Center Consent Templates

**Location:** `client/templates/nih-cc/`

**Files:**
| File | Purpose | Size |
|------|---------|------|
| `nih-cc-consent-template-2024-04-15.docx` | Master consent form template | 67KB |
| `nih-cc-consent-template-2024-04-15.txt` | Text extraction | 17KB |
| `adult-affected-patient.txt` | Consent generation prompt | 132KB |
| `adult-family-member.txt` | Family consent prompt | 134KB |
| `adult-healthy-volunteer.txt` | Volunteer consent prompt | 132KB |
| `language-reqs.txt` | Language requirements | 27KB |

**Relevant for EAGLE:**
- Large system prompts (~130KB) for complex document generation
- Template + prompt pattern for different document types
- Compliance-focused language requirements

---

### 8. Consent Crafter Configuration

**Location:** `client/pages/tools/consent-crafter/config.js`

**Purpose:** Template management system for consent forms

**Pattern:**
```javascript
export const templateConfigs = {
  "nih-cc-adult-patient": {
    label: "Adult affected patient",
    category: "NIH Clinical Center Consent (NIH CCC)",
    templateUrl: "/templates/nih-cc/nih-cc-consent-template-2024-04-15.docx",
    promptUrl: "/templates/nih-cc/adult-affected-patient.txt",
    filename: "nih-cc-consent-adult-affected.docx",
    disabled: false,
  },
  // ... more templates
};
```

**Relevant for EAGLE:**
- Template configuration pattern (category, templateUrl, promptUrl, filename)
- Could adapt for acquisition document types (SOW, IGCE, AP, etc.)
- Grouped templates by category

---

### 9. GovInfo API Template

**Location:** `client/templates/govinfo-api.md`

**Purpose:** Instructions for accessing federal government documents

**Size:** 6.5KB

**Relevant for EAGLE:**
- Federal document API access patterns
- Could be useful for FAR/HHSAR lookups

---

### 10. Privacy Notice Template

**Location:** `client/templates/privacy-notice.md`

**Purpose:** Privacy notice content

**Size:** 4.3KB

---

## Database Models

### 11. Server-Side Agent/Prompt Models

**Location:** `server/services/schema.js:80-109`

**Agent Model:**
```javascript
Agent: {
  attributes: {
    userId: DataTypes.INTEGER,
    modelId: DataTypes.INTEGER,
    name: DataTypes.STRING,
    promptId: DataTypes.INTEGER,
    tools: DataTypes.JSON,
  }
}
```

**Prompt Model:**
```javascript
Prompt: {
  attributes: {
    name: DataTypes.STRING,
    version: DataTypes.INTEGER,
    content: DataTypes.TEXT,
  }
}
```

**Relevant for EAGLE:**
- Server-side prompt versioning
- Agent-to-prompt relationship
- Tools stored as JSON array

---

### 12. Client-Side Models

**Location:** `client/models/models.js`

**Project Model:**
```javascript
this.context = {
  systemPrompt: "",
  files: [], // Resource IDs
  customText: "",
};

this.apiConfig = {
  baseUrl: "/api/model",
  method: "POST",
  headers: {},
  variables: {},
};

this.mcpConfig = {
  enabled: false,
  endpoint: "",
  tools: [],
};
```

**Relevant for EAGLE:**
- Project-level context configuration
- MCP (Model Context Protocol) integration pattern
- Custom API endpoint configuration

---

## Tools Definitions

### 13. Chat Tools - `client/pages/tools/chat/config.js`

**Location:** `client/pages/tools/chat/config.js:1-175`

| Tool | Purpose | Relevant for EAGLE |
|------|---------|-------------------|
| `search` | Web search with current year | Product/vendor search |
| `browse` | Extract content from URLs | Document analysis |
| `code` | Execute JavaScript/HTML | Calculations, formatting |
| `editor` | View/edit memory files | Document editing |
| `think` | Complex reasoning space | Multi-step analysis |
| `data` | Access S3 bucket files | Knowledge base access |

**Tool Spec Pattern:**
```javascript
{
  toolSpec: {
    name: "data",
    description: "Access data files from S3 buckets...",
    inputSchema: {
      json: {
        type: "object",
        properties: {
          bucket: { type: "string", description: "..." },
          key: { type: "string", description: "..." },
        },
        required: ["bucket"],
      },
    },
  },
}
```

---

## FedPulse Configuration

### 14. FedPulse Context

**Location:** `client/pages/tools/chat/fedpulse.config.js`

**Purpose:** Federal executive order context loading

**Pattern:**
```javascript
export const currentExecutiveOrders = jsonToXml(
  JSON.parse(await browse({
    url: "https://www.federalregister.gov/api/v1/documents.json?..."
  }))
);
const instructions = await fetch("/templates/govinfo-api.md").then(res => res.text());
export const context = { currentExecutiveOrders, instructions };
```

**Relevant for EAGLE:**
- Dynamic context loading from external APIs
- Could adapt for FAR updates, threshold changes

---

## Summary: What's Reusable for EAGLE

### Patterns to Adopt

| Pattern | Source | EAGLE Use |
|---------|--------|-----------|
| Template + Prompt pairing | Consent Crafter | SOW, IGCE, AP templates |
| Tool definitions | chat/config.js | KB query, doc gen, threshold calc |
| Agent-specific system prompts | chat-v2/hooks.js | OA Contracting Agent |
| Placeholder syntax | lay-person-abstract | Document generation |
| Version-controlled prompts | server/schema.js | Regulatory updates |
| Context injection | Ada prompt | FAR/HHSAR context |
| S3 data access tool | config.js `data` tool | Knowledge base access |

### Templates to Adapt

| Existing | Adapt For |
|----------|-----------|
| `lay-person-abstract-template.docx` | SOW template |
| `nih-cc-consent-template.docx` | Acquisition Plan template |
| Consent Crafter config pattern | Document type selector |

### System Prompt Sections to Reference

| Section | Location | Why |
|---------|----------|-----|
| Tool usage instructions | Ada prompt lines 189-203 | How to describe tool use |
| Accuracy requirements | Ada prompt lines 270-276 | Critical for FAR compliance |
| Response patterns | Ada prompt lines 243-268 | Professional tone |
| Memory management | Ada prompt lines 344-349 | Context persistence |

---

## Next Steps for EAGLE

**Note:** EAGLE agent (agentId=3) already exists in `server/services/schema.js` with a comprehensive system prompt and knowledge base structure. The following are enhancements to the existing implementation.

### Already Implemented ✅

1. **EAGLE Agent Configuration** (`server/services/schema.js:755-761`)
   - Agent ID: 3
   - System prompt: 100+ lines covering FAR/HHSAR guidance
   - Tools: search, browse, code, editor, think, data
   - S3 knowledge base: `rh-eagle` bucket

2. **Knowledge Base Structure** (S3 bucket `rh-eagle`)
   - 8 specialist folders matching multi-agent design
   - Dual-format approach (TXT for retrieval, DOCX/XLSX for generation)

### Needs Implementation 🔲

1. **Word Document Export:**
   - Current: Text/HTML output only
   - Needed: Generate downloadable DOCX files
   - Pattern: Use Consent Crafter's mammoth.js approach

2. **Document Templates:**
   - Create SOW template (adapt lay-person-abstract pattern)
   - Create IGCE template
   - Create Acquisition Plan template
   - Use `{{placeholder}}` syntax

3. **Additional Tools (Optional):**
   - `threshold_check` - Acquisition threshold validation
   - `product_search` - Search approved products database

4. **Verify S3 Knowledge Base Content:**
   - Confirm `rh-eagle` bucket exists and is populated
   - Validate folder structure matches prompt expectations
   - Check TXT/DOCX file availability

---

*Document created: January 2026*
*Last updated: January 2026*
*Purpose: Reference for EAGLE development team*
