import jwt
import boto3
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import os
import base64
import json
from app.models import SubscriptionTier

security = HTTPBearer()

class CognitoAuth:
    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp')
        self.user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        self.client_id = os.getenv("COGNITO_CLIENT_ID")
    
    def verify_token(self, token: str) -> Dict:
        """Verify Cognito JWT token and extract tenant context"""
        try:
            # Decode JWT token without verification (for development)
            # In production, you should verify the signature with Cognito's public keys
            parts = token.split('.')
            if len(parts) != 3:
                raise HTTPException(status_code=401, detail="Invalid token format")
            
            # Decode payload
            payload_encoded = parts[1]
            # Add padding if needed
            payload_encoded += '=' * (4 - len(payload_encoded) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_encoded)
            payload = json.loads(payload_bytes)
            
            # Extract tenant_id and subscription_tier from custom attributes
            tenant_id = payload.get("custom:tenant_id")
            subscription_tier = payload.get("custom:subscription_tier", "basic")
            
            if not tenant_id:
                raise HTTPException(status_code=403, detail="No tenant ID found in token")
            
            return {
                "user_id": payload.get("sub"),
                "tenant_id": tenant_id,
                "subscription_tier": SubscriptionTier(subscription_tier),
                "email": payload.get("email"),
                "username": payload.get("cognito:username", payload.get("email"))
            }
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

auth_service = CognitoAuth()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated user with tenant context"""
    return auth_service.verify_token(credentials.credentials)