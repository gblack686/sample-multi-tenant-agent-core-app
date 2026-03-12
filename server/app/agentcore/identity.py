"""
AgentCore Identity Service — wraps IdentityClient for multi-tenant
auth with per-session IAM scoping.

Complements existing Cognito auth (cognito_auth.py) by adding:
- Per-session token scoping (tenant isolation)
- Workload identity for agent-to-service auth
- OAuth token vault (requires both workload + user identity)

Falls back to existing Cognito auth when AgentCore Identity is unavailable.
"""

import logging
import os
from typing import Any

logger = logging.getLogger("eagle.agentcore_identity")

_REGION = os.getenv("AWS_REGION", "us-east-1")
_IDENTITY_ENABLED = os.getenv("AGENTCORE_IDENTITY_ENABLED", "false").lower() == "true"

# Lazy singleton
_identity_client = None


def _get_identity_client():
    """Lazy-init AgentCore IdentityClient."""
    global _identity_client
    if _identity_client is not None:
        return _identity_client

    if not _IDENTITY_ENABLED:
        logger.info("AgentCore Identity not enabled — using Cognito auth directly")
        return None

    try:
        from bedrock_agentcore.identity import IdentityClient
        _identity_client = IdentityClient(region=_REGION)
        logger.info("AgentCore IdentityClient initialized (region=%s)", _REGION)
        return _identity_client
    except Exception as exc:
        logger.warning("AgentCore Identity unavailable: %s — using Cognito fallback", exc)
        return None


def is_identity_available() -> bool:
    """Check if AgentCore Identity is configured."""
    return _get_identity_client() is not None


def resolve_identity(
    token: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Resolve user identity from token via AgentCore Identity.

    Returns claims dict with tenant_id, user_id, tier, roles.
    Falls back to Cognito JWT validation if Identity is unavailable.
    """
    client = _get_identity_client()

    if client:
        return _agentcore_resolve(client, token, session_id)
    return _cognito_fallback(token)


def _agentcore_resolve(client, token: str, session_id: str | None) -> dict[str, Any]:
    """Resolve identity via AgentCore IdentityClient."""
    try:
        # Validate token and get claims with resource-scoped access
        result = client.validate_token(
            token=token,
            session_id=session_id,
        )

        claims = result.get("claims", {})
        return {
            "user_id": claims.get("sub", claims.get("user_id", "anonymous")),
            "tenant_id": claims.get("custom:tenant_id", claims.get("tenant_id", "default")),
            "tier": claims.get("custom:tier", claims.get("tier", "free")),
            "email": claims.get("email", ""),
            "roles": claims.get("cognito:groups", claims.get("roles", [])),
            "session_scoped": True,
            "source": "agentcore_identity",
        }
    except Exception as exc:
        logger.warning("AgentCore identity resolution failed: %s — Cognito fallback", exc)
        return _cognito_fallback(token)


def _cognito_fallback(token: str) -> dict[str, Any]:
    """Fall back to existing Cognito auth."""
    from app.cognito_auth import extract_user_context

    user_ctx, error = extract_user_context(token)
    if error:
        logger.debug("Cognito fallback auth error: %s", error)

    return {
        "user_id": user_ctx.user_id,
        "tenant_id": user_ctx.tenant_id,
        "tier": user_ctx.tier,
        "email": user_ctx.email or "",
        "roles": user_ctx.roles,
        "session_scoped": False,
        "source": "cognito",
    }


def get_scoped_credentials(
    tenant_id: str,
    user_id: str,
    service: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Get tenant-scoped credentials for an AWS service.

    AgentCore Identity can issue per-session tokens that restrict
    access to tenant-specific resources (S3 prefixes, DDB partitions).
    """
    client = _get_identity_client()
    if not client:
        return {"scoped": False, "message": "AgentCore Identity not available"}

    try:
        result = client.get_session_credentials(
            tenant_id=tenant_id,
            user_id=user_id,
            service=service,
            session_id=session_id,
            resource_indicators=[
                f"arn:aws:s3:::eagle-documents-*/{tenant_id}/*",
                "arn:aws:dynamodb:*:*:table/eagle",
            ],
        )

        return {
            "scoped": True,
            "credentials": result.get("credentials", {}),
            "expires_at": result.get("expiresAt", ""),
            "source": "agentcore_identity",
        }
    except Exception as exc:
        logger.warning("Failed to get scoped credentials: %s", exc)
        return {"scoped": False, "error": str(exc)}
