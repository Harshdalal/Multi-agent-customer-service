"""Publish asynchronous human-handoff messages to SQS. No-op when unconfigured."""
from __future__ import annotations

import asyncio
import json

from .config import get_settings


async def enqueue(payload: dict) -> None:
    s = get_settings()
    if s.mock or not s.handoff_queue_url:
        return
    import boto3

    sqs = boto3.client("sqs", region_name=s.region)
    await asyncio.to_thread(
        lambda: sqs.send_message(
            QueueUrl=s.handoff_queue_url, MessageBody=json.dumps(payload)
        )
    )
