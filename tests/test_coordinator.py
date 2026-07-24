from agents.registry import AGENT_MAP
from orchestrator.coordinator import handle_message
from shared.store import InMemoryStore


async def test_flow_routes_and_persists():
    store = InMemoryStore()
    chunks = [c async for c in handle_message("conv1", "please refund my duplicate charge", store=store)]
    assert any(c.kind == "text" for c in chunks)

    convo = await store.load("conv1")
    assert convo.active_agent == "billing"
    roles = [m["role"] for m in convo.history]
    assert roles[0] == "user" and "assistant" in roles


async def test_active_agent_is_sticky():
    store = InMemoryStore()
    await store.set_active_agent("conv2", "technical")
    [c async for c in handle_message("conv2", "still broken", store=store)]
    convo = await store.load("conv2")
    # stays with technical without re-consulting the router
    assert convo.active_agent == "technical"


def test_registry_has_four_specialists():
    assert set(AGENT_MAP) == {"billing", "technical", "account", "escalation"}
