"""The Router: a Haiku model with one tool whose only job is to pick a specialist."""
from __future__ import annotations

from shared.anthropic_client import get_client
from shared.config import get_settings

from .prompts import ROUTER_PROMPT

VALID_AGENTS = ["billing", "technical", "account", "escalation"]

HANDOFF_TOOL = {
    "name": "handoff",
    "description": "Assign this conversation to exactly one specialist.",
    "input_schema": {
        "type": "object",
        "properties": {
            "agent": {"type": "string", "enum": VALID_AGENTS},
            "reason": {"type": "string", "description": "One short phrase."},
        },
        "required": ["agent"],
    },
}


async def route(message: str, history: list[dict], client=None) -> str:
    client = client or get_client()
    response = await client.messages.create(
        model=get_settings().router_model,
        max_tokens=64,
        system=ROUTER_PROMPT,
        tools=[HANDOFF_TOOL],
        tool_choice={"type": "any"},  # force a tool call, not a chat reply
        messages=history + [{"role": "user", "content": message}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    agent = tool_use.input.get("agent", "escalation")
    return agent if agent in VALID_AGENTS else "escalation"
