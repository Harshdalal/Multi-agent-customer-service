"""Small value types shared across the orchestrator and agents."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A single unit streamed out of an agent.

    kind is one of: "text" (customer-visible token), "handoff" (specialist is
    giving the conversation back to the router), or "tool" (diagnostic only).
    """

    kind: str
    text: str = ""
    context: str = ""
    target: str | None = None
    meta: dict = field(default_factory=dict)

    @classmethod
    def text_chunk(cls, text: str) -> Chunk:
        return cls(kind="text", text=text)

    @classmethod
    def handoff(cls, context: str = "", target: str | None = None) -> Chunk:
        return cls(kind="handoff", context=context, target=target)


@dataclass
class Conversation:
    conversation_id: str
    active_agent: str | None = None
    history: list[dict] = field(default_factory=list)  # anthropic messages format
    metadata: dict = field(default_factory=dict)
