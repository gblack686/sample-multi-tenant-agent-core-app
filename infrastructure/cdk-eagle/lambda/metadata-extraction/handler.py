"""Lambda entry point — iterates S3 records, orchestrates metadata extraction pipeline."""

from __future__ import annotations

import logging
import os
import urllib.parse
from datetime import datetime, timezone

import boto3

from catalog_manager import update_catalog
from dynamo_writer import write_metadata
from extractor import extract_metadata
from file_processors import extract_text
from models import DocumentMetadata

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client(
    "s3",
    region_name=os.environ.get("AWS_REGION_NAME", "us-east-1"),
)


def lambda_handler(event, context):
    """Process S3 ObjectCreated events and extract document metadata."""
    records = event.get("Records", [])
    logger.info("Processing %d S3 event record(s)", len(records))

    results = []

    for record in records:
        try:
            bucket = record["s3"]["bucket"]["name"]
            key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
            size = record["s3"]["object"].get("size", 0)

            logger.info("Processing s3://%s/%s (%d bytes)", bucket, key, size)

            # Determine file type from extension
            file_name = key.split("/")[-1]
            file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

            if file_ext not in ("txt", "md", "pdf", "doc", "docx"):
                logger.warning("Skipping unsupported file type: %s", file_ext)
                continue

            # Download document from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            body_bytes = response["Body"].read()

            # Extract text content
            text = extract_text(body_bytes, file_ext)
            if not text.strip():
                logger.warning("No text extracted from %s, using filename as metadata", key)

            # Call Gemini via Bedrock for metadata extraction
            extracted = extract_metadata(text, file_name) if text.strip() else {}

            # Build metadata model
            now = datetime.now(timezone.utc).isoformat()
            metadata = DocumentMetadata(
                document_id=key,
                file_name=file_name,
                file_type=file_ext,
                file_size_bytes=size,
                s3_bucket=bucket,
                s3_key=key,
                title=extracted.get("title", file_name),
                summary=extracted.get("summary", ""),
                document_type=extracted.get("document_type", "unknown"),
                primary_topic=extracted.get("primary_topic", "general"),
                primary_agent=extracted.get("primary_agent", "supervisor"),
                keywords=extracted.get("keywords", []),
                agencies=extracted.get("agencies", []),
                far_references=extracted.get("far_references", []),
                confidence_score=float(extracted.get("confidence_score", 0.0)),
                upload_date=now,
                last_updated=now,
                extraction_model=os.environ.get("BEDROCK_MODEL_ID", ""),
            )

            # Write to DynamoDB
            write_metadata(metadata.to_dynamo_item())

            # Update S3 catalog
            update_catalog(key, metadata.model_dump())

            results.append({"document_id": key, "status": "success"})
            logger.info("Successfully processed %s", key)

        except Exception:
            logger.exception("Failed to process record: %s", record)
            results.append({
                "document_id": record.get("s3", {}).get("object", {}).get("key", "unknown"),
                "status": "error",
            })

    return {
        "statusCode": 200,
        "body": {"processed": len(results), "results": results},
    }
