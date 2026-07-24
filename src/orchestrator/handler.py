"""AWS Lambda entry point for the API Gateway WebSocket API.

Tokens stream to the client immediately for latency. The assembled reply is then
run through Bedrock Guardrails once and sent as an authoritative ``final`` event.
"""
from __future__ import annotations

import asyncio
import json

from shared.guardrails import Guardrails
from shared.store import get_store
from shared.streaming import WebSocketStreamer
from shared.transcripts import archive

from .coordinator import handle_message


def lambda_handler(event, context):
    ctx = event.get("requestContext", {})
    route_key = ctx.get("routeKey")
    connection_id = ctx.get("connectionId")

    if route_key in ("$connect", "$disconnect"):
        return {"statusCode": 200}

    body = json.loads(event.get("body") or "{}")
    message = body.get("message", "")
    conversation_id = body.get("conversation_id") or connection_id
    endpoint = f"https://{ctx.get('domainName')}/{ctx.get('stage')}"

    if not message:
        return {"statusCode": 400, "body": "message is required"}

    streamer = WebSocketStreamer(endpoint, connection_id)
    asyncio.run(_run(conversation_id, message, streamer))
    return {"statusCode": 200}


async def _run(conversation_id, message, streamer):
    guardrails = Guardrails()
    parts: list[str] = []
    async for chunk in handle_message(conversation_id, message):
        if chunk.kind == "text":
            parts.append(chunk.text)
            await streamer.send(chunk.text)
    final = await guardrails.apply_output("".join(parts))
    await streamer.send_final(final)

    convo = await get_store().load(conversation_id)
    await archive(conversation_id, convo.history)
