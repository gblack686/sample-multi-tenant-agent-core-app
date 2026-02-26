"""DynamoDB put_item with Decimal conversion for metadata records."""

from __future__ import annotations

import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.types import TypeSerializer

logger = logging.getLogger(__name__)

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.environ.get("AWS_REGION_NAME", "us-east-1"),
)


def _convert_floats(obj):
    """Recursively convert floats to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_floats(i) for i in obj]
    return obj


def write_metadata(metadata_item: dict) -> None:
    """Write a metadata record to the DynamoDB table."""
    table_name = os.environ["METADATA_TABLE"]
    table = dynamodb.Table(table_name)

    item = _convert_floats(metadata_item)

    logger.info(
        "Writing metadata for document_id=%s to %s",
        item.get("document_id", "unknown"),
        table_name,
    )

    table.put_item(Item=item)
    logger.info("Successfully wrote metadata for %s", item.get("document_id"))
