"""
MCP-Agent Core Integration Service
Integrates Model Context Protocol with AWS Bedrock Agent Core runtime capabilities
"""
import json
from typing import Dict, Any, List, Optional
from app.models import TenantContext, SubscriptionTier
from app.mcp_service import MCPClient
from app.agentic_service import AgenticService
from app.runtime_context import RuntimeContextManager

class MCPAgentCoreIntegration:
    """Integrates MCP tools as Agent Core action groups"""
    
    def __init__(self, agentic_service: AgenticService, mcp_client: MCPClient):
        self.agentic_service = agentic_service
        self.mcp_client = mcp_client
        
    async def invoke_agent_with_mcp_tools(self, message: str, tenant_context: TenantContext, 
                                        subscription_tier: SubscriptionTier) -> Dict[str, Any]:
        """Invoke Agent Core with MCP tools available as action groups"""
        
        # Get available MCP tools for this tier
        available_tools = await self.mcp_client.get_available_tools(subscription_tier)
        
        # Build enhanced session attributes with MCP context
        session_attributes = RuntimeContextManager.build_session_attributes(
            tenant_context.tenant_id,
            tenant_context.user_id,
            tenant_context.session_id,
            additional_context={
                "mcp_tools_enabled": len(available_tools) > 0,
                "available_mcp_tools": ",".join(available_tools),
                "subscription_tier": subscription_tier.value
            }
        )
        
        # Build prompt attributes with MCP tool context
        prompt_attributes = RuntimeContextManager.build_prompt_session_attributes(
            tenant_context.tenant_id,
            tenant_context.user_id,
            message_context={
                "mcp_context": f"Available MCP tools: {', '.join(available_tools)}",
                "tier_capabilities": self._get_tier_capabilities(subscription_tier),
                "enable_mcp_routing": "true" if available_tools else "false"
            }
        )
        
        # Check if message requires MCP tool execution
        mcp_tool_request = self._parse_mcp_tool_request(message, available_tools)
        
        if mcp_tool_request:
            # Execute MCP tool directly
            mcp_result = await self.mcp_client.execute_mcp_tool(
                mcp_tool_request["tool_name"],
                mcp_tool_request["arguments"],
                subscription_tier
            )
            
            # Enhance message with MCP result for Agent Core processing
            enhanced_message = self._build_enhanced_message(message, mcp_result, mcp_tool_request)
            
            # Invoke Agent Core with MCP result context
            agent_result = self.agentic_service.invoke_agent_with_planning(
                enhanced_message, tenant_context
            )
            
            # Merge MCP and Agent Core results
            return self._merge_mcp_agent_results(agent_result, mcp_result, mcp_tool_request)
        
        else:
            # Standard Agent Core invocation with MCP context available
            return self.agentic_service.invoke_agent_with_planning(message, tenant_context)
    
    def _parse_mcp_tool_request(self, message: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
        """Parse message to detect MCP tool requests"""
        message_lower = message.lower()
        
        # Simple pattern matching for MCP tool requests
        tool_patterns = {
            "get_tier_info": ["tier info", "subscription info", "my plan", "plan details"],
            "upgrade_tier": ["upgrade", "change plan", "upgrade tier", "premium"],
            "get_usage_analytics": ["usage", "analytics", "statistics", "metrics"],
            "manage_limits": ["increase limit", "manage limit", "change limit"]
        }
        
        for tool_name in available_tools:
            if tool_name in tool_patterns:
                for pattern in tool_patterns[tool_name]:
                    if pattern in message_lower:
                        return {
                            "tool_name": tool_name,
                            "arguments": self._extract_tool_arguments(message, tool_name),
                            "confidence": 0.8
                        }
        
        return None
    
    def _extract_tool_arguments(self, message: str, tool_name: str) -> Dict[str, Any]:
        """Extract arguments for MCP tool from message"""
        # Simple argument extraction - in production, use NLP
        args = {}
        
        if tool_name == "get_tier_info":
            args = {"tier": "current"}
        elif tool_name == "upgrade_tier":
            if "premium" in message.lower():
                args = {"new_tier": "premium"}
            elif "advanced" in message.lower():
                args = {"new_tier": "advanced"}
        elif tool_name == "get_usage_analytics":
            args = {"period": "current_month"}
        elif tool_name == "manage_limits":
            if "increase" in message.lower():
                args = {"action": "increase", "limit_type": "daily"}
        
        return args
    
    def _build_enhanced_message(self, original_message: str, mcp_result: Dict[str, Any], 
                              mcp_request: Dict[str, Any]) -> str:
        """Build enhanced message with MCP result for Agent Core"""
        
        mcp_context = f"""
        MCP Tool Executed: {mcp_request['tool_name']}
        MCP Result: {json.dumps(mcp_result, indent=2)}
        
        Original User Message: {original_message}
        
        Please provide a comprehensive response based on the MCP tool result and the user's request.
        """
        
        return mcp_context
    
    def _merge_mcp_agent_results(self, agent_result: Dict[str, Any], mcp_result: Dict[str, Any], 
                               mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Merge MCP tool results with Agent Core results"""
        
        # Enhance agent result with MCP context
        agent_result["mcp_integration"] = {
            "tool_used": mcp_request["tool_name"],
            "tool_result": mcp_result,
            "integration_success": True
        }
        
        # Add MCP trace to agentic trace
        if "agentic_trace" in agent_result:
            agent_result["agentic_trace"]["mcp_tools"] = [{
                "tool_name": mcp_request["tool_name"],
                "arguments": mcp_request["arguments"],
                "result": mcp_result
            }]
        
        # Update capabilities used
        if "capabilities_used" in agent_result:
            agent_result["capabilities_used"]["mcp_tools"] = True
            agent_result["capabilities_used"]["subscription_aware"] = True
        
        return agent_result
    
    def _get_tier_capabilities(self, tier: SubscriptionTier) -> str:
        """Get tier capabilities description for prompt context"""
        capabilities = {
            SubscriptionTier.BASIC: "Basic chat capabilities only",
            SubscriptionTier.ADVANCED: "Advanced features including MCP tools, analytics, and extended sessions",
            SubscriptionTier.PREMIUM: "Full premium features with unlimited access to all MCP tools and advanced analytics"
        }
        return capabilities.get(tier, "Unknown tier")

class MCPActionGroupSimulator:
    """Simulates MCP tools as Bedrock Agent Action Groups"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
    
    def generate_action_group_schema(self, subscription_tier: SubscriptionTier) -> Dict[str, Any]:
        """Generate OpenAPI schema for MCP tools as action groups"""
        
        if subscription_tier == SubscriptionTier.BASIC:
            return {"openapi": "3.0.0", "info": {"title": "No MCP Tools", "version": "1.0.0"}, "paths": {}}
        
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "MCP Tools Action Group",
                "version": "1.0.0",
                "description": f"MCP tools available for {subscription_tier.value} tier"
            },
            "paths": {
                "/get_tier_info": {
                    "post": {
                        "summary": "Get subscription tier information",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "tier": {"type": "string", "description": "Subscription tier"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "Tier information"}}
                    }
                },
                "/get_usage_analytics": {
                    "post": {
                        "summary": "Get usage analytics",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "tenant_id": {"type": "string", "description": "Tenant ID"},
                                            "period": {"type": "string", "description": "Analytics period"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "Usage analytics"}}
                    }
                }
            }
        }
        
        if subscription_tier == SubscriptionTier.PREMIUM:
            # Add premium-only tools
            schema["paths"]["/upgrade_tier"] = {
                "post": {
                    "summary": "Upgrade subscription tier",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tenant_id": {"type": "string"},
                                        "new_tier": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Upgrade result"}}
                }
            }
        
        return schema