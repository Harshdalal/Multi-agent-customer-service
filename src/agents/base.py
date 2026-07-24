"""The specialist loop every agent shares: stream text, run tools, repeat."""
from __future__ import annotations

from dataclasses import dataclass

from shared.anthropic_client import get_client
from shared.config import get_settings
from shared.models import Chunk

from .tools import execute_tools, find_handoff, tools_for


@dataclass
class Agent:
    name: str
    model: str
    system: str
    max_tokens: int = 1024

    @property
    def tools(self) -> list[dict]:
        return tools_for(self.name)


async def run(agent: Agent, messages: list[dict], client=None):
    """Async-generate Chunks for one customer turn owned by ``agent``."""
    client = client or get_client()
    settings = get_settings()
    work = list(messages)
    cycles = 0

    while True:
        async with client.messages.stream(
            model=agent.model,
            max_tokens=agent.max_tokens,
            system=agent.system,
            tools=agent.tools,
            messages=work,
        ) as stream:
            async for text in stream.text_stream:  # real token streaming
                yield Chunk.text_chunk(text)
            reply = await stream.get_final_message()

        if reply.stop_reason != "tool_use":
            return

        handoff = find_handoff(reply.content)
        if handoff is not None:
            yield Chunk.handoff(context=handoff.get("note", ""), target=handoff.get("target"))
            return

        cycles += 1
        if cycles > settings.max_tool_cycles:
            yield Chunk.handoff(context="tool-cycle limit reached", target="escalation")
            return

        results = await execute_tools(reply.content, agent.name)
        work += [
            {"role": "assistant", "content": reply.content},
            {"role": "user", "content": results},
        ]
