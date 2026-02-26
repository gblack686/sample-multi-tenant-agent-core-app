#!/usr/bin/env python3
"""
Create test users with different subscription tiers for multi-tenant testing
"""
import boto3
import json
import base64
from datetime import datetime, timedelta
import os

def create_jwt_token(user_data):
    """Create a simple JWT token for testing (development only)"""
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    payload = {
        "sub": user_data["user_id"],
        "email": user_data["email"],
        "custom:tenant_id": user_data["tenant_id"],
        "custom:subscription_tier": user_data["subscription_tier"],
        "cognito:username": user_data["email"],
        "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
        "iat": int(datetime.now().timestamp())
    }
    
    # Base64 encode header and payload
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Create simple token (no signature for development)
    token = f"{header_encoded}.{payload_encoded}.dev-signature"
    
    return token

def main():
    # Test users with different subscription tiers
    test_users = [
        {
            "email": "basic-user@tenant1.com",
            "tenant_id": "tenant-001",
            "user_id": "basic-user-001",
            "subscription_tier": "basic",
            "password": "TempPass123!"
        },
        {
            "email": "advanced-user@tenant1.com", 
            "tenant_id": "tenant-001",
            "user_id": "advanced-user-001",
            "subscription_tier": "advanced",
            "password": "TempPass123!"
        },
        {
            "email": "premium-user@tenant1.com",
            "tenant_id": "tenant-001", 
            "user_id": "premium-user-001",
            "subscription_tier": "premium",
            "password": "TempPass123!"
        },
        {
            "email": "basic-user@tenant2.com",
            "tenant_id": "tenant-002",
            "user_id": "basic-user-002", 
            "subscription_tier": "basic",
            "password": "TempPass123!"
        },
        {
            "email": "premium-user@tenant2.com",
            "tenant_id": "tenant-002",
            "user_id": "premium-user-002",
            "subscription_tier": "premium", 
            "password": "TempPass123!"
        }
    ]
    
    print("🔐 Creating Multi-Tier Test Users for Bedrock Agent Chat")
    print("=" * 60)
    
    # Get Cognito configuration
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_CLIENT_ID")
    
    if not user_pool_id or not client_id:
        print("❌ Missing Cognito configuration. Set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID")
        return
    
    cognito = boto3.client('cognito-idp')
    
    print(f"📋 User Pool ID: {user_pool_id}")
    print(f"📋 Client ID: {client_id}")
    print()
    
    jwt_tokens = {}
    
    for user in test_users:
        try:
            print(f"👤 Creating user: {user['email']} ({user['subscription_tier']} tier)")
            
            # Create user in Cognito
            response = cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=user["email"],
                UserAttributes=[
                    {"Name": "email", "Value": user["email"]},
                    {"Name": "email_verified", "Value": "true"},
                    {"Name": "custom:tenant_id", "Value": user["tenant_id"]},
                    {"Name": "custom:subscription_tier", "Value": user["subscription_tier"]}
                ],
                TemporaryPassword=user["password"],
                MessageAction="SUPPRESS"
            )
            
            # Set permanent password
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=user["email"],
                Password=user["password"],
                Permanent=True
            )
            
            # Generate JWT token for testing
            jwt_token = create_jwt_token(user)
            jwt_tokens[f"{user['subscription_tier']}-{user['tenant_id']}"] = jwt_token
            
            print(f"   ✅ Created successfully")
            print(f"   🎫 Tenant: {user['tenant_id']}")
            print(f"   🏷️  Tier: {user['subscription_tier']}")
            print()
            
        except cognito.exceptions.UsernameExistsException:
            print(f"   ⚠️  User already exists, generating JWT token")
            jwt_token = create_jwt_token(user)
            jwt_tokens[f"{user['subscription_tier']}-{user['tenant_id']}"] = jwt_token
            print()
        except Exception as e:
            print(f"   ❌ Error creating user: {str(e)}")
            print()
    
    # Display JWT tokens for testing
    print("🎫 JWT TOKENS FOR TESTING")
    print("=" * 60)
    print("Copy these tokens to test different subscription tiers:")
    print()
    
    for key, token in jwt_tokens.items():
        tier, tenant = key.split('-', 1)
        print(f"🏷️  {tier.upper()} TIER ({tenant}):")
        print(f"   {token}")
        print()
    
    # Display tier limits
    print("📊 SUBSCRIPTION TIER LIMITS")
    print("=" * 60)
    
    tier_info = {
        "basic": {
            "daily_messages": 50,
            "monthly_messages": 1000,
            "max_session_duration": "30 minutes",
            "concurrent_sessions": 1,
            "mcp_server_access": False
        },
        "advanced": {
            "daily_messages": 200,
            "monthly_messages": 5000,
            "max_session_duration": "2 hours",
            "concurrent_sessions": 3,
            "mcp_server_access": True
        },
        "premium": {
            "daily_messages": 1000,
            "monthly_messages": 25000,
            "max_session_duration": "8 hours",
            "concurrent_sessions": 10,
            "mcp_server_access": True
        }
    }
    
    for tier, limits in tier_info.items():
        print(f"🏷️  {tier.upper()} TIER:")
        for key, value in limits.items():
            print(f"   {key}: {value}")
        print()
    
    print("🧪 TESTING INSTRUCTIONS")
    print("=" * 60)
    print("1. Start the application: python run.py")
    print("2. Visit: http://localhost:8000")
    print("3. Paste a JWT token in the 'JWT Token' field")
    print("4. Click 'Set Auth' then 'Create Session'")
    print("5. Test tier limits by sending messages")
    print("6. Try MCP tools with Advanced/Premium tiers")
    print()
    print("🔧 API ENDPOINTS TO TEST:")
    print("   GET /api/tenants/{tenant_id}/subscription - View tier info")
    print("   GET /api/mcp/tools - View available MCP tools")
    print("   POST /api/mcp/tools/{tool_name} - Execute MCP tools")

if __name__ == "__main__":
    main()