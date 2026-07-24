"""Push tokens back to the client over the API Gateway WebSocket connection."""
from __future__ import annotations

import json

from .config import get_settings


class ConsoleStreamer:
    """Local streamer: prints tokens to stdout."""

    async def send(self, text: str) -> None:
        print(text, end="", flush=True)

    async def send_final(self, text: str) -> None:
        print()  # newline; the guardrailed text matches what was streamed


class WebSocketStreamer:
    def __init__(self, endpoint_url: str, connection_id: str):
        import boto3

        self._client = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=endpoint_url,
            region_name=get_settings().region,
        )
        self._conn = connection_id

    async def _post(self, payload: dict) -> None:
        import asyncio

        await asyncio.to_thread(
            lambda: self._client.post_to_connection(
                ConnectionId=self._conn, Data=json.dumps(payload).encode()
            )
        )

    async def send(self, text: str) -> None:
        await self._post({"type": "token", "text": text})

    async def send_final(self, text: str) -> None:
        # Authoritative, guardrailed message the client should render as final.
        await self._post({"type": "final", "text": text})
