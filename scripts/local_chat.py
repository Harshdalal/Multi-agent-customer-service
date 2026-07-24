"""Chat with the system locally, no AWS required.

Uses the in-memory store and streams tokens to your terminal. Falls back to the
offline stub if no ANTHROPIC_API_KEY is set.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import sys
import uuid

if not os.getenv("ANTHROPIC_API_KEY") and "ANTHROPIC_MOCK" not in os.environ:
    os.environ["ANTHROPIC_MOCK"] = "1"
os.environ.setdefault("STORE_BACKEND", "memory")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from orchestrator.coordinator import handle_message  # noqa: E402
from shared.store import InMemoryStore  # noqa: E402


async def main():
    store = InMemoryStore()
    conv_id = str(uuid.uuid4())[:8]
    print(f"conversation #{conv_id}  (Ctrl-C to quit)\n")
    while True:
        try:
            message = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not message:
            continue
        print("bot > ", end="", flush=True)
        async for chunk in handle_message(conv_id, message, store=store):
            if chunk.kind == "text":
                print(chunk.text, end="", flush=True)
            elif chunk.kind == "handoff":
                print(f"\n  (handoff: {chunk.context})\n  bot > ", end="", flush=True)
        convo = await store.load(conv_id)
        print(f"\n  [owned by: {convo.active_agent}]\n")


if __name__ == "__main__":
    asyncio.run(main())
