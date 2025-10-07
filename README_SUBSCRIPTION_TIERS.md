# Multi-Tier Subscription System

## Overview
Enhanced the multi-tenant Bedrock chat application with a 3-tier subscription system (Basic, Advanced, Premium) with usage limitations and MCP server integration.

## 🏷️ Subscription Tiers

### Basic Tier
- **Daily Messages**: 50
- **Monthly Messages**: 1,000
- **Session Duration**: 30 minutes
- **Concurrent Sessions**: 1
- **MCP Server Access**: ❌ No
- **Price**: Free

### Advanced Tier
- **Daily Messages**: 200
- **Monthly Messages**: 5,000
- **Session Duration**: 2 hours
- **Concurrent Sessions**: 3
- **MCP Server Access**: ✅ Yes
- **Price**: $29/month

### Premium Tier
- **Daily Messages**: 1,000
- **Monthly Messages**: 25,000
- **Session Duration**: 8 hours
- **Concurrent Sessions**: 10
- **MCP Server Access**: ✅ Yes
- **Price**: $99/month

## 🔧 New Components

### 1. Subscription Service (`app/subscription_service.py`)
- Manages tier limits and usage tracking
- Enforces daily/monthly message limits
- Tracks concurrent sessions
- Handles usage analytics

### 2. MCP Service (`app/mcp_service.py`)
- Model Context Protocol server implementation
- Tier-based tool access control
- Available tools:
  - `get_tier_info`: Get subscription tier details
  - `upgrade_tier`: Simulate tier upgrades
  - `get_usage_analytics`: Detailed usage analytics
  - `manage_limits`: Administrative limit management

### 3. Enhanced Data Models (`app/models.py`)
- `SubscriptionTier`: Enum for tier types
- `TierLimits`: Usage limits per tier
- `SubscriptionUsage`: Current usage tracking
- Updated session models with tier information

### 4. Tier-Based Storage (`app/dynamodb_store.py`)
- Sessions stored with tier prefix: `{tenant_id}-{tier}-{user_id}-{session_id}`
- Separate usage tracking per tier
- Enhanced session management

## 🚀 Deployment Updates

### CDK Infrastructure (`infra/cdk/app.py`)
- Added `custom:subscription_tier` attribute to Cognito User Pool
- Maintains backward compatibility

### Test User Creation (`scripts/create_test_users_with_tiers.py`)
- Creates users across all tiers for testing
- Generates JWT tokens with tier information
- Provides testing instructions

## 📊 API Enhancements

### New Endpoints

#### Get Subscription Info
```bash
GET /api/tenants/{tenant_id}/subscription
Authorization: Bearer <jwt-token>
```

#### Execute MCP Tools
```bash
POST /api/mcp/tools/{tool_name}
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "tenant_id": "tenant-001",
  "arguments": {...}
}
```

#### Get Available MCP Tools
```bash
GET /api/mcp/tools
Authorization: Bearer <jwt-token>
```

### Enhanced Endpoints
- All chat endpoints now enforce tier limits
- Session creation checks concurrent limits
- Usage tracking per tier

## 🧪 Testing the Tier System

### 1. Deploy Infrastructure
```bash
cd infra/cdk
cdk deploy
```

### 2. Create Test Users
```bash
export COGNITO_USER_POOL_ID="your-pool-id"
export COGNITO_CLIENT_ID="your-client-id"
python scripts/create_test_users_with_tiers.py
```

### 3. Test Different Tiers
1. Use JWT tokens from script output
2. Test message limits by sending multiple messages
3. Try MCP tools with Advanced/Premium users
4. Verify Basic users can't access MCP tools

### 4. Frontend Testing
- Visit http://localhost:8000
- Register new users (default to Basic tier)
- View subscription info and limits
- Test MCP tools if available

## 🔒 Security & Isolation

### Tier-Based Access Control
- JWT tokens include `custom:subscription_tier`
- All endpoints validate tier permissions
- MCP tools blocked for Basic tier users
- Usage limits enforced at API level

### Data Isolation
- Sessions stored with tier prefix for complete separation
- Usage metrics tracked per tenant-tier combination
- Cross-tier access prevention

## 📈 Usage Analytics

### Per-Tier Metrics
- Daily/monthly message counts
- Session duration tracking
- Concurrent session monitoring
- MCP tool usage (Advanced/Premium only)

### Analytics Endpoints
- Enhanced tenant analytics with tier information
- Usage limit status and remaining quotas
- Tier-specific feature usage

## 🔄 Migration Path

### Existing Users
- Default to Basic tier if no tier specified
- Backward compatible with existing JWT tokens
- Gradual migration to tier-based system

### Upgrading Tiers
- MCP tool `upgrade_tier` simulates upgrades
- Real implementation would integrate with billing system
- Immediate access to new tier features

## 🛠️ Development Notes

### MCP Server Implementation
- Follows Model Context Protocol standards
- Extensible tool system
- Tier-based access control
- Error handling and validation

### Performance Considerations
- Usage tracking optimized for high throughput
- Efficient tier limit checking
- Minimal overhead for Basic tier users

This tier system provides a complete foundation for monetizing the Bedrock chat application while maintaining the multi-tenant architecture and adding powerful MCP server capabilities for advanced users.