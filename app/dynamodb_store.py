import boto3
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from .models import TenantSession, UsageMetric, SubscriptionTier
import os

class DynamoDBStore:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.sessions_table = self.dynamodb.Table(os.getenv("SESSIONS_TABLE", "tenant-sessions"))
        self.usage_table = self.dynamodb.Table(os.getenv("USAGE_TABLE", "tenant-usage"))
    
    def create_session(self, tenant_id: str, user_id: str, subscription_tier: SubscriptionTier) -> str:
        """Create tier-based session in DynamoDB"""
        session_id = str(uuid.uuid4())
        session_key = f"{tenant_id}-{subscription_tier.value}-{user_id}-{session_id}"
        
        session_item = {
            "session_key": session_key,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "session_id": session_id,
            "subscription_tier": subscription_tier.value,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "message_count": 0,
            "tier_usage_count": 0
        }
        
        self.sessions_table.put_item(Item=session_item)
        return session_id
    
    def get_session(self, tenant_id: str, user_id: str, session_id: str, subscription_tier: SubscriptionTier) -> Optional[Dict]:
        """Get tier-based session from DynamoDB"""
        session_key = f"{tenant_id}-{subscription_tier.value}-{user_id}-{session_id}"
        
        try:
            response = self.sessions_table.get_item(Key={"session_key": session_key})
            return response.get("Item")
        except Exception:
            return None
    
    def update_session_activity(self, tenant_id: str, user_id: str, session_id: str, subscription_tier: SubscriptionTier):
        """Update tier-based session activity in DynamoDB"""
        session_key = f"{tenant_id}-{subscription_tier.value}-{user_id}-{session_id}"
        
        self.sessions_table.update_item(
            Key={"session_key": session_key},
            UpdateExpression="SET last_activity = :la, message_count = message_count + :inc, tier_usage_count = tier_usage_count + :inc",
            ExpressionAttributeValues={
                ":la": datetime.utcnow().isoformat(),
                ":inc": 1
            }
        )
    
    def record_usage_metric(self, metric: UsageMetric):
        """Record usage metric in DynamoDB"""
        usage_item = {
            "tenant_id": metric.tenant_id,
            "timestamp": metric.timestamp.isoformat(),
            "metric_type": metric.metric_type,
            "value": metric.value,
            "session_id": metric.session_id,
            "agent_id": metric.agent_id
        }
        
        self.usage_table.put_item(Item=usage_item)
    
    def get_tenant_usage(self, tenant_id: str) -> Dict:
        """Get usage metrics for tenant from DynamoDB"""
        try:
            response = self.usage_table.query(
                KeyConditionExpression="tenant_id = :tid",
                ExpressionAttributeValues={":tid": tenant_id},
                ScanIndexForward=False,
                Limit=50
            )
            
            metrics = response.get("Items", [])
            
            # Get session count
            sessions_response = self.sessions_table.scan(
                FilterExpression="tenant_id = :tid",
                ExpressionAttributeValues={":tid": tenant_id}
            )
            
            return {
                "tenant_id": tenant_id,
                "total_messages": len(metrics),
                "sessions": len(sessions_response.get("Items", [])),
                "metrics": metrics[:10]  # Last 10 metrics
            }
            
        except Exception as e:
            return {
                "tenant_id": tenant_id,
                "total_messages": 0,
                "sessions": 0,
                "metrics": [],
                "error": str(e)
            }
    
    def get_tenant_sessions(self, tenant_id: str) -> List[Dict]:
        """Get all sessions for tenant from DynamoDB"""
        try:
            response = self.sessions_table.scan(
                FilterExpression="tenant_id = :tid",
                ExpressionAttributeValues={":tid": tenant_id}
            )
            
            return response.get("Items", [])
            
        except Exception:
            return []