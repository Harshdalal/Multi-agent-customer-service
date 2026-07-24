"""Conversation state. Single-table design keyed on conversation_id.

Two backends: an in-memory store for local runs and tests, and a DynamoDB
store for deployment. Agents are stateless; all durable state lives here.
"""
from __future__ import annotations

import asyncio
import functools
import time

from .config import get_settings
from .models import Conversation


class InMemoryStore:
    def __init__(self):
        self._data: dict[str, Conversation] = {}

    async def load(self, conv_id: str) -> Conversation:
        return self._data.setdefault(conv_id, Conversation(conversation_id=conv_id))

    async def set_active_agent(self, conv_id: str, agent: str) -> None:
        (await self.load(conv_id)).active_agent = agent

    async def clear_active(self, conv_id: str) -> None:
        (await self.load(conv_id)).active_agent = None

    async def append_turn(self, conv_id: str, role: str, content: str) -> None:
        if not content:
            return
        (await self.load(conv_id)).history.append({"role": role, "content": content})


class DynamoDBStore:
    """boto3 is synchronous, so calls are dispatched to a thread pool."""

    TTL_DAYS = 30

    def __init__(self):
        import boto3

        self._table = boto3.resource(
            "dynamodb", region_name=get_settings().region
        ).Table(get_settings().table_name)

    async def _get(self, conv_id: str) -> dict:
        item = await asyncio.to_thread(
            lambda: self._table.get_item(Key={"conversation_id": conv_id}).get("Item")
        )
        return item or {"conversation_id": conv_id, "active_agent": None, "history": []}

    async def load(self, conv_id: str) -> Conversation:
        item = await self._get(conv_id)
        return Conversation(
            conversation_id=conv_id,
            active_agent=item.get("active_agent"),
            history=item.get("history", []),
            metadata=item.get("metadata", {}),
        )

    async def _put(self, item: dict) -> None:
        item["ttl"] = int(time.time()) + self.TTL_DAYS * 86400
        await asyncio.to_thread(lambda: self._table.put_item(Item=item))

    async def set_active_agent(self, conv_id: str, agent: str) -> None:
        item = await self._get(conv_id)
        item["active_agent"] = agent
        await self._put(item)

    async def clear_active(self, conv_id: str) -> None:
        item = await self._get(conv_id)
        item["active_agent"] = None
        await self._put(item)

    async def append_turn(self, conv_id: str, role: str, content: str) -> None:
        if not content:
            return
        item = await self._get(conv_id)
        item.setdefault("history", []).append({"role": role, "content": content})
        await self._put(item)


@functools.lru_cache(maxsize=1)
def get_store():
    if get_settings().store_backend == "dynamodb":
        return DynamoDBStore()
    return InMemoryStore()
