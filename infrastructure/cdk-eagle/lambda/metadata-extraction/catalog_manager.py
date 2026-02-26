"""S3 metadata-catalog.json read/update for backup catalog."""

from __future__ import annotations

import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

s3 = boto3.client(
    "s3",
    region_name=os.environ.get("AWS_REGION_NAME", "us-east-1"),
)


def update_catalog(document_id: str, metadata_summary: dict) -> None:
    """Add or update an entry in the metadata catalog JSON on S3."""
    bucket = os.environ["DOCUMENT_BUCKET"]
    catalog_key = os.environ.get("CATALOG_KEY", "metadata/metadata-catalog.json")

    catalog = _read_catalog(bucket, catalog_key)

    catalog[document_id] = {
        "title": metadata_summary.get("title", ""),
        "document_type": metadata_summary.get("document_type", "unknown"),
        "primary_topic": metadata_summary.get("primary_topic", "general"),
        "primary_agent": metadata_summary.get("primary_agent", "supervisor"),
        "file_name": metadata_summary.get("file_name", ""),
        "last_updated": metadata_summary.get("last_updated", ""),
    }

    _write_catalog(bucket, catalog_key, catalog)
    logger.info("Updated catalog with document_id=%s (%d total entries)", document_id, len(catalog))


def _read_catalog(bucket: str, key: str) -> dict:
    """Read the existing catalog from S3, or return empty dict if not found."""
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        logger.info("No existing catalog found, creating new one")
        return {}
    except Exception:
        logger.exception("Failed to read catalog, starting fresh")
        return {}


def _write_catalog(bucket: str, key: str, catalog: dict) -> None:
    """Write the catalog back to S3."""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(catalog, indent=2, default=str).encode("utf-8"),
        ContentType="application/json",
    )
