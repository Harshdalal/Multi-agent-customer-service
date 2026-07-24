"""The Coordinator: owns state, routes the first turn, honors handoffs.

It is deliberately small. Everything durable lives in the store; the agents are
stateless. The blog describes each specialist as its own Lambda; here they run
in-process behind AGENT_MAP so the reference runs as a single deployable. The
module boundaries mirror that split, so promoting a specialist to its own
function is a wiring change, not a rewrite.
"""
from __future__ import annotations

from agents.base import run
from agents.registry import AGENT_MAP
from router.router import route
from shared.config import get_settings
from shared.models import Chunk
from shared.store import get_store


def _last_user(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            return m["content"]
    return ""


async def handle_message(conv_id: str, message: str, store=None, client=None):
    """Top-level entry: persist the turn, dispatch, persist the reply."""
    store = store or get_store()
    convo = await store.load(conv_id)
    await store.append_turn(conv_id, "user", message)
    convo.history.append({"role": "user", "content": message})

    parts: list[str] = []
    async for chunk in _dispatch(conv_id, convo.history, convo.active_agent, store, client, 0):
        if chunk.kind == "text":
            parts.append(chunk.text)
        yield chunk
    await store.append_turn(conv_id, "assistant", "".join(parts))


async def _dispatch(conv_id, messages, active, store, client, depth):
    settings = get_settings()
    if depth > settings.max_handoff_depth:
        note = "Let me bring in a human teammate to take this from here."
        await store.set_active_agent(conv_id, "escalation")
        yield Chunk.text_chunk(note)
        return

    if not active:
        active = await route(_last_user(messages), messages[:-1], client=client)
    await store.set_active_agent(conv_id, active)

    agent = AGENT_MAP[active]
    async for chunk in run(agent, messages, client=client):
        if chunk.kind == "handoff":                       # specialist bails out
            await store.clear_active(conv_id)
            note = chunk.context or _last_user(messages)
            forwarded = messages + [{"role": "user", "content": f"[handoff] {note}"}]
            async for c in _dispatch(conv_id, forwarded, None, store, client, depth + 1):
                yield c
            return
        yield chunk
