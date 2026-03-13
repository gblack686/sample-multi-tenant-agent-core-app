# Full AgentCore Adoption Plan

**Date**: 2026-03-12
**Scope**: Integrate all 7 GA AgentCore services into EAGLE
**SDK Version**: `bedrock-agentcore>=1.4.0` (upgrade from `>=0.1.0`)

---

## Current State

| Service | Status | File |
|---------|--------|------|
| Memory | 54% (6/13 ops, no batch) | `agentcore_memory.py` (214 lines) |
| Code Interpreter | Live w/ fallback | `agentcore_code.py` (133 lines) |
| Browser | Stubbed (falls back to requests) | `agentcore_browser.py` (191 lines) |
| Gateway | Not started | — |
| Identity | Not started (manual Cognito) | `cognito_auth.py` (348 lines) |
| Observability | Not started (custom telemetry) | `cloudwatch_emitter.py` (238 lines) |
| Runtime | Not started (ECS Fargate) | `compute-stack.ts` (250+ lines) |
| Policy | Not started (manual TIER_TOOLS dict) | `strands_agentic_service.py:186-190` |
| Evaluations | Preview only | — |

---

## Phase 1: Complete Existing Tools (1-2 days)

### 1A. Complete Browser Tool
**File**: `server/app/agentcore_browser.py`

Replace stubbed `_agentcore_browse()` with full Playwright session:

```python
from bedrock_agentcore.tools import BrowserClient, browser_session

async def _agentcore_browse(urls: list[str], question: str = None) -> list[dict]:
    results = []
    client = _get_browser_client()
    for url in urls:
        with browser_session(client) as session:
            session.navigate(url)
            # Wait for page load
            session.wait_for_selector("body", timeout=10000)
            # Extract content
            if question:
                content = session.evaluate(f"""
                    document.body.innerText
                """)
            else:
                content = session.evaluate("document.body.innerText")
            # Screenshot for debugging
            screenshot = session.screenshot()
            results.append({
                "url": url,
                "content": content[:10000],
                "title": session.evaluate("document.title"),
                "success": True,
            })
    return results
```

**Validation**: `python -c "from app.agentcore_browser import browse_urls; print(browse_urls({'urls': ['https://sam.gov']}))"`

### 1B. Add Batch Memory Operations
**File**: `server/app/agentcore_memory.py`

Add batch_write and batch_delete using provisioned-but-unused IAM actions:

```python
def batch_write(actor_id: str, session_id: str, files: dict[str, str]) -> dict:
    """Write multiple workspace files atomically."""
    manager = _get_manager()
    if not manager:
        return _fallback_batch_write(actor_id, files)
    records = [
        {"path": path, "content": content, "actor_id": actor_id}
        for path, content in files.items()
    ]
    manager.batch_create_memory_records(records)
    return {"written": len(files), "paths": list(files.keys())}
```

### 1C. Verify Code Interpreter Response Parsing
**File**: `server/app/agentcore_code.py`

Test with actual SDK v1.4.x response structure. Verify `session.execute_code()` return format matches our parsing at lines 74-78.

**Validation**: `ruff check app/agentcore_*.py && python -m pytest tests/test_agentcore_tools.py -v`

---

## Phase 2: Gateway — Replace Manual Tool Wiring (2-3 days)

### What Changes
Replace `_SERVICE_TOOL_DEFS` (70 lines, 26 manual tool definitions) and `TOOL_DISPATCH` (18 entries) with a single MCP Gateway that auto-discovers tools from OpenAPI specs.

### 2A. Create OpenAPI Spec for EAGLE Tools
**New file**: `server/app/openapi_tools.yaml`

Extract tool schemas from `agentic_service.py` EAGLE_TOOLS list into OpenAPI 3.0 format. Each of the 18 tools becomes an endpoint:

```yaml
paths:
  /tools/s3_document_ops:
    post:
      operationId: s3_document_ops
      summary: Manage acquisition documents in S3
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/S3DocumentOpsInput'
```

### 2B. Create Gateway via Starter Toolkit
```python
from bedrock_agentcore_starter_toolkit import GatewayClient

gateway = GatewayClient()
gateway.create_mcp_gateway(
    name="eagle-tools",
    api_spec_path="server/app/openapi_tools.yaml",
    enable_semantic_search=True,  # Agent picks best tool by query
)
```

### 2C. Wire Gateway to Strands Agent
**File**: `server/app/strands_agentic_service.py`

Replace `_build_service_tools()` (46 lines) with Gateway MCP client:

```python
from bedrock_agentcore.tools import MCPClient

def _build_service_tools_via_gateway(tenant_id, user_id, session_id):
    """Fetch tools from AgentCore Gateway (MCP) instead of manual definitions."""
    mcp = MCPClient(gateway_id=os.getenv("AGENTCORE_GATEWAY_ID"))
    return mcp.list_tools()  # Auto-discovered, typed, ready for Strands
```

### 2D. CDK Changes
**File**: `infrastructure/cdk-eagle/lib/core-stack.ts`

Add Gateway IAM permissions:
```typescript
'bedrock-agentcore-control:CreateGateway',
'bedrock-agentcore-control:GetGateway',
'bedrock-agentcore-control:ListGateways',
'bedrock-agentcore-control:DeleteGateway',
'bedrock-agentcore-control:CreateGatewayTarget',
'bedrock-agentcore-control:InvokeGateway',
```

**Env var**: `AGENTCORE_GATEWAY_ID` in compute-stack.ts

**Validation**: `npx cdk synth --quiet && python -m pytest tests/test_strands_eval.py -v`

---

## Phase 3: Identity — Replace Manual Cognito Auth (2-3 days)

### What Changes
Replace `cognito_auth.py` (348 lines of manual JWT validation, JWKS caching, UserContext extraction) with AgentCore Identity.

### 3A. Configure Identity Provider
```python
from bedrock_agentcore.identity import IdentityClient

identity = IdentityClient()
# Register existing Cognito pool as identity source
identity.register_provider(
    provider_type="cognito",
    user_pool_id="us-east-1_fyy3Ko0tX",
    client_id="7jlpjkiov7888kcbu57jcn68no",
    claims_mapping={
        "tenant_id": "custom:tenant_id",
        "tier": "custom:subscription_tier",
        "user_id": "sub",
    },
)
```

### 3B. Replace Auth Middleware
**File**: `server/app/cognito_auth.py` → simplify to AgentCore Identity decorator

```python
from bedrock_agentcore.identity import require_auth, get_identity

@require_auth
async def chat_endpoint(request):
    identity = get_identity(request)
    tenant_id = identity.claims["tenant_id"]
    user_id = identity.claims["user_id"]
    tier = identity.claims["tier"]
```

### 3C. Per-Session IAM Scoping
AgentCore Identity can issue per-session tokens with resource indicators — tenant-1 tokens only access tenant-1 S3 prefixes and DynamoDB partitions. This replaces manual `_extract_tenant_id()` everywhere.

### 3D. CDK Changes
```typescript
'bedrock-agentcore-control:CreateIdentityProvider',
'bedrock-agentcore-control:GetIdentityProvider',
'bedrock-agentcore-control:ListIdentityProviders',
'bedrock-agentcore-control:CreateWorkloadIdentity',
```

**Validation**: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/health`

---

## Phase 4: Observability — Replace Custom Telemetry (1-2 days)

### What Changes
Replace `cloudwatch_emitter.py` (238 lines, 7 emit functions) and `log_context.py` (93 lines) with ADOT auto-instrumentation.

### 4A. Add Dependencies
```
# requirements.txt
aws-opentelemetry-distro>=0.5.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
```

### 4B. Enable Auto-Instrumentation
**Launch command change** in `Dockerfile.backend`:
```dockerfile
CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Environment variables** in `compute-stack.ts`:
```typescript
AGENT_OBSERVABILITY_ENABLED: 'true',
OTEL_PYTHON_DISTRO: 'aws_distro',
OTEL_SERVICE_NAME: 'eagle-backend',
OTEL_EXPORTER_OTLP_ENDPOINT: 'https://xray.us-east-1.amazonaws.com',
```

### 4C. Add Custom Spans for Agent Operations
**File**: `server/app/strands_agentic_service.py`

```python
from opentelemetry import trace
tracer = trace.get_tracer("eagle.agent")

async def sdk_query_streaming(...):
    with tracer.start_as_current_span("supervisor_query") as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("tier", tier)
        span.set_attribute("fast_path", use_fast_path)
        # ... existing logic
```

### 4D. Deprecate Custom Telemetry
- Keep `cloudwatch_emitter.py` as optional supplement for EAGLE-specific business events (feedback, eval results)
- Remove `emit_trace_started`, `emit_trace_completed`, `emit_tool_started`, `emit_tool_result` — ADOT handles these automatically
- Keep `emit_feedback_submitted` (business event, not infra trace)

**Validation**: Deploy → check CloudWatch X-Ray traces → verify agent spans appear

---

## Phase 5: Policy — Replace TIER_TOOLS Dict (1 day)

### What Changes
Replace the manual Python dict:
```python
TIER_TOOLS = {
    "basic": [],
    "advanced": ["workspace_memory", "web_search"],
    "premium": ["browse_url", "code_execute"],
}
```

With Cedar policies enforced at the Gateway level.

### 5A. Create Policy Engine
```python
import boto3
client = boto3.client('bedrock-agentcore-control')

# Create policy engine attached to Gateway
client.create_policy_engine(
    name="eagle-tier-gating",
    gatewayId=GATEWAY_ID,
)
```

### 5B. Define Tier Policies (Natural Language → Cedar)
```
Policy: "basic-tier-restrictions"
Rule: "Users with tier=basic cannot invoke workspace_memory, web_search,
       browse_url, code_execute, or create_document tools."

Policy: "advanced-tier-restrictions"
Rule: "Users with tier=advanced cannot invoke browse_url or code_execute tools."

Policy: "premium-tier-access"
Rule: "Users with tier=premium can invoke all tools."
```

### 5C. Remove Manual Gating Code
Delete `TIER_TOOLS` dict and any `if tier not in ...` checks. Policy enforcement happens at the Gateway before the request reaches the agent.

**Validation**: Send browse_url request as basic-tier user → expect 403

---

## Phase 6: Runtime — Replace ECS Fargate (3-5 days)

### What Changes
Replace self-managed ECS Fargate (2 services, ALB, auto-scaling, Docker builds, ECR pushes, compute-stack.ts) with AgentCore Runtime.

### 6A. Wrap Agent as Runtime Entrypoint
**New file**: `server/runtime_app.py`

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
async def handle_request(request):
    """Main agent entry point — replaces FastAPI POST /api/chat."""
    from app.strands_agentic_service import sdk_query_streaming

    prompt = request.get("prompt", "")
    tenant_id = request.identity.claims["tenant_id"]
    user_id = request.identity.claims["user_id"]
    tier = request.identity.claims["tier"]
    session_id = request.get("session_id")

    chunks = []
    async for chunk in sdk_query_streaming(
        prompt=prompt,
        tenant_id=tenant_id,
        user_id=user_id,
        tier=tier,
        session_id=session_id,
    ):
        chunks.append(chunk)
        yield chunk  # Bidirectional streaming

@app.ping
async def health():
    return {"status": "healthy", "service": "EAGLE"}
```

### 6B. Deploy via Starter Toolkit
```bash
pip install bedrock-agentcore-starter-toolkit
agentcore launch \
  --name eagle-agent \
  --source ./server \
  --entrypoint runtime_app.py \
  --memory-id eagle_workspace_memory-Tch0BU74Ex \
  --gateway-id $AGENTCORE_GATEWAY_ID \
  --identity-provider cognito \
  --region us-east-1
```

### 6C. Frontend Adaptation
The Next.js frontend currently calls `POST /api/invoke` which proxies to the FastAPI backend ALB. With Runtime:

**File**: `client/app/api/invoke/route.ts`
```typescript
// Replace: fetch(`${FASTAPI_URL}/api/chat`, ...)
// With:    invoke AgentCore Runtime endpoint
const response = await fetch(
  `https://bedrock-agentcore.us-east-1.amazonaws.com/agents/${AGENT_RUNTIME_ID}/invoke`,
  {
    method: 'POST',
    headers: { Authorization: `Bearer ${cognitoToken}` },
    body: JSON.stringify({ prompt: message, session_id: sessionId }),
  }
);
```

### 6D. What Gets Deleted
- `infrastructure/cdk-eagle/lib/compute-stack.ts` — ECS Fargate services, ALB, ECR repos
- `deployment/docker/Dockerfile.backend` — Runtime handles containerization
- `.github/workflows/deploy.yml` — deploy-backend/deploy-frontend jobs
- `server/app/main.py` — FastAPI app setup (routes stay, app shell goes)

### 6E. What Stays
- `client/` — Next.js frontend (deploy separately: S3+CloudFront or Amplify)
- `server/app/strands_agentic_service.py` — Agent logic unchanged
- `server/app/agentic_service.py` — Tool handlers unchanged
- `infrastructure/cdk-eagle/lib/core-stack.ts` — DynamoDB, Cognito, S3, IAM

**Validation**: `agentcore invoke --prompt "hello" --agent-id $AGENT_ID`

---

## Phase 7: Evaluations (When GA)

### What It Will Replace
Current eval suite: `server/tests/test_strands_eval.py` (28 tests, run via pytest)

### What It Adds
- **13 built-in evaluators**: Correctness, Faithfulness, Helpfulness, ResponseRelevance, Conciseness, etc.
- **Continuous monitoring**: Run evals against production traffic, not just pre-deploy
- **Custom evaluators**: Extend with EAGLE-specific checks (FAR accuracy, document completeness)

### When to Adopt
- Wait for GA (currently Preview in us-east-1, us-west-2)
- Keep pytest eval suite as regression baseline
- Layer AgentCore Evaluations on top for production monitoring

---

## Dependency Changes

### requirements.txt Updates
```diff
- bedrock-agentcore>=0.1.0
+ bedrock-agentcore>=1.4.0
+ bedrock-agentcore-starter-toolkit>=0.5.0
+ aws-opentelemetry-distro>=0.5.0
+ opentelemetry-api>=1.20.0
+ opentelemetry-sdk>=1.20.0
```

### CDK IAM Additions (core-stack.ts)
```typescript
// Gateway
'bedrock-agentcore-control:CreateGateway',
'bedrock-agentcore-control:GetGateway',
'bedrock-agentcore-control:ListGateways',
'bedrock-agentcore-control:InvokeGateway',
'bedrock-agentcore-control:CreateGatewayTarget',

// Identity
'bedrock-agentcore-control:CreateIdentityProvider',
'bedrock-agentcore-control:GetIdentityProvider',
'bedrock-agentcore-control:CreateWorkloadIdentity',

// Policy
'bedrock-agentcore-control:CreatePolicyEngine',
'bedrock-agentcore-control:GetPolicyEngine',
'bedrock-agentcore-control:ListPolicies',

// Runtime (if adopted)
'bedrock-agentcore-control:CreateAgentRuntime',
'bedrock-agentcore-control:GetAgentRuntime',
'bedrock-agentcore-control:InvokeAgentRuntime',
```

---

## Implementation Order & Timeline

| Phase | Service | Effort | Depends On | Deletes |
|-------|---------|--------|------------|---------|
| **1** | Complete Tools (Browser, Memory batch, Code verify) | 1-2 days | Nothing | — |
| **2** | Gateway (replace manual tool wiring) | 2-3 days | Phase 1 | `_SERVICE_TOOL_DEFS`, `TOOL_DISPATCH` boilerplate |
| **3** | Identity (replace Cognito auth) | 2-3 days | Phase 2 | `cognito_auth.py` (348 lines) |
| **4** | Observability (replace custom telemetry) | 1-2 days | Nothing | `cloudwatch_emitter.py` (most of 238 lines) |
| **5** | Policy (replace TIER_TOOLS) | 1 day | Phase 2+3 | `TIER_TOOLS` dict, manual gating |
| **6** | Runtime (replace ECS Fargate) | 3-5 days | Phase 2+3+4 | `compute-stack.ts`, Dockerfiles, deploy jobs |
| **7** | Evaluations | TBD | GA release | — (additive) |

**Total**: ~12-17 days for Phases 1-6

---

## Validation Commands

```bash
# Phase 1
ruff check app/agentcore_*.py
python -m pytest tests/ -k agentcore -v

# Phase 2
python -c "from bedrock_agentcore_starter_toolkit import GatewayClient; print('OK')"
npx cdk synth --quiet

# Phase 3
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/health

# Phase 4
opentelemetry-instrument uvicorn app.main:app --port 8000
# Check CloudWatch X-Ray for traces

# Phase 5
# Test: basic tier user attempts browse_url → 403
python -m pytest tests/test_tier_gating.py -v

# Phase 6
agentcore invoke --prompt "hello" --agent-id $AGENT_ID
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| NCI SCP blocks AgentCore IAM | Test in sandbox first (Phase 6a from existing plan) |
| Gateway latency overhead | Benchmark: direct TOOL_DISPATCH vs Gateway MCP roundtrip |
| Runtime cold start | AgentCore uses microVMs with fast cold starts; benchmark vs ECS |
| Identity migration breaks auth | Run dual-stack: Cognito direct + AgentCore Identity in parallel |
| Browser tool instability | Keep requests fallback; add circuit breaker |

---

## Lines of Code Impact

| Deleted | Added | Net |
|---------|-------|-----|
| `cognito_auth.py` (348) | `runtime_app.py` (~50) | -298 |
| `cloudwatch_emitter.py` (~180) | OTEL config (~20) | -160 |
| `_SERVICE_TOOL_DEFS` (70) | Gateway config (~30) | -40 |
| `TOOL_DISPATCH` boilerplate (50) | — | -50 |
| `compute-stack.ts` (250) | Runtime CDK (~50) | -200 |
| Deploy workflow jobs (100) | `agentcore launch` (~20) | -80 |
| **Total** | | **~-828 lines** |
