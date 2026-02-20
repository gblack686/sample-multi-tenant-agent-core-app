"""Pydantic model for document metadata matching the DynamoDB schema."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata extracted from a government acquisition document."""

    document_id: str = Field(..., description="S3 object key as unique identifier")
    file_name: str
    file_type: str = Field(..., description="Extension: txt, md, pdf, doc, docx")
    file_size_bytes: int = Field(ge=0)
    s3_bucket: str
    s3_key: str

    # Extracted by Gemini
    title: str = ""
    summary: str = ""
    document_type: str = Field(
        default="unknown",
        description="regulation, guidance, template, memo, report, policy, unknown",
    )
    primary_topic: str = Field(
        default="general",
        description="Main acquisition topic: contracting, pricing, compliance, etc.",
    )
    primary_agent: str = Field(
        default="supervisor",
        description="Best-matched EAGLE agent for this document",
    )
    keywords: list[str] = Field(default_factory=list)
    agencies: list[str] = Field(default_factory=list)
    far_references: list[str] = Field(
        default_factory=list, description="FAR/DFARS clause references"
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Gemini extraction confidence"
    )

    # Timestamps
    upload_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_updated: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    extraction_model: str = ""

    def to_dynamo_item(self) -> dict:
        """Convert to DynamoDB-compatible dict with string-typed numerics."""
        data = self.model_dump()
        # DynamoDB stores lists as List type natively via boto3
        # Convert float to string for Decimal compatibility
        data["confidence_score"] = str(data["confidence_score"])
        data["file_size_bytes"] = data["file_size_bytes"]
        return data
