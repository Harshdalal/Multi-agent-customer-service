"""A tiny offline stand-in for the Anthropic async client.

It implements just enough of ``messages.create`` and ``messages.stream`` to run
the whole system deterministically without network access. Enabled with
ANTHROPIC_MOCK=1. Never used in production.
"""
from __future__ import annotations

# Keyword hints let the mock router return plausible classifications so the eval
# harness and local chat produce sensible output offline.
KEYWORDS = {
    "billing": ["refund", "charge", "charged", "invoice", "payment", "billing",
                "card", "subscription", "price", "overcharge", "receipt"],
    "technical": ["error", "bug", "not working", "crash", "api", "integration",
                  "slow", "500", "timeout", "connect", "install", "outage"],
    "account": ["password", "profile", "email address", "username", "2fa",
                "login", "sign in", "access", "deactivate", "update my"],
    "escalation": ["manager", "lawsuit", "angry", "unacceptable", "human",
                   "supervisor", "cancel everything", "furious"],
}


def classify(text: str) -> str:
    t = text.lower()
    best, score = "technical", 0
    for agent, words in KEYWORDS.items():
        hits = sum(1 for w in words if w in t)
        if hits > score:
            best, score = agent, hits
    return best


class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Message:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _MockStream:
    def __init__(self, reply: str):
        self._reply = reply

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def gen():
            for word in self._reply.split(" "):
                yield word + " "
        return gen()

    async def get_final_message(self):
        return _Message([_Block(type="text", text=self._reply)], "end_turn")


class _Messages:
    async def create(self, **kwargs):
        # Router path: forced tool call that names an agent.
        last_user = ""
        for m in kwargs.get("messages", []):
            if m.get("role") == "user":
                content = m["content"]
                last_user = content if isinstance(content, str) else str(content)
        agent = classify(last_user)
        tool = _Block(type="tool_use", name="handoff", input={"agent": agent})
        return _Message([tool], "tool_use")

    def stream(self, **kwargs):
        reply = ("Thanks for reaching out. I've looked into this and here's what "
                 "I found, along with the next step I'd recommend.")
        return _MockStream(reply)


class MockAsyncAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = _Messages()
