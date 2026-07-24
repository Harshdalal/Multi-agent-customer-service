import pytest

from router.router import HANDOFF_TOOL, VALID_AGENTS, route


def test_handoff_tool_is_well_formed():
    assert HANDOFF_TOOL["name"] == "handoff"
    assert HANDOFF_TOOL["input_schema"]["properties"]["agent"]["enum"] == VALID_AGENTS


@pytest.mark.parametrize(
    "message,expected",
    [
        ("my card was charged twice this month", "billing"),
        ("I keep getting a 500 error from your api", "technical"),
        ("I need to update my email address and reset 2fa", "account"),
        ("this is unacceptable, get me a human supervisor", "escalation"),
    ],
)
async def test_route_classifies(message, expected):
    assert await route(message, []) == expected
