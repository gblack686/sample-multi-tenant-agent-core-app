# Amazon Bedrock AgentCore Migration Comparison

**Generated:** January 20, 2026  
**Purpose:** Analysis of how AWS Bedrock AgentCore fits into the NCI-OA-Agent tech stack

---

## What is Amazon Bedrock AgentCore?

AgentCore is AWS's **managed agentic AI platform** - designed to take AI agents from prototype to production without managing infrastructure. It was announced at re:Invent 2025 and is now generally available.

### Key Value Proposition

> "Accelerate agents to production with composable services that work with any framework, any model"

AgentCore provides:
- **Framework agnostic** runtime (LangGraph, CrewAI, Strands, custom)
- **Session isolation** via microVMs
- **Long-running tasks** up to 8 hours
- **Built-in memory, observability, and security**

---

## AgentCore Components

| Component | Purpose | Your Current Equivalent |
|-----------|---------|------------------------|
| **AgentCore Runtime** | Serverless environment to run AI agents | Your Express.js + Bedrock API calls |
| **AgentCore Memory** | Persistent memory across sessions | Your PostgreSQL + IndexedDB |
| **AgentCore Gateway** | Transform APIs into agent-ready tools | Your custom tool implementations |
| **AgentCore Identity** | Secure access to services | Your OAuth/OIDC implementation |
| **AgentCore Observability** | Monitor agent execution | Your Winston logging |
| **Code Interpreter** | Execute code safely | N/A (you don't have this yet) |
| **Browser Tool** | Web automation | N/A |

---

## Architecture Comparison

### Your Current Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    YOUR CURRENT IMPLEMENTATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User → SolidJS Frontend → Express.js Server                              │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                       │
│                    ▼               ▼               ▼                       │
│              inference.js    conversation.js   tools.js                    │
│                    │               │               │                        │
│                    ▼               ▼               ▼                        │
│            Bedrock Runtime   PostgreSQL     External APIs                  │
│            (Claude API)      (pgvector)    (Brave Search)                  │
│                                                                             │
│   ✅ Full control over prompts, streaming, conversation flow               │
│   ✅ Custom tool implementations                                            │
│   ✅ Client-side embeddings (Transformers.js)                              │
│   ⚠️ You manage: scaling, session isolation, memory                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### With AgentCore

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WITH AGENTCORE                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User → SolidJS Frontend → API Gateway                                    │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                       │
│                    ▼               ▼               ▼                        │
│           AgentCore Runtime  AgentCore Memory  AgentCore Gateway           │
│           (runs your agent)  (managed memory)  (tool registry)             │
│                    │               │               │                        │
│                    ▼               ▼               ▼                        │
│            Any LLM          Managed Storage   Your APIs as Tools           │
│        (Bedrock/External)                     (auto-transformed)           │
│                                                                             │
│   ✅ Session isolation (microVM per session)                               │
│   ✅ Long-running tasks (up to 8 hours)                                    │
│   ✅ Built-in observability                                                │
│   ✅ Framework agnostic (LangGraph, CrewAI, Strands, custom)               │
│   ⚠️ Less control, AWS pricing                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Migration Options

### Option 1: Hybrid Approach (Recommended)

Keep your frontend and some backend, add AgentCore for agent logic:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│   SolidJS Frontend (your existing code)                                     │
│        │                                                                    │
│        ▼                                                                    │
│   Express.js Server (slimmed down)                                         │
│   ├── Auth routes (keep)                                                   │
│   ├── User management (keep)                                               │
│   ├── File handling (keep)                                                 │
│   └── Agent endpoint → AgentCore Runtime ← NEW                             │
│                              │                                              │
│                    ┌─────────┼─────────┐                                   │
│                    ▼         ▼         ▼                                   │
│              Your Agent   Memory    Tools                                  │
│           (LangGraph/     (managed) (Gateway)                              │
│            Strands/                                                        │
│            custom)                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Minimal code changes
- Keep existing auth, user management, file handling
- Offload complex agent orchestration to AWS

### Option 2: Full AgentCore Migration

Replace your inference layer entirely:

```javascript
// BEFORE: Your current inference.js
import { BedrockRuntimeClient, ConverseStreamCommand } from "@aws-sdk/client-bedrock-runtime";

export async function converseStream(messages, modelId) {
  const client = new BedrockRuntimeClient({ region: "us-east-1" });
  const response = await client.send(new ConverseStreamCommand({
    modelId,
    messages,
    // ... your custom logic
  }));
  return response;
}

// AFTER: Using AgentCore Runtime
import { BedrockAgentRuntimeClient, InvokeAgentCommand } from "@aws-sdk/client-bedrock-agent-runtime";

export async function invokeAgent(prompt, sessionId) {
  const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });
  const response = await client.send(new InvokeAgentCommand({
    agentId: "YOUR_AGENT_ID",
    agentAliasId: "YOUR_ALIAS_ID", 
    sessionId,
    inputText: prompt,
  }));
  
  // AgentCore handles: memory, tool selection, execution
  for await (const chunk of response.completion) {
    yield new TextDecoder().decode(chunk.bytes);
  }
}
```

### Option 3: Selective Adoption

Use AgentCore for specific complex tasks only:

```javascript
// routes/agent.js
router.post('/research-task', async (req, res) => {
  // Use AgentCore Runtime for complex, long-running research
  const agentClient = new BedrockAgentRuntimeClient();
  const response = await agentClient.send(new InvokeAgentCommand({
    agentId: process.env.RESEARCH_AGENT_ID,
    sessionId: req.session.id,
    inputText: req.body.query,
  }));
  // Stream response back...
});

// routes/chat.js  
router.post('/chat', async (req, res) => {
  // Keep your existing direct Bedrock calls for simple chat
  const response = await converseStream(messages, modelId);
  // ...
});
```

---

## Feature Comparison Matrix

### When to Use What

| Use Case | Your Current Setup | AgentCore | Winner |
|----------|-------------------|-----------|--------|
| **Simple chat with Claude** | ✅ Perfect | Overkill | Current |
| **Multi-step reasoning tasks** | ⚠️ Manual orchestration | ✅ Built-in | AgentCore |
| **Long-running tasks (hours)** | ❌ Server timeout issues | ✅ Up to 8 hours | AgentCore |
| **Memory across sessions** | ⚠️ PostgreSQL (manual) | ✅ Managed | AgentCore |
| **Tool calling** | ⚠️ Custom implementation | ✅ Gateway auto-transforms | AgentCore |
| **Session isolation** | ❌ Shared process | ✅ microVM per session | AgentCore |
| **Multi-agent collaboration** | ❌ Not built | ✅ A2A protocol | AgentCore |
| **Cost control** | ✅ Predictable | ⚠️ Usage-based | Current |
| **Custom streaming UI** | ✅ Full control | ⚠️ Abstracted | Current |
| **Debugging/tracing** | ⚠️ Manual logging | ✅ Built-in observability | AgentCore |

---

## Bedrock Agents vs AgentCore

These are **different services** - important to understand the distinction:

| Aspect | Bedrock Agents (Original) | AgentCore (New) |
|--------|--------------------------|-----------------|
| **Philosophy** | Fully managed, AWS-opinionated | Framework-agnostic, BYOF |
| **LLM Support** | Bedrock models only | Any model (Bedrock, OpenAI, etc.) |
| **Tools** | Action Groups (Lambda functions) | Gateway (any API) + pre-built tools |
| **Framework** | AWS-specific | LangGraph, CrewAI, Strands, custom |
| **Execution** | Serverless (short tasks) | Serverless (up to 8 hours) |
| **Code** | Configuration-driven | Code-driven |
| **Best For** | Simple agents, AWS-native | Complex agents, any framework |

---

## Cost Implications

### Current vs AgentCore Pricing

| Component | Current Cost | With AgentCore |
|-----------|-------------|----------------|
| **Server** | $50-200/mo (self-hosted) | $0 (serverless) |
| **Bedrock API** | ~$X per 1K tokens | Same |
| **AgentCore Runtime** | N/A | ~$0.0001/sec execution |
| **AgentCore Memory** | N/A | ~$0.02/GB/month |
| **AgentCore Gateway** | N/A | Per-request pricing |
| **Total Estimate** | **$50-200/mo + API** | **$100-400/mo + API** |

### Cost Drivers

1. **Execution Time** - AgentCore Runtime charges per second
2. **Memory Storage** - Persistent memory has storage costs
3. **Gateway Requests** - Each tool invocation has overhead
4. **Session Duration** - Long sessions = higher costs

### When AgentCore is Cost-Effective

- ✅ Sporadic usage (pay only when running)
- ✅ Complex tasks that require isolation
- ✅ When development time > infrastructure cost
- ❌ High-volume, simple chat (current setup cheaper)
- ❌ Continuous streaming applications

---

## Full AWS Architecture with AgentCore

If you fully migrate to AWS:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FULL AWS NATIVE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CloudFront (CDN)                                                          │
│        │                                                                    │
│        ▼                                                                    │
│   S3 (SolidJS Static Hosting)                                              │
│        │                                                                    │
│        ▼                                                                    │
│   API Gateway                                                               │
│        │                                                                    │
│   ┌────┴────────────────────────────────────┐                              │
│   ▼                                         ▼                              │
│   Lambda Functions                    AgentCore Runtime                    │
│   ├── Auth (Cognito)                  ├── Research Agent                   │
│   ├── User Management                 ├── Analysis Agent                   │
│   └── File Processing                 └── Multi-Agent Workflows            │
│        │                                    │                              │
│        ▼                                    ▼                              │
│   Aurora PostgreSQL              ┌─────────┴─────────┐                     │
│   (user data, usage)             ▼                   ▼                     │
│                            AgentCore Memory    AgentCore Gateway           │
│                            (conversation)      (tools/APIs)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Supported Frameworks

AgentCore Runtime is framework-agnostic. You can use:

| Framework | Description | Best For |
|-----------|-------------|----------|
| **Strands** | AWS's own agent framework | AWS-native development |
| **LangGraph** | LangChain's graph-based agents | Complex workflows |
| **CrewAI** | Multi-agent orchestration | Team-based agents |
| **LlamaIndex** | RAG-focused framework | Knowledge retrieval |
| **Custom** | Your own implementation | Full control |

### Example: Using LangGraph with AgentCore

```python
# agent/main.py - Deploy to AgentCore Runtime
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

# Define your agent graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge("agent", "tools")
workflow.add_edge("tools", "agent")

app = workflow.compile()

# AgentCore Runtime handles deployment, scaling, memory
```

---

## Migration Checklist

### Phase 1: Assessment (Week 1-2)

- [ ] Inventory current AI/agent functionality
- [ ] Identify candidates for AgentCore migration
- [ ] Evaluate cost projections
- [ ] Review framework options (Strands, LangGraph, custom)

### Phase 2: Pilot (Week 3-4)

- [ ] Create AgentCore account and enable in region
- [ ] Build simple agent with AgentCore Runtime
- [ ] Test tool integration via Gateway
- [ ] Compare performance/cost with current setup

### Phase 3: Hybrid Integration (Week 5-8)

- [ ] Keep Express.js for auth, user management
- [ ] Route complex agent tasks to AgentCore
- [ ] Implement session bridging (your session → AgentCore session)
- [ ] Set up observability and monitoring

### Phase 4: Optimization (Ongoing)

- [ ] Monitor costs and usage patterns
- [ ] Optimize agent prompts and tool usage
- [ ] Evaluate multi-agent capabilities
- [ ] Consider full migration if ROI positive

---

## Recommendation Summary

| Question | Answer |
|----------|--------|
| Is AgentCore better than your current setup? | **Not necessarily** - it's a different abstraction level |
| Should you migrate now? | **Not urgently** - your current setup works well |
| When would AgentCore make sense? | Complex multi-step agents, long-running tasks, multi-agent systems |
| Can you use both? | **Yes** - hybrid approach is valid and recommended |
| Does it replace Express.js? | **No** - it replaces/augments your AI inference layer only |
| What's the learning curve? | **Moderate** - new concepts but good documentation |

### Final Verdict

**AgentCore is essentially AWS doing the orchestration work you're currently doing manually** in your `inference.js`, `conversation.js`, and tool implementations. 

If your current approach works and you have full control, there's no rush to migrate. But if you're building more complex agentic features (research agents, multi-step workflows, autonomous tasks), AgentCore could save significant development time.

**Recommended Path:**
1. Keep current stack for simple chat functionality
2. Experiment with AgentCore for new, complex agent features
3. Migrate incrementally based on ROI

---

## References

- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- [AgentCore Runtime Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)
- [AWS SDK for JavaScript - Bedrock Agent Runtime](https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/javascript_bedrock-agent-runtime_code_examples.html)
- [Sample AgentCore Full-Stack Webapp](https://github.com/aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp)
- [Deploy AI Agents with GitHub Actions](https://aws.amazon.com/blogs/ai/deploy-ai-agents-on-amazon-bedrock-agentcore-using-github-actions/)

---

*Document generated for NCI-OA-Agent project analysis. Last updated: January 20, 2026*

