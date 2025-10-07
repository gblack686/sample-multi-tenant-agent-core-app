# MCP-Agent Core Integration

## Overview
This integration combines **Model Context Protocol (MCP)** with **AWS Bedrock Agent Core** runtime capabilities, creating a powerful unified system for subscription-aware agentic AI.

## 🔗 Integration Architecture

### Before Integration
```
User Message → Agent Core → Bedrock Agent → Response
User Message → MCP Tools → Response
```

### After Integration
```
User Message → MCP-Agent Integration → {
    ├── Parse MCP Tool Request
    ├── Execute MCP Tool (if needed)
    ├── Enhance Message with MCP Context
    ├── Invoke Agent Core with Enhanced Context
    ├── Merge MCP + Agent Results
    └── Return Unified Response
}
```

## 🧠 Key Integration Capabilities

### 1. **Intelligent Tool Routing**
```python
# Automatically detects MCP tool requests in natural language
message = "What's my subscription tier info?"
# → Routes to get_tier_info MCP tool
# → Enhances Agent Core context with MCP result
```

### 2. **Enhanced Runtime Context**
```python
session_attributes = {
    "mcp_tools_enabled": True,
    "available_mcp_tools": "get_tier_info,get_usage_analytics",
    "subscription_tier": "premium"
}

prompt_attributes = {
    "mcp_context": "Available MCP tools: get_tier_info, get_usage_analytics",
    "tier_capabilities": "Full premium features with unlimited access",
    "enable_mcp_routing": "true"
}
```

### 3. **Unified Trace Analysis**
```python
agentic_trace = {
    "planning_steps": ["analyze_request", "execute_mcp_tool", "synthesize_response"],
    "reasoning_chain": ["User requested tier information"],
    "mcp_tools": [{
        "tool_name": "get_tier_info",
        "arguments": {"tier": "current"},
        "result": {"tier_info": {...}}
    }],
    "capabilities_used": {
        "planning": True,
        "reasoning": True,
        "mcp_tools": True,
        "subscription_aware": True
    }
}
```

## 🔧 Integration Components

### 1. **MCPAgentCoreIntegration**
Main integration service that:
- Parses messages for MCP tool requests
- Executes MCP tools when needed
- Enhances Agent Core context with MCP results
- Merges responses from both systems

### 2. **MCPActionGroupSimulator**
Simulates MCP tools as Bedrock Agent Action Groups:
- Generates OpenAPI schemas for MCP tools
- Tier-based schema generation
- Future-ready for native Bedrock Agent integration

### 3. **Enhanced Runtime Context**
- Session attributes include MCP tool availability
- Prompt attributes provide MCP context
- Trace analysis captures MCP tool usage

## 🎯 Usage Examples

### Basic Tier (No MCP Access)
```python
message = "Show me my usage analytics"
# → Agent Core responds: "Analytics require Advanced/Premium tier"
# → No MCP tools executed
# → Standard Agent Core capabilities only
```

### Advanced Tier (MCP Tools Available)
```python
message = "Show me my usage analytics"
# → Detects MCP tool request: get_usage_analytics
# → Executes MCP tool with tenant context
# → Enhances Agent Core prompt with MCP results
# → Agent Core synthesizes comprehensive response
# → Returns unified response with both MCP data and Agent reasoning
```

### Premium Tier (Full MCP Access)
```python
message = "I want to upgrade my plan and see detailed analytics"
# → Detects multiple MCP tools: upgrade_tier, get_usage_analytics
# → Executes MCP tools in sequence
# → Agent Core plans multi-step response
# → Returns comprehensive response with planning trace
```

## 🚀 Agent Core Capabilities Enhanced by MCP

### 1. **Planning & Reasoning**
- MCP tool results inform Agent Core planning
- Multi-step reasoning incorporates subscription context
- Dynamic capability adjustment based on tier

### 2. **Tool Calling (Action Groups)**
- MCP tools act as virtual action groups
- Subscription-aware tool availability
- Seamless integration with existing action groups

### 3. **Knowledge Retrieval**
- MCP analytics enhance knowledge base queries
- Tenant-specific context from MCP tools
- Usage patterns inform retrieval strategies

### 4. **Orchestration**
- Complex workflows combining MCP and Agent capabilities
- Subscription tier-aware orchestration
- Multi-tenant workflow management

### 5. **Trace Analysis**
- Comprehensive traces including MCP tool usage
- Subscription tier impact on processing
- Enhanced analytics for tenant insights

## 📊 Integration Benefits

### For Users
- **Seamless Experience**: Natural language requests automatically route to appropriate tools
- **Tier-Aware Responses**: Responses adapt to subscription capabilities
- **Enhanced Functionality**: Combined power of MCP tools and Agent Core reasoning

### For Developers
- **Unified API**: Single endpoint handles both MCP and Agent Core
- **Extensible Architecture**: Easy to add new MCP tools
- **Rich Telemetry**: Comprehensive trace data for debugging and analytics

### For Business
- **Subscription Monetization**: Clear tier differentiation through MCP access
- **Usage Analytics**: Detailed insights into feature usage
- **Scalable Architecture**: Supports growth and new capabilities

## 🔮 Future Enhancements

### 1. **Native Action Group Integration**
```python
# Future: MCP tools as actual Bedrock Agent Action Groups
action_group_schema = mcp_simulator.generate_action_group_schema(tier)
# → Deploy as real Action Group in Bedrock Agent
```

### 2. **Advanced Tool Chaining**
```python
# Future: Complex MCP tool workflows
workflow = [
    "get_usage_analytics",
    "analyze_patterns", 
    "recommend_tier_upgrade",
    "execute_upgrade"
]
```

### 3. **Dynamic Tool Discovery**
```python
# Future: Runtime MCP server discovery
mcp_servers = discover_mcp_servers(tenant_context)
available_tools = aggregate_tools(mcp_servers, subscription_tier)
```

## 🧪 Testing the Integration

### 1. **Run the Demo**
```bash
python examples/mcp_agent_demo.py
```

### 2. **Test Different Tiers**
```bash
# Create test users with different tiers
python scripts/create_test_users_with_tiers.py

# Test in the application
python run.py
# Visit http://localhost:8000
# Use JWT tokens for different tiers
```

### 3. **API Testing**
```bash
# Test integrated endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me my subscription tier info",
    "tenant_context": {
      "tenant_id": "tenant-001",
      "user_id": "user-001", 
      "session_id": "session-001"
    }
  }'
```

This integration creates a **unified agentic system** where MCP tools and Agent Core capabilities work together seamlessly, providing subscription-aware, intelligent responses that leverage the best of both frameworks.