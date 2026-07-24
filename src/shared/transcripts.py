"""Archive completed conversations to S3. No-op when unconfigured or mocked."""
from __future__ import annotations

import asyncio
import json
import time

from .config import get_settings


async def archive(conversation_id: str, history: list[dict]) -> None:
    s = get_settings()
    if s.mock or not s.transcripts_bucket or not history:
        return
    import boto3

    s3 = boto3.client("s3", region_name=s.region)
    key = f"conversations/{conversation_id}/{int(time.time())}.json"
    body = json.dumps({"conversation_id": conversation_id, "history": history}).encode()
    await asyncio.to_thread(
        lambda: s3.put_object(
            Bucket=s.transcripts_bucket, Key=key, Body=body,
            ContentType="application/json",
        )
    )
