"""The article's platform tier shows SQS (human handoff) and S3 (transcripts).
These tests prove the code paths are wired; in mock mode the AWS calls no-op."""
from agents.tools import execute_tools
from shared.transcripts import archive


class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


async def test_create_ticket_runs_handoff_path():
    block = _Block(type="tool_use", name="create_ticket", id="t1",
                   input={"summary": "angry customer", "priority": "high"})
    results = await execute_tools([block], "escalation")
    assert '"status": "queued"' in results[0]["content"]


async def test_transcript_archive_is_safe_offline():
    # No bucket configured + mock: returns cleanly without touching S3.
    assert await archive("conv-x", [{"role": "user", "content": "hi"}]) is None
