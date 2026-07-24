from agents.base import Agent, run
from agents.tools import execute_tools, find_handoff, tools_for


class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Msg:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _Stream:
    def __init__(self, msg):
        self._msg = msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    @property
    def text_stream(self):
        async def gen():
            yield "ok "
        return gen()

    async def get_final_message(self):
        return self._msg


class _Client:
    """Returns a tool_use turn first, then a plain turn."""

    def __init__(self, msgs):
        self._msgs = list(msgs)
        self.messages = self

    def stream(self, **kw):
        return _Stream(self._msgs.pop(0))


def test_every_agent_has_at_most_seven_tools():
    for agent in ["billing", "technical", "account", "escalation"]:
        tools = tools_for(agent)
        assert len(tools) <= 7  # six specialist tools + handoff
        assert any(t["name"] == "handoff_to_router" for t in tools)


def test_find_handoff():
    content = [_Block(type="tool_use", name="handoff_to_router", input={"note": "billing issue"})]
    assert find_handoff(content) == {"note": "billing issue"}


async def test_execute_tools_runs_backends():
    content = [_Block(type="tool_use", name="get_invoice", id="t1", input={"customer_id": "c1"})]
    results = await execute_tools(content, "billing")
    assert results[0]["tool_use_id"] == "t1"
    assert "invoices" in results[0]["content"]


async def test_run_stops_on_handoff():
    handoff_turn = _Msg(
        [_Block(type="tool_use", name="handoff_to_router", id="h1", input={"note": "needs billing"})],
        "tool_use",
    )
    agent = Agent(name="technical", model="m", system="s")
    kinds = [c.kind async for c in run(agent, [{"role": "user", "content": "hi"}], client=_Client([handoff_turn]))]
    assert "handoff" in kinds
