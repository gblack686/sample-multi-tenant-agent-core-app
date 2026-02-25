# RH Eagle Metadata Schema

## Overview
This schema defines the metadata structure for the 256 documents in the RH Eagle multi-agent system. The metadata enables intelligent document discovery and routing without requiring vector embeddings.

## Core Metadata Fields

### Document Identification
- **document_id** (string, required) - Unique identifier for the document
- **file_name** (string, required) - Original filename
- **file_path** (string, required) - S3 key path relative to bucket root
- **s3_bucket** (string, required) - S3 bucket name (rh-eagle-files)
- **document_type** (string, required) - Document classification
  - Values: "regulation", "guidance", "policy", "template", "memo", "checklist", "reference"
- **source_agency** (string, optional) - Originating agency
  - Examples: "FAR", "GSA", "OMB", "DOD", "GAO", "Agency-specific"

### Temporal Information
- **effective_date** (string, ISO 8601 format, optional) - When the document became/becomes effective
  - Format: "YYYY-MM-DD"
- **last_updated** (string, ISO 8601 format, optional) - Last revision date
  - Format: "YYYY-MM-DD"
- **expiration_date** (string, ISO 8601 format, nullable) - When document expires (if applicable)
  - Format: "YYYY-MM-DD"
- **fiscal_year** (number, optional) - Relevant fiscal year if applicable
  - Format: YYYY

### Content Summaries
- **summary** (string, optional) - High-level document summary (2-3 sentences)
  - Max recommended length: 500 characters
- **key_requirements** (array of strings, optional) - Main requirements or obligations
  - Max recommended: 5 items
- **section_summaries** (object, optional) - Section-by-section breakdown
  - Structure: `{"section_name": "summary text"}`

### Topic Classification
- **primary_topic** (string, required) - Main subject area
- **related_topics** (array of strings, optional) - Secondary topics

#### Standard Topic Taxonomy
- `funding` - Appropriations, obligations, fiscal law
- `acquisition_packages` - Solicitations, proposals, awards
- `contract_types` - FFP, CPFF, T&M, IDIQ, BPA
- `compliance` - Regulatory requirements, audits
- `legal` - Disputes, claims, protests, unauthorized commitments
- `market_research` - Industry analysis, pricing, competition
- `socioeconomic` - Small business, set-asides, HUBZone, SDVOSB
- `labor` - Service Contract Act, wage determinations
- `intellectual_property` - Data rights, patents, technical data
- `termination` - Convenience, default, settlement
- `modifications` - Contract changes, scope changes
- `closeout` - Final payments, records retention
- `performance` - Quality assurance, inspections
- `subcontracting` - Subcontractor management, flow-downs

### Agent Relevance
- **primary_agent** (string, required) - Which agent owns/manages this content
- **relevant_agents** (array of strings, optional) - Other agents that should reference this

#### Agent List
- `supervisor-core`
- `financial-advisor`
- `legal-counselor`
- `compliance-strategist`
- `market-intelligence`
- `technical-translator`
- `public-interest-guardian`
- `agents` (general/shared)

### Regulatory Context
- **far_references** (array of strings, optional) - FAR citations
  - Format: "FAR X.XXX" or "FAR XX.XXX-X"
  - Examples: ["FAR 16.505", "FAR 52.216-18"]
- **statute_references** (array of strings, optional) - Legal statute citations
  - Format: "XX USC XXXX"
  - Examples: ["31 USC 1341", "41 USC 3304"]
- **agency_references** (array of strings, optional) - Agency-specific regulations
  - Examples: ["DFARS 232.7", "GSAM 538.273"]
- **authority_level** (string, required) - Hierarchical authority
  - Values: "statute", "regulation", "policy", "guidance", "internal"

### Search & Retrieval Hints
- **keywords** (array of strings, required) - Important terms for discovery
  - Recommended: 5-15 keywords
  - Include acronyms, common terms, technical terms
- **complexity_level** (string, required) - Content difficulty
  - Values: "basic", "intermediate", "advanced"
- **audience** (array of strings, optional) - Intended readers
  - Examples: "contracting_officer", "legal_counsel", "program_manager", "financial_advisor", "supervisor"

### File Metadata
- **file_size_bytes** (number, optional) - File size in bytes
- **file_size_kb** (number, optional) - File size in kilobytes (rounded)
- **page_count** (number, optional) - Number of pages (for PDFs)
- **word_count** (number, optional) - Approximate word count

### Catalog Metadata
- **catalog_version** (string) - Schema version
- **added_to_catalog** (string, ISO 8601 format) - When added to catalog
- **last_validated** (string, ISO 8601 format) - Last time metadata was verified

## Example Metadata Entries

### Example 1: FAR Guidance Document
```json
{
  "document_id": "far-idiq-funding-001",
  "file_name": "appropriations_law_IDIQ_funding.txt",
  "file_path": "financial-advisor/appropriations-law/appropriations_law_IDIQ_funding.txt",
  "s3_bucket": "rh-eagle-files",
  "document_type": "guidance",
  "source_agency": "GAO",
  
  "effective_date": "2020-01-15",
  "last_updated": "2023-06-30",
  "expiration_date": null,
  "fiscal_year": null,
  
  "summary": "Explains appropriations law requirements for IDIQ contract funding, including bona fide needs rule and incremental funding restrictions. Covers base contract vs task order funding obligations.",
  "key_requirements": [
    "IDIQ base contract requires minimal funding at award",
    "Task orders must be fully funded at time of issuance",
    "Bona fide needs rule applies to task order funding",
    "Incremental funding prohibited for task orders except S&E"
  ],
  
  "primary_topic": "funding",
  "related_topics": ["contract_types", "compliance", "legal"],
  
  "primary_agent": "financial-advisor",
  "relevant_agents": ["legal-counselor", "compliance-strategist"],
  
  "far_references": ["FAR 16.504", "FAR 32.703", "FAR 16.505"],
  "statute_references": ["31 USC 1502", "31 USC 1341"],
  "agency_references": [],
  "authority_level": "guidance",
  
  "keywords": ["IDIQ", "indefinite delivery", "funding", "appropriations", "task order", "bona fide needs", "incremental funding"],
  "complexity_level": "advanced",
  "audience": ["contracting_officer", "legal_counsel", "financial_advisor"],
  
  "file_size_bytes": 45231,
  "file_size_kb": 45,
  "word_count": 3200,
  
  "catalog_version": "1.0",
  "added_to_catalog": "2026-02-20",
  "last_validated": "2026-02-20"
}
```

### Example 2: Contract Template
```json
{
  "document_id": "template-uc-ratification-001",
  "file_name": "Unauthorized Commitments Ratification Template.pdf",
  "file_path": "supervisor-core/checklists/Unauthorized Commitments Ratification Template.pdf",
  "s3_bucket": "rh-eagle-files",
  "document_type": "template",
  "source_agency": "Agency-specific",
  
  "effective_date": "2022-03-01",
  "last_updated": "2024-11-15",
  "expiration_date": null,
  "fiscal_year": null,
  
  "summary": "Standard template for ratifying unauthorized commitments made without proper contracting authority. Includes documentation requirements and approval workflow.",
  "key_requirements": [
    "Document circumstances of unauthorized commitment",
    "Obtain legal review and opinion",
    "Secure warranted contracting officer approval",
    "Verify funding availability and appropriateness"
  ],
  
  "primary_topic": "legal",
  "related_topics": ["compliance", "funding"],
  
  "primary_agent": "supervisor-core",
  "relevant_agents": ["legal-counselor", "compliance-strategist", "financial-advisor"],
  
  "far_references": ["FAR 1.602-3"],
  "statute_references": ["31 USC 1341"],
  "agency_references": [],
  "authority_level": "internal",
  
  "keywords": ["unauthorized commitment", "ratification", "antideficiency", "warrant", "authority", "UC"],
  "complexity_level": "intermediate",
  "audience": ["contracting_officer", "supervisor", "legal_counsel"],
  
  "file_size_bytes": 5850856,
  "file_size_kb": 5713,
  "page_count": 8,
  
  "catalog_version": "1.0",
  "added_to_catalog": "2026-02-20",
  "last_validated": "2026-02-20"
}
```

### Example 3: Market Intelligence
```json
{
  "document_id": "market-cat-mgmt-framework-001",
  "file_name": "Category_Management_Framework.txt",
  "file_path": "market-intelligence/vehicle-information/Category_Management_Framework.txt",
  "s3_bucket": "rh-eagle-files",
  "document_type": "guidance",
  "source_agency": "OMB",
  
  "effective_date": "2019-05-01",
  "last_updated": "2023-09-20",
  "expiration_date": null,
  "fiscal_year": null,
  
  "summary": "OMB framework for implementing category management strategies to improve government buying power and reduce duplication. Emphasizes use of Best-in-Class vehicles.",
  "key_requirements": [
    "Use Best-in-Class vehicles where applicable",
    "Conduct spend analysis across government",
    "Consolidate requirements across agencies",
    "Report category management metrics"
  ],
  
  "primary_topic": "market_research",
  "related_topics": ["acquisition_packages", "compliance"],
  
  "primary_agent": "market-intelligence",
  "relevant_agents": ["compliance-strategist", "financial-advisor"],
  
  "far_references": ["FAR 10.001"],
  "statute_references": [],
  "agency_references": [],
  "authority_level": "policy",
  
  "keywords": ["category management", "BIC", "best in class", "strategic sourcing", "spend analysis", "OMB"],
  "complexity_level": "intermediate",
  "audience": ["contracting_officer", "program_manager", "market_analyst"],
  
  "file_size_bytes": 38421,
  "file_size_kb": 38,
  "word_count": 2800,
  
  "catalog_version": "1.0",
  "added_to_catalog": "2026-02-20",
  "last_validated": "2026-02-20"
}
```

## Catalog File Structure

The metadata catalog is stored as a single JSON file: `metadata-catalog.json`

```json
{
  "catalog_metadata": {
    "version": "1.0",
    "created": "2026-02-20T18:30:00Z",
    "last_updated": "2026-02-20T18:30:00Z",
    "total_documents": 256,
    "schema_version": "1.0"
  },
  "statistics": {
    "by_topic": {
      "funding": 45,
      "acquisition_packages": 67,
      "legal": 38,
      "compliance": 52,
      "market_research": 28,
      "contract_types": 26
    },
    "by_agent": {
      "financial-advisor": 52,
      "legal-counselor": 48,
      "compliance-strategist": 55,
      "market-intelligence": 35,
      "supervisor-core": 40,
      "technical-translator": 15,
      "public-interest-guardian": 11
    },
    "by_document_type": {
      "guidance": 120,
      "regulation": 45,
      "template": 30,
      "policy": 35,
      "memo": 15,
      "reference": 11
    }
  },
  "documents": [
    {
      // Document metadata as defined above
    }
    // ... 255 more documents
  ]
}
```

## Validation Rules

### Required Fields
- document_id
- file_name
- file_path
- s3_bucket
- document_type
- primary_topic
- primary_agent
- authority_level
- keywords (at least 3)
- complexity_level

### Recommended Fields
- summary
- key_requirements
- related_topics
- relevant_agents
- far_references OR statute_references
- audience

### Format Validation
- Dates must be ISO 8601 format (YYYY-MM-DD)
- FAR references must match pattern: "FAR \\d+\\.\\d+"
- USC references must match pattern: "\\d+ USC \\d+"
- document_id must be unique across catalog
- file_path must be valid S3 key

## Usage Notes

1. **Maintenance**: Update catalog when documents are added/removed/modified
2. **Size**: At 256 documents, catalog should be ~200-300KB
3. **Performance**: Small enough to load entirely into agent context
4. **Versioning**: Increment catalog_version on schema changes
5. **Validation**: Run validation script after manual edits
