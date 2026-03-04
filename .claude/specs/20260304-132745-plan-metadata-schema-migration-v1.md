# Plan: Metadata Schema Migration & Knowledge Base Integration

**ID**: 20260304-132745-plan-metadata-schema-migration-v1
**Created**: 2026-03-04
**Status**: Draft
**Owner**: TBD

---

## Executive Summary

Migrate the 195 knowledge base documents from `rh-eagle-files` S3 bucket to `eagle-documents-*` and update the metadata extraction Lambda to capture the full schema defined in `metadata-schema.md`. This enables intelligent document discovery and agent routing without vector embeddings.

---

## Current State

| Component | Status | Location |
|-----------|--------|----------|
| Knowledge base documents | 195 files | `s3://rh-eagle-files/` |
| Document bucket (CDK) | Empty | `s3://eagle-documents-695681773636-dev/` |
| Metadata table | Empty (0 items) | `eagle-document-metadata-dev` |
| Lambda extractor | Partial schema | `infrastructure/cdk-eagle/lambda/metadata-extraction/` |
| Full schema spec | Documented | `/Users/hoquemi/Downloads/metadata-schema.md` |

### Schema Gap Analysis

The Lambda currently extracts 13 fields. The full schema defines 28+ fields.

**Missing fields (15)**:
- `effective_date`, `expiration_date`, `fiscal_year` (temporal)
- `key_requirements`, `section_summaries` (content)
- `related_topics`, `relevant_agents` (routing)
- `statute_references`, `agency_references`, `authority_level` (regulatory)
- `complexity_level`, `audience` (discovery)
- `word_count`, `page_count`, `file_size_kb` (file metadata)
- `catalog_version`, `added_to_catalog`, `last_validated` (catalog)

---

## Target State

1. **Lambda extracts full schema** — all 28 fields from `metadata-schema.md`
2. **DynamoDB populated** — 195+ documents with complete metadata
3. **Agents can query** — by topic, agent, authority level, complexity
4. **Catalog synced** — `metadata-catalog.json` in S3 for bulk reads

---

## Implementation Plan

### Phase 1: Update Lambda Schema (Day 1)

#### Task 1.1: Update `models.py`

Add missing fields to `DocumentMetadata` dataclass:

```python
# New fields to add
effective_date: str = ""           # ISO 8601
expiration_date: str = ""          # ISO 8601 or null
fiscal_year: int = 0               # YYYY
key_requirements: List[str] = field(default_factory=list)
section_summaries: dict = field(default_factory=dict)
related_topics: List[str] = field(default_factory=list)
relevant_agents: List[str] = field(default_factory=list)
statute_references: List[str] = field(default_factory=list)
agency_references: List[str] = field(default_factory=list)
authority_level: str = "guidance"  # statute|regulation|policy|guidance|internal
complexity_level: str = "intermediate"  # basic|intermediate|advanced
audience: List[str] = field(default_factory=list)
word_count: int = 0
page_count: int = 0
file_size_kb: int = 0
source_agency: str = ""
catalog_version: str = "1.0"
added_to_catalog: str = field(default_factory=_now_iso)
last_validated: str = field(default_factory=_now_iso)
```

**File**: `infrastructure/cdk-eagle/lambda/metadata-extraction/models.py`

#### Task 1.2: Update `extractor.py` Prompt

Modify the Bedrock prompt to extract all fields:

```python
EXTRACTION_PROMPT = """You are a federal acquisition document analyst. Extract metadata from this document.

## Document
Filename: {filename}
Content:
{content}

## Required Output (JSON)
Return a JSON object with these fields:
- title: Document title
- summary: 2-3 sentence summary (max 500 chars)
- document_type: regulation|guidance|policy|template|memo|checklist|reference
- source_agency: FAR|GSA|OMB|DOD|GAO|HHS|NIH|Agency-specific
- primary_topic: funding|acquisition_packages|contract_types|compliance|legal|market_research|socioeconomic|labor|intellectual_property|termination|modifications|closeout|performance|subcontracting
- related_topics: array of secondary topics
- primary_agent: supervisor-core|financial-advisor|legal-counselor|compliance-strategist|market-intelligence|technical-translator|public-interest-guardian
- relevant_agents: array of other agents that should reference this
- key_requirements: array of 3-5 main requirements (short bullets)
- far_references: array of FAR citations (e.g., "FAR 16.505")
- statute_references: array of USC citations (e.g., "31 USC 1341")
- agency_references: array of agency regs (e.g., "DFARS 232.7")
- authority_level: statute|regulation|policy|guidance|internal
- keywords: array of 5-15 search terms
- complexity_level: basic|intermediate|advanced
- audience: array of roles (contracting_officer|legal_counsel|program_manager|financial_advisor|supervisor)
- effective_date: ISO date or empty string
- expiration_date: ISO date or empty string
- fiscal_year: number or 0
- confidence_score: 0.0-1.0 confidence in extraction accuracy

Return ONLY valid JSON, no markdown fences."""
```

**File**: `infrastructure/cdk-eagle/lambda/metadata-extraction/extractor.py`

#### Task 1.3: Update `handler.py`

Add computed fields (word_count, page_count, file_size_kb):

```python
# After text extraction
word_count = len(text.split()) if text else 0
page_count = text.count('\f') + 1 if text else 0  # form feed = page break
file_size_kb = round(size / 1024)

# Pass to metadata constructor
metadata = DocumentMetadata(
    # ... existing fields ...
    word_count=word_count,
    page_count=page_count,
    file_size_kb=file_size_kb,
    # ... new extracted fields ...
)
```

**File**: `infrastructure/cdk-eagle/lambda/metadata-extraction/handler.py`

#### Task 1.4: Add DynamoDB GSIs for New Fields

Update `storage-stack.ts` to add GSIs for queryable fields:

```typescript
// Add GSI for authority_level queries
this.metadataTable.addGlobalSecondaryIndex({
  indexName: 'authority_level-index',
  partitionKey: { name: 'authority_level', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'last_updated', type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.ALL,
});

// Add GSI for complexity_level queries
this.metadataTable.addGlobalSecondaryIndex({
  indexName: 'complexity_level-index',
  partitionKey: { name: 'complexity_level', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'last_updated', type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.ALL,
});
```

**File**: `infrastructure/cdk-eagle/lib/storage-stack.ts`

---

### Phase 2: Create Migration Script (Day 2)

#### Task 2.1: Write Migration Script

Create a script to copy documents from `rh-eagle-files` to `eagle-documents-*`:

```python
#!/usr/bin/env python3
"""Migrate knowledge base from rh-eagle-files to eagle-documents bucket."""

import boto3
import time

SOURCE_BUCKET = "rh-eagle-files"
DEST_BUCKET = "eagle-documents-695681773636-dev"
DEST_PREFIX = "eagle-knowledge-base/approved/"

s3 = boto3.client("s3")

def migrate_documents():
    """Copy all documents, preserving folder structure."""
    paginator = s3.get_paginator("list_objects_v2")

    copied = 0
    for page in paginator.paginate(Bucket=SOURCE_BUCKET):
        for obj in page.get("Contents", []):
            source_key = obj["Key"]
            dest_key = f"{DEST_PREFIX}{source_key}"

            print(f"Copying: {source_key} -> {dest_key}")
            s3.copy_object(
                CopySource={"Bucket": SOURCE_BUCKET, "Key": source_key},
                Bucket=DEST_BUCKET,
                Key=dest_key,
            )
            copied += 1

            # Rate limit to avoid Lambda throttling
            if copied % 10 == 0:
                time.sleep(1)

    print(f"Migrated {copied} documents")

if __name__ == "__main__":
    migrate_documents()
```

**File**: `scripts/migrate-knowledge-base.py`

#### Task 2.2: Write Backfill Script

For documents already in S3 (pre-Lambda), create a backfill trigger:

```python
#!/usr/bin/env python3
"""Trigger metadata extraction for existing documents."""

import boto3
import json

BUCKET = "eagle-documents-695681773636-dev"
PREFIX = "eagle-knowledge-base/approved/"
LAMBDA_NAME = "eagle-metadata-extractor-dev"

s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")

def trigger_extraction():
    """Invoke Lambda for each document to extract metadata."""
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size = obj["Size"]

            # Simulate S3 event
            event = {
                "Records": [{
                    "s3": {
                        "bucket": {"name": BUCKET},
                        "object": {"key": key, "size": size}
                    }
                }]
            }

            print(f"Processing: {key}")
            lambda_client.invoke(
                FunctionName=LAMBDA_NAME,
                InvocationType="Event",  # async
                Payload=json.dumps(event),
            )

if __name__ == "__main__":
    trigger_extraction()
```

**File**: `scripts/backfill-metadata.py`

---

### Phase 3: Add Knowledge Retrieval Tool (Day 3)

#### Task 3.1: Create DynamoDB Query Tool

Add a tool for agents to query the metadata table:

```python
def _exec_knowledge_search(params: dict, tenant_id: str, session_id: str = None) -> dict:
    """Search knowledge base metadata in DynamoDB."""
    table = _get_dynamodb().Table("eagle-document-metadata-dev")

    # Query parameters
    topic = params.get("topic")
    agent = params.get("agent")
    authority = params.get("authority_level")
    complexity = params.get("complexity")
    keywords = params.get("keywords", [])
    limit = params.get("limit", 10)

    # Build query based on available indexes
    if topic:
        response = table.query(
            IndexName="primary_topic-index",
            KeyConditionExpression="primary_topic = :topic",
            ExpressionAttributeValues={":topic": topic},
            Limit=limit,
        )
    elif agent:
        response = table.query(
            IndexName="primary_agent-index",
            KeyConditionExpression="primary_agent = :agent",
            ExpressionAttributeValues={":agent": agent},
            Limit=limit,
        )
    else:
        # Scan with filters (less efficient)
        response = table.scan(Limit=limit)

    # Return summaries for agent to evaluate
    results = []
    for item in response.get("Items", []):
        results.append({
            "document_id": item["document_id"],
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "key_requirements": item.get("key_requirements", []),
            "authority_level": item.get("authority_level", ""),
            "complexity_level": item.get("complexity_level", ""),
            "s3_key": item.get("s3_key", ""),
        })

    return {"results": results, "count": len(results)}
```

**File**: `server/app/agentic_service.py` (add to TOOL_REGISTRY)

#### Task 3.2: Add Tool Definition

```python
{
    "name": "knowledge_search",
    "description": (
        "Search the acquisition knowledge base for relevant documents. "
        "Returns summaries and metadata to help decide which documents to read in full. "
        "Query by topic, agent, authority level, or keywords."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Primary topic: funding, legal, compliance, market_research, etc.",
            },
            "agent": {
                "type": "string",
                "description": "Primary agent: legal-counselor, financial-advisor, etc.",
            },
            "authority_level": {
                "type": "string",
                "enum": ["statute", "regulation", "policy", "guidance", "internal"],
            },
            "complexity": {
                "type": "string",
                "enum": ["basic", "intermediate", "advanced"],
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Search keywords",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (default 10)",
            },
        },
    },
}
```

#### Task 3.3: Add Document Fetch Tool

```python
def _exec_knowledge_fetch(params: dict, tenant_id: str, session_id: str = None) -> dict:
    """Fetch full document content from S3 given a document_id or s3_key."""
    s3 = _get_s3()
    bucket = os.getenv("S3_BUCKET", "eagle-documents-695681773636-dev")
    key = params.get("s3_key") or params.get("document_id")

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8", errors="replace")
        return {
            "document_id": key,
            "content": content[:50000],  # Limit to 50KB
            "truncated": len(content) > 50000,
        }
    except Exception as e:
        return {"error": str(e)}
```

---

### Phase 4: Deploy & Validate (Day 4)

#### Task 4.1: Deploy Lambda Changes

```bash
cd infrastructure/cdk-eagle
npm run build
npx cdk deploy EagleStorageStack-dev --require-approval never
```

#### Task 4.2: Run Migration

```bash
# Copy documents
python scripts/migrate-knowledge-base.py

# Trigger metadata extraction
python scripts/backfill-metadata.py
```

#### Task 4.3: Validate DynamoDB Population

```bash
# Check item count
aws dynamodb scan --table-name eagle-document-metadata-dev --select COUNT

# Sample items
aws dynamodb scan --table-name eagle-document-metadata-dev --limit 5
```

#### Task 4.4: Test Agent Queries

```python
# Test knowledge_search tool
result = execute_tool("knowledge_search", {
    "topic": "funding",
    "limit": 5,
})
print(result)

# Test knowledge_fetch tool
result = execute_tool("knowledge_fetch", {
    "s3_key": "eagle-knowledge-base/approved/financial-advisor/appropriations-law/appropriations_law_IDIQ_funding.txt",
})
print(result["content"][:500])
```

---

## Validation Commands

```bash
# Phase 1: Lambda schema
cd infrastructure/cdk-eagle/lambda/metadata-extraction
python -c "from models import DocumentMetadata; print(DocumentMetadata.__dataclass_fields__.keys())"

# Phase 2: Migration
aws s3 ls s3://eagle-documents-695681773636-dev/eagle-knowledge-base/approved/ --recursive | wc -l
# Expected: 195

# Phase 3: DynamoDB
aws dynamodb scan --table-name eagle-document-metadata-dev --select COUNT
# Expected: {"Count": 195, ...}

# Phase 4: Agent tool
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Search the knowledge base for IDIQ funding guidance"}'
```

---

## Rollback Plan

1. **Lambda rollback**: Redeploy previous version via CDK
2. **DynamoDB**: Delete items with scan + batch delete (data is regenerable)
3. **S3**: Keep `rh-eagle-files` as source of truth until migration confirmed

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Documents in `eagle-documents-*` | 195 |
| Metadata items in DynamoDB | 195 |
| Fields per item | 28+ |
| Agent can query by topic | Yes |
| Agent can query by authority_level | Yes |
| Full document fetch works | Yes |

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Lambda schema | 4 hours | None |
| Phase 2: Migration scripts | 2 hours | Phase 1 |
| Phase 3: Agent tools | 3 hours | Phase 1 |
| Phase 4: Deploy & validate | 2 hours | Phases 1-3 |
| **Total** | **~2 days** | |

---

## Files to Modify

| File | Changes |
|------|---------|
| `infrastructure/cdk-eagle/lambda/metadata-extraction/models.py` | Add 15 new fields |
| `infrastructure/cdk-eagle/lambda/metadata-extraction/extractor.py` | Update Bedrock prompt |
| `infrastructure/cdk-eagle/lambda/metadata-extraction/handler.py` | Compute word_count, page_count |
| `infrastructure/cdk-eagle/lib/storage-stack.ts` | Add 2 new GSIs |
| `server/app/agentic_service.py` | Add knowledge_search, knowledge_fetch tools |
| `scripts/migrate-knowledge-base.py` | New file |
| `scripts/backfill-metadata.py` | New file |

---

## Open Questions

1. **Authority on schema**: Is `metadata-schema.md` the canonical schema, or should we extend it?
2. **Bedrock model**: Use Haiku for cost savings or Sonnet for accuracy?
3. **HITL review**: Should migrated docs go through `pending/` or direct to `approved/`?
4. **Cleanup**: Delete `rh-eagle-files` after migration, or keep as backup?

---

## References

- Schema spec: `/Users/hoquemi/Downloads/metadata-schema.md`
- Lambda code: `infrastructure/cdk-eagle/lambda/metadata-extraction/`
- Storage stack: `infrastructure/cdk-eagle/lib/storage-stack.ts`
- Agent service: `server/app/agentic_service.py`
