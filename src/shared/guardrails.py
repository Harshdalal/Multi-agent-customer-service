"""Bedrock Guardrails on outbound text. No-op when unconfigured or mocked."""
from __future__ import annotations

import asyncio

from .config import get_settings


class Guardrails:
    def __init__(self):
        s = get_settings()
        self._enabled = bool(s.guardrail_id) and not s.mock
        self._id = s.guardrail_id
        self._version = s.guardrail_version
        self._client = None
        if self._enabled:
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=s.region)

    async def apply_output(self, text: str) -> str:
        if not self._enabled or not text.strip():
            return text
        resp = await asyncio.to_thread(
            lambda: self._client.apply_guardrail(
                guardrailIdentifier=self._id,
                guardrailVersion=self._version,
                source="OUTPUT",
                content=[{"text": {"text": text}}],
            )
        )
        outputs = resp.get("outputs") or []
        if outputs and outputs[0].get("text"):
            return outputs[0]["text"]
        return text
