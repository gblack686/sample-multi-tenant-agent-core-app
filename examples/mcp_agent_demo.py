#!/usr/bin/env python3
"""
Demo: MCP-Agent Core Integration
Shows how MCP tools are integrated with Bedrock Agent Core runtime capabilities
"""
import asyncio
import os
from app.models import TenantContext, SubscriptionTier
from app.mcp_service import MCPClient
from app.agentic_service import AgenticService
from app.mcp_agent_integration import MCPAgentCoreIntegration, MCPActionGroupSimulator

async def demo_mcp_agent_integration():
    """Demonstrate MCP-Agent Core integration"""
    
    print("🔗 MCP-Agent Core Integration Demo")
    print("=" * 50)
    
    # Initialize services
    agent_id = os.getenv("BEDROCK_AGENT_ID", "demo-agent")
    agentic_service = AgenticService(agent_id)
    mcp_client = MCPClient()
    integration = MCPAgentCoreIntegration(agentic_service, mcp_client)
    
    # Test tenant context
    tenant_context = TenantContext(
        tenant_id="demo-tenant",
        user_id="demo-user",
        session_id="demo-session"
    )
    
    # Demo different subscription tiers
    tiers = [SubscriptionTier.BASIC, SubscriptionTier.ADVANCED, SubscriptionTier.PREMIUM]
    
    for tier in tiers:
        print(f"\n🏷️  Testing {tier.value.upper()} Tier")
        print("-" * 30)
        
        # Show available MCP tools
        available_tools = await mcp_client.get_available_tools(tier)
        print(f"Available MCP Tools: {available_tools}")
        
        # Test messages that trigger MCP tools
        test_messages = [
            "What's my subscription tier info?",
            "Show me my usage analytics",
            "I want to upgrade to premium"
        ]
        
        for message in test_messages:
            print(f"\n📝 Message: {message}")
            
            try:
                # This would normally call the integrated service
                # For demo, we'll simulate the integration
                result = await simulate_mcp_agent_integration(
                    integration, message, tenant_context, tier
                )
                
                print(f"✅ Response: {result['response'][:100]}...")
                
                if 'mcp_integration' in result:
                    mcp_info = result['mcp_integration']
                    print(f"🔧 MCP Tool Used: {mcp_info['tool_used']}")
                    print(f"🎯 Integration Success: {mcp_info['integration_success']}")
                
                if 'capabilities_used' in result:
                    caps = result['capabilities_used']
                    print(f"🧠 Capabilities: Planning={caps.get('planning', False)}, "
                          f"MCP={caps.get('mcp_tools', False)}, "
                          f"Reasoning={caps.get('reasoning', False)}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print()

async def simulate_mcp_agent_integration(integration, message, tenant_context, tier):
    """Simulate the MCP-Agent Core integration for demo"""
    
    # Get available tools
    available_tools = await integration.mcp_client.get_available_tools(tier)
    
    # Parse for MCP tool request
    mcp_request = integration._parse_mcp_tool_request(message, available_tools)
    
    if mcp_request and available_tools:
        # Execute MCP tool
        mcp_result = await integration.mcp_client.execute_mcp_tool(
            mcp_request["tool_name"],
            mcp_request["arguments"],
            tier
        )
        
        # Simulate Agent Core response
        agent_result = {
            "response": f"Based on the {mcp_request['tool_name']} results, here's what I found: {mcp_result}",
            "session_id": tenant_context.session_id,
            "tenant_id": tenant_context.tenant_id,
            "agentic_trace": {
                "planning_steps": ["analyze_request", "execute_mcp_tool", "synthesize_response"],
                "reasoning_chain": [f"User requested {mcp_request['tool_name']} information"],
                "mcp_tools": [{
                    "tool_name": mcp_request["tool_name"],
                    "result": mcp_result
                }]
            },
            "capabilities_used": {
                "planning": True,
                "reasoning": True,
                "mcp_tools": True,
                "subscription_aware": True
            },
            "mcp_integration": {
                "tool_used": mcp_request["tool_name"],
                "tool_result": mcp_result,
                "integration_success": True
            },
            "usage_metrics": {"mcp_integration": True}
        }
        
        return agent_result
    
    else:
        # Standard response without MCP
        return {
            "response": f"I understand your request: '{message}'. However, this requires MCP tools which are not available for your subscription tier.",
            "session_id": tenant_context.session_id,
            "tenant_id": tenant_context.tenant_id,
            "capabilities_used": {
                "planning": False,
                "mcp_tools": False
            },
            "usage_metrics": {"standard_response": True}
        }

def demo_action_group_schema():
    """Demo MCP tools as Action Group schemas"""
    
    print("\n🔧 MCP Action Group Schema Generation")
    print("=" * 50)
    
    mcp_client = MCPClient()
    simulator = MCPActionGroupSimulator(mcp_client)
    
    for tier in [SubscriptionTier.BASIC, SubscriptionTier.ADVANCED, SubscriptionTier.PREMIUM]:
        print(f"\n🏷️  {tier.value.upper()} Tier Action Group Schema:")
        schema = simulator.generate_action_group_schema(tier)
        
        print(f"Title: {schema['info']['title']}")
        print(f"Available Endpoints: {list(schema['paths'].keys())}")
        
        if schema['paths']:
            for path, methods in schema['paths'].items():
                for method, details in methods.items():
                    print(f"  {method.upper()} {path}: {details['summary']}")

async def main():
    """Run all demos"""
    await demo_mcp_agent_integration()
    demo_action_group_schema()
    
    print("\n🎯 Key Integration Benefits:")
    print("- MCP tools seamlessly integrated with Agent Core runtime")
    print("- Subscription tier-aware tool access")
    print("- Enhanced trace analysis with MCP context")
    print("- Unified response format combining MCP and Agent results")
    print("- Action Group simulation for future Bedrock Agent integration")

if __name__ == "__main__":
    asyncio.run(main())