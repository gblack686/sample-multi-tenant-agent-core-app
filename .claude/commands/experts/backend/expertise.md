---
type: expert-file
parent: "[[backend/_index]]"
file-type: expertise
human_reviewed: false
tags: [expert-file, mental-model, backend, agentic-service, eagle, aws, s3, dynamodb, cloudwatch]
last_updated: 2026-02-17T00:00:00
---

# Backend Expertise (Complete Mental Model)

> **Sources**: server/app/*.py, server/eagle_skill_constants.py, infrastructure/cdk-eagle/lib/*.ts

---

## Part 1: Architecture Overview

### File Layout

```
server/app/
├── main.py                  # FastAPI app (v4.0.0), CORS, all endpoints
├── agentic_service.py       # 2357 lines — tool dispatch, handlers, stream_chat
├── sdk_agentic_service.py   # SDK-based service with SKILL_AGENT_REGISTRY
├── session_store.py         # Unified DynamoDB session/message/usage store (eagle table)
├── cognito_auth.py          # Cognito JWT auth, UserContext, DEV_MODE fallback
├── document_export.py       # DOCX/PDF/Markdown export
├── admin_service.py         # Dashboard stats, rate limiting, cost tracking
├── admin_auth.py            # Admin group auth (Cognito groups)
├── admin_cost_service.py    # 4-level cost reports (tenant, user, service, comprehensive)
├── subscription_service.py  # Tier-based limits (SubscriptionTier enum)
├── cost_attribution.py      # Per-tenant/user cost attribution
├── streaming_routes.py      # SSE streaming router (alternative to WebSocket)
├── models.py                # Pydantic models (ChatMessage, TenantContext, etc.)
├── auth.py                  # Legacy auth (get_current_user)
├── stream_protocol.py       # Stream protocol definitions
├── runtime_context.py       # Runtime context utilities
├── gateway_client.py        # API gateway client
├── bedrock_service.py       # Bedrock-specific service
├── mcp_agent_integration.py # MCP agent integration
├── weather_mcp_service.py   # Weather MCP compatibility endpoint
server/
├── eagle_skill_constants.py # Auto-discovery: walks eagle-plugin/, exports AGENTS, SKILLS
├── config.py                # App configuration
├── run.py                   # Uvicorn runner
├── requirements.txt         # Python dependencies
└── start_dev.sh             # Dev startup script
```

### Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | FastAPI 4.0.0 | REST + WebSocket + SSE |
| LLM SDK | `anthropic` Python SDK | Direct API or Bedrock |
| AWS SDK | `boto3` | S3, DynamoDB, CloudWatch, Cognito |
| Runtime | Python 3.11+ | `str | None` union syntax used |
| Async | `asyncio` | `stream_chat()` is async |
| Auth | Cognito JWT | `cognito_auth.py` with DEV_MODE fallback |
| Persistence | DynamoDB `eagle` table | Single-table design via `session_store.py` |
| Logging | `logging` | Logger: `eagle.agent`, `eagle.sessions` |

### Entry Points

| Function | File | Purpose |
|----------|------|---------|
| `execute_tool()` | agentic_service.py:2181 | Synchronous tool dispatch — called by test suite and chat |
| `stream_chat()` | agentic_service.py:2221 | Async streaming chat with tool-use loop |
| `get_client()` | agentic_service.py:2206 | Create Anthropic/AnthropicBedrock client |
| `api_chat()` | main.py:144 | REST chat endpoint with cost tracking |
| `websocket_chat()` | main.py:610 | WebSocket streaming chat |
| `api_list_sessions()` | main.py:228 | Session CRUD endpoints |
| `api_export_document()` | main.py:337 | Document export (DOCX/PDF/MD) |
| `api_list_documents()` | main.py:400 | S3 document browser |

### Configuration

```python
# agentic_service.py
_USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() == "true"
_BEDROCK_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL = os.getenv("ANTHROPIC_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0" if _USE_BEDROCK else "claude-haiku-4-5-20251001")

# main.py feature flags
USE_PERSISTENT_SESSIONS = os.getenv("USE_PERSISTENT_SESSIONS", "true").lower() == "true"
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
```

### Deployment (ECS Fargate via CDK)

```
Dockerfile.backend: python:3.11-slim
  COPY server/requirements.txt → pip install
  COPY server/app/, run.py, config.py, eagle_skill_constants.py
  COPY eagle-plugin/ → ../eagle-plugin/
  EXPOSE 8000
  CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000

ECS Service (EagleComputeStack):
  CPU: 0.5 vCPU | Memory: 1024 MiB
  Port: 8000
  ALB: Internal (not internet-facing)
  Health: /health (30s interval)
  Scaling: 1-3 tasks, target tracking

Environment Variables (from CDK):
  ANTHROPIC_API_KEY  → Secrets Manager
  EAGLE_TABLE        → "eagle" (DynamoDB)
  S3_BUCKET          → "nci-documents"
  AWS_REGION         → "us-east-1"
  LOG_GROUP          → "/eagle/app"
  USE_PERSISTENT_SESSIONS → "true"
  REQUIRE_AUTH       → "false" (dev) / "true" (prod)
```

---

## Part 2: Tool Dispatch System

### TOOL_DISPATCH (line 2167)

```python
TOOL_DISPATCH = {
    "s3_document_ops":  _exec_s3_document_ops,
    "dynamodb_intake":  _exec_dynamodb_intake,
    "cloudwatch_logs":  _exec_cloudwatch_logs,
    "search_far":       _exec_search_far,
    "create_document":  _exec_create_document,
    "get_intake_status": _exec_get_intake_status,
    "intake_workflow":  _exec_intake_workflow,
}
```

### TOOLS_NEEDING_SESSION (line 2178)

```python
TOOLS_NEEDING_SESSION = {"s3_document_ops", "create_document", "get_intake_status"}
```

These tools receive `session_id` as a third argument to enable per-user S3 prefix scoping.

### execute_tool() Flow (line 2181)

```
execute_tool(tool_name, tool_input, session_id)
  |-- tenant_id = _extract_tenant_id(session_id)
  |-- handler = TOOL_DISPATCH.get(tool_name)
  |-- if tool_name in TOOLS_NEEDING_SESSION:
  |       result = handler(tool_input, tenant_id, session_id)
  |   else:
  |       result = handler(tool_input, tenant_id)
  |-- return json.dumps(result, indent=2, default=str)
  |
  |-- On exception: return JSON error with tool name + suggestion
  |-- On unknown tool: return JSON {"error": "Unknown tool: {name}"}
```

### Handler Signatures

| Handler | Signature |
|---------|-----------|
| `_exec_s3_document_ops` | `(params, tenant_id, session_id)` |
| `_exec_dynamodb_intake` | `(params, tenant_id)` |
| `_exec_cloudwatch_logs` | `(params, tenant_id)` |
| `_exec_search_far` | `(params, tenant_id)` |
| `_exec_create_document` | `(params, tenant_id, session_id)` |
| `_exec_get_intake_status` | `(params, tenant_id, session_id)` |
| `_exec_intake_workflow` | `(params, tenant_id)` |

---

## Part 3: AWS Tool Handlers

### _exec_s3_document_ops (line 384)

**Actions**: `read`, `write`, `list`

| Action | Required Params | Returns |
|--------|----------------|---------|
| `read` | `key` | `{content, key, metadata}` |
| `write` | `key`, `content` | `{message, key, size}` |
| `list` | (optional: `prefix`) | `{documents: [{key, size, last_modified}], count}` |

- **Bucket**: `nci-documents`
- **Key prefix**: `eagle/{tenant}/{user}/` (from `_get_user_prefix()`)
- **Full key**: `{prefix}{params.key}`

### _exec_dynamodb_intake (line 471)

**Actions**: `create`, `read`, `update`, `list`

| Action | Required Params | Returns |
|--------|----------------|---------|
| `create` | `item_data` | `{message, item_id, pk, sk}` |
| `read` | `item_id` | `{item: {fields...}}` |
| `update` | `item_id`, `updates` | `{message, item_id}` |
| `list` | (optional) | `{items: [...], count}` |

- **Table**: `eagle`
- **Key schema**: `PK=INTAKE#{tenant_id}`, `SK=INTAKE#{item_id}`
- `item_id` auto-generated via `uuid.uuid4().hex[:12]` on create
- Timestamps: `created_at`, `updated_at` auto-set

### _exec_cloudwatch_logs (line 589)

**Actions**: `get_stream`, `recent`, `search`

| Action | Required Params | Returns |
|--------|----------------|---------|
| `get_stream` | `stream_name` | `{events: [...], count}` |
| `recent` | (optional: `limit`) | `{streams: [...], count}` |
| `search` | `pattern` | `{matches: [...], count}` |

- **Log group**: `/eagle/test-runs`
- Read-only operations; no write/delete actions

### _exec_search_far (line 708)

**Params**: `query` (search text), optional `parts` (FAR parts to search)

- Returns matching FAR clauses with relevance
- Uses embedded FAR reference data
- No AWS resource dependency

### _exec_create_document (line 1027)

**Params**: `doc_type`, `title`, `data` (dict of document-specific fields)

- Dispatches to `_generate_{doc_type}()` function
- Saves generated markdown to S3: `eagle/{tenant}/{user}/documents/{doc_type}_{timestamp}.md`
- Returns `{message, doc_type, s3_key, content_preview, word_count}`

### _exec_get_intake_status (line 1828)

**Params**: (none required)

- Scans S3 prefix `eagle/{tenant}/{user}/documents/` for existing docs
- Tracks 10 document types: 5 always required + 5 conditional
- Returns `{status: {type: "complete"|"pending"}, summary: {complete, pending, total}}`

**Always required**: sow, igce, market_research, acquisition_plan, cor_certification
**Conditional**: justification, eval_criteria, security_checklist, section_508, contract_type_justification

### _exec_intake_workflow (line 1955)

**Actions**: `start`, `advance`, `status`

| Action | Params | Returns |
|--------|--------|---------|
| `start` | `requirement_description` | `{workflow_id, stage, next_actions, progress_bar}` |
| `advance` | `workflow_id`, `completed_actions` | `{stage, next_actions, progress_bar}` |
| `status` | `workflow_id` | `{stage, progress, completed_documents}` |

- 4-stage workflow: Requirements Gathering -> Compliance Check -> Document Generation -> Review & Submit

---

## Part 4: Tenant Scoping

### Extract Functions

```python
_extract_tenant_id(session_id) -> str
    # Always returns "demo-tenant" (placeholder for production auth)

_extract_user_id(session_id) -> str
    # Returns "demo-user" for non "ws-" session IDs
    # Returns session_id itself for "ws-*" WebSocket sessions

_get_user_prefix(session_id) -> str
    # Returns "eagle/{tenant}/{user}/"
```

### S3 Key Patterns

| Pattern | Example |
|---------|---------|
| User prefix | `eagle/demo-tenant/demo-user/` |
| Document key | `eagle/demo-tenant/demo-user/documents/sow_20260209T120000.md` |
| Custom key | `eagle/demo-tenant/demo-user/{params.key}` |

### DynamoDB Key Patterns

| Key | Format | Example |
|-----|--------|---------|
| PK (Partition) | `INTAKE#{tenant_id}` | `INTAKE#demo-tenant` |
| SK (Sort) | `INTAKE#{item_id}` | `INTAKE#a1b2c3d4e5f6` |

### WebSocket Session Scoping

- Session IDs starting with `ws-` use the session ID as user_id
- This gives each WebSocket connection its own S3 namespace
- Non-ws sessions share the `demo-user` namespace

---

## Part 5: Document Generation

### 10 Document Types

| Type | Generator Function | Line | Key Content |
|------|-------------------|------|-------------|
| `sow` | `_generate_sow()` | 1086 | Statement of Work with objectives, deliverables, period of performance |
| `igce` | `_generate_igce()` | 1173 | Independent Government Cost Estimate with line items, totals |
| `market_research` | `_generate_market_research()` | 1250 | Market analysis, vendor capabilities, pricing benchmarks |
| `justification` | `_generate_justification()` | 1313 | Justification & Approval for sole source (FAR 6.302) |
| `acquisition_plan` | `_generate_acquisition_plan()` | 1381 | Streamlined 5-section acquisition plan |
| `eval_criteria` | `_generate_eval_criteria()` | 1481 | Technical evaluation factors and rating scale |
| `security_checklist` | `_generate_security_checklist()` | 1546 | IT security checklist (FISMA, FedRAMP) |
| `section_508` | `_generate_section_508()` | 1610 | Section 508 accessibility compliance statement |
| `cor_certification` | `_generate_cor_certification()` | 1681 | COR nominee certification with FAC-COR level |
| `contract_type_justification` | `_generate_contract_type_justification()` | 1754 | Contract type D&F elements |

### Generator Pattern

All generators follow the same signature and pattern:

```python
def _generate_{doc_type}(title: str, data: dict) -> str:
    """Generate a {document name} document."""
    # Extract fields from data dict with defaults
    field = data.get("field_name", "default value")
    # Build markdown string with headers, sections, FAR references
    content = f"# {title}\n\n..."
    # Return markdown string
    return content
```

### S3 Save Pattern (in _exec_create_document)

```python
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
s3_key = f"{prefix}documents/{doc_type}_{timestamp}.md"
_get_s3().put_object(Bucket="nci-documents", Key=s3_key, Body=content.encode())
```

### Document Data Fields

Each generator accepts different fields in the `data` dict. Common patterns:
- `title` is always the first positional argument
- `data.get("field", "default")` for optional fields
- Generators produce self-contained markdown with FAR references
- Word counts typically 200-800 words depending on type

---

## Part 6: SYSTEM_PROMPT

### Structure (7 Sections, ~4800 chars)

| Section | Content |
|---------|---------|
| 1. Identity & Mission | EAGLE is NCI OA intake assistant, knows FAR/DFARS/HHSAR |
| 2. Intake Philosophy | "Trish" pattern — start minimal, ask smart follow-ups |
| 3. Five-Phase Workflow | Minimal Intake -> Clarifying -> Pathway -> Documents -> Summary |
| 4. Key Thresholds | MPT $15K, SAT $250K, Cost Data $750K, 8(a) $4M/$7M, Davis-Bacon $25K |
| 5. Specialist Lenses | Legal, Tech Translator, Market Intelligence, Public Interest |
| 6. Document Types | Lists all 10 types with brief descriptions |
| 7. Tool Usage | Guidance on when to use workflow vs. direct tool calls |

### Five Phases

| Phase | Name | Actions |
|-------|------|---------|
| 1 | Minimal Intake | Collect requirement description, cost range, timeline |
| 2 | Clarifying Questions | Product vs service, vendor knowledge, funding, urgency |
| 3 | Pathway Determination | Micro-purchase / Simplified / Negotiated; contract type; set-asides |
| 4 | Document Requirements | Identify and generate required documents by acquisition type |
| 5 | Summary & Handoff | Determination table, document checklist, next steps |

### Specialist Lenses

| Lens | Focus |
|------|-------|
| Legal Counsel | GAO protests, FAR compliance, fiscal law, appropriations, protest vulnerabilities |
| Technical Translator | Bridge technical needs with contract language, evaluation criteria, performance standards |
| Market Intelligence | GSA rates, FPDS data, small business programs (8(a), HUBZone, WOSB, SDVOSB) |
| Public Interest | Fair competition, transparency, taxpayer value, congressional/media sensitivity |

---

## Part 7: Known Issues and Patterns

### Patterns That Work

- Lazy singleton AWS clients (`_get_s3()`, etc.) avoid repeated initialization
- `TOOLS_NEEDING_SESSION` set cleanly separates user-scoped vs. tenant-scoped handlers
- `json.dumps(result, indent=2, default=str)` handles datetime serialization
- Document generators use `data.get("field", "default")` for graceful degradation
- `_get_user_prefix()` centralizes S3 path construction

### Patterns to Avoid

- Don't add AWS client initialization outside lazy singletons (cold start cost)
- Don't hardcode `"demo-tenant"` in handlers — always use `_extract_tenant_id()`
- Don't skip `default=str` in `json.dumps()` — DynamoDB returns Decimal types
- Don't add new tools without updating both `TOOL_DISPATCH` and `EAGLE_TOOLS`

### Common Issues

- **Missing EAGLE_TOOLS entry**: Tool is dispatchable but Claude doesn't know about it (never called)
- **Missing TOOL_DISPATCH entry**: Tool schema defined but `execute_tool()` returns "Unknown tool"
- **Session scoping mismatch**: Tool added to `TOOLS_NEEDING_SESSION` but handler signature only takes `(params, tenant_id)`
- **DynamoDB Decimal**: `json.dumps()` without `default=str` raises `TypeError` on Decimal values
- **S3 prefix trailing slash**: `_get_user_prefix()` always ends with `/` — don't add another

### Adding a New Tool Handler

Checklist for adding a new tool:

1. **Define handler function**: `def _exec_new_tool(params, tenant_id)` or `(params, tenant_id, session_id)`
2. **Add to TOOL_DISPATCH** (line 2167): `"new_tool": _exec_new_tool,`
3. **Add to TOOLS_NEEDING_SESSION** (line 2178) if it needs per-user scoping
4. **Add to EAGLE_TOOLS** (line 173): Anthropic tool_use schema with name, description, input_schema
5. **Update SYSTEM_PROMPT** if the tool needs usage guidance
6. **Validate**: `python -c "import py_compile; py_compile.compile('server/app/agentic_service.py', doraise=True)"`

### stream_chat() Tool-Use Loop

```
stream_chat(messages, on_text, on_tool_use, on_tool_result, session_id)
  |-- MAX_TOOL_ITERATIONS = 10
  |-- Loop:
  |     |-- Send messages to Claude with EAGLE_TOOLS
  |     |-- Stream response (text deltas + tool_use blocks)
  |     |-- If stop_reason == "tool_use":
  |     |     |-- For each tool_use block:
  |     |     |     |-- execute_tool(name, input, session_id)
  |     |     |     |-- Append tool_result to messages
  |     |     |-- Continue loop
  |     |-- Else: break (end_turn or max_tokens)
  |-- Return {text, usage, model, tools_called}
```

---

## Part 8: Session Store (session_store.py)

### Unified `eagle` Table Access

All DynamoDB operations go through `session_store.py`, which implements the unified single-table design:

| Operation | PK | SK | Notes |
|-----------|----|----|-------|
| `create_session()` | `SESSION#{tenant}#{user}` | `SESSION#{session_id}` | Auto-generates UUID if not provided |
| `get_session()` | `SESSION#{tenant}#{user}` | `SESSION#{session_id}` | Returns None if not found |
| `list_sessions()` | `SESSION#{tenant}#{user}` | `begins_with(SESSION#)` | Sorted by created_at desc |
| `add_message()` | `SESSION#{tenant}#{user}` | `MSG#{session_id}#{msg_id}` | msg_id is auto-incremented |
| `get_messages()` | `SESSION#{tenant}#{user}` | `begins_with(MSG#{session_id}#)` | Sorted by SK |
| `record_usage()` | `USAGE#{tenant}` | `USAGE#{date}#{session}#{ts}` | Token counts, cost, model |

### Caching

- In-memory cache with 5-minute TTL per session
- Write-through: updates DynamoDB + cache simultaneously
- `_invalidate_cache()` on delete operations

### Configuration

```python
TABLE_NAME = os.getenv("EAGLE_SESSIONS_TABLE", "eagle")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "30"))
```

---

## Part 9: Authentication (cognito_auth.py)

### UserContext

```python
@dataclass
class UserContext:
    user_id: str
    tenant_id: str
    email: str
    tier: str  # "free", "pro", "enterprise"
    groups: List[str]
```

### Auth Flow

1. Client sends `Authorization: Bearer <JWT>` header
2. `extract_user_context(token)` decodes JWT (Cognito)
3. Falls back to `DEV_MODE` if `DEV_MODE=true` env var set
4. Dev mode returns `UserContext(user_id="dev-user", tenant_id="dev-tenant")`

### Feature Flags

- `REQUIRE_AUTH=false` → anonymous access allowed (dev)
- `REQUIRE_AUTH=true` → 401 if no valid JWT (production)
- `DEV_MODE=true` → bypass Cognito, use dev user context

---

## Part 10: CDK Integration Points

### EagleCoreStack → Backend

| Resource | CDK Reference | Backend Usage |
|----------|---------------|---------------|
| DynamoDB `eagle` | `Table.fromTableName()` (imported) | `session_store.py`, `agentic_service.py` |
| S3 `nci-documents` | `Bucket.fromBucketName()` (imported) | `agentic_service.py` s3_document_ops, create_document |
| Cognito `eagle-users-dev` | Created by Core stack | `cognito_auth.py` JWT validation |
| IAM `eagle-app-role-dev` | Created by Core stack | ECS task role with DDB/S3/CW permissions |
| CloudWatch `/eagle/app` | Created by Core stack | Application logging |

### EagleComputeStack → Backend

| Resource | CDK Config | Notes |
|----------|-----------|-------|
| ECR `eagle-backend-dev` | Image repository | Docker push target |
| ECS Service | 0.5 vCPU / 1024 MiB | Fargate task definition |
| ALB (internal) | Port 8000, /health | Not internet-accessible |
| Auto-scaling | 1-3 tasks | CPU target tracking |

### EagleCiCdStack → Backend

| Resource | Purpose |
|----------|---------|
| OIDC Provider | GitHub Actions federation |
| Deploy Role | `eagle-github-actions-dev` — ECR push + ECS deploy |

---

## Learnings

### patterns_that_work
- Tool dispatch via dict lookup is fast and easily extensible
- Lazy AWS client singletons work well for Lambda-style cold starts
- Generating markdown documents with embedded FAR references gives Claude useful context
- `_get_user_prefix()` as a single source of truth for S3 paths prevents scoping bugs
- Unified `eagle` DynamoDB table with PK/SK patterns handles sessions, messages, usage, costs in one table (discovered: 2026-02-16, component: session_store)
- Write-through cache in session_store.py gives fast reads without stale data (discovered: 2026-02-16, component: session_store)
- `DEV_MODE` flag in cognito_auth.py lets backend run without Cognito configured — essential for local dev and testing (discovered: 2026-02-16, component: cognito_auth)
- CDK `fromTableName()` / `fromBucketName()` pattern — import existing resources into stacks without recreating them (discovered: 2026-02-16, component: cdk-eagle)
- Internal ALB for backend keeps API not internet-accessible — frontend ALB is the only public entry point (discovered: 2026-02-16, component: compute-stack)
- Dockerfile copies `eagle-plugin/` to `../eagle-plugin/` so `eagle_skill_constants.py` can walk it at runtime (discovered: 2026-02-16, component: docker)

### patterns_to_avoid
- Don't test document generation with empty `data` dicts — generators produce minimal stubs
- Don't assume DynamoDB items have all fields — use `.get()` with defaults
- Don't call `_get_s3()` at module level — fails if AWS creds aren't configured at import time
- Don't create S3 clients inline per request (as in main.py `api_list_documents`) — use the lazy singleton from agentic_service.py instead (discovered: 2026-02-16, component: main.py)
- Don't hardcode `"nci-documents"` bucket name — use `os.getenv("S3_BUCKET", "nci-documents")` for CDK flexibility (discovered: 2026-02-16, component: cdk-eagle)
- Don't delete AWS resources (CF stacks, Lightsail, ECS) without confirming the new CDK stacks have images pushed and running tasks (discovered: 2026-02-16, component: aws-cleanup)

### common_issues
- AWS credentials not configured → all tool handlers fail with ClientError
- S3 bucket "nci-documents" doesn't exist → s3_document_ops and create_document fail
- DynamoDB table "eagle" doesn't exist → dynamodb_intake and session_store fail
- CloudWatch log group "/eagle/test-runs" doesn't exist → cloudwatch_logs returns empty
- ECS services show desiredCount=1 but runningCount=0 → no Docker images pushed to ECR yet (discovered: 2026-02-16, component: compute-stack)
- `MSYS_NO_PATHCONV=1` required on MINGW64/Git Bash when running AWS CLI with `/aws/...` paths — otherwise Git Bash converts them to `C:/Program Files/Git/aws/...` (discovered: 2026-02-16, component: aws-cli)
- Cognito pools with custom domains require `delete-user-pool-domain` before `delete-user-pool` (discovered: 2026-02-16, component: cognito)
- Versioned S3 buckets can't be deleted with `aws s3 rb --force` on MINGW — use Python boto3 with `bucket.object_versions.delete()` instead (discovered: 2026-02-16, component: s3)

### tips
- Use `execute_tool()` for testing — it's synchronous and returns JSON strings
- The `search_far` tool has no AWS dependency — good for offline testing
- `intake_workflow` is stateless — workflow state is tracked in the response, not persisted
- Check `EAGLE_TOOLS` list for the exact parameter schemas Claude sees
- Backend health check is at `/health` (not `/api/health`) — the ALB uses this for target group health (discovered: 2026-02-16)
- `main.py` version is 4.0.0 — reflects the merged multi-tenant + EAGLE architecture (discovered: 2026-02-16)
- `session_store.py` uses `boto3.resource("dynamodb")` (high-level) while `agentic_service.py` uses `boto3.client("dynamodb")` (low-level) — both access the same `eagle` table (discovered: 2026-02-16)
- Old infrastructure (Lightsail, old ECS clusters, old CF stacks) was cleaned up 2026-02-16 — ~$51-63/mo savings. See `.claude/specs/aws-resource-cleanup.md` for full inventory (discovered: 2026-02-16)
- Browser smoke test command at `.claude/commands/bowser/eagle-smoke-test.md` — tests login, home, chat, documents, workflows, admin, and backend health (discovered: 2026-02-17, component: bowser)
- Frontend auth-context.tsx auto-detects dev mode when `NEXT_PUBLIC_COGNITO_USER_POOL_ID` is empty — provides mock `dev-user` / `dev-tenant` without real Cognito (discovered: 2026-02-17, component: auth)
