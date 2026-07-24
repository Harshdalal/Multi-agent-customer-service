"""Runtime configuration, read once from the environment."""
from __future__ import annotations

import functools
import os
from dataclasses import dataclass


def _bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    router_model: str = os.getenv("ROUTER_MODEL", "claude-haiku-4-5-20251001")
    specialist_model: str = os.getenv("SPECIALIST_MODEL", "claude-sonnet-5")
    store_backend: str = os.getenv("STORE_BACKEND", "memory")
    table_name: str = os.getenv("TABLE_NAME", "multi-agent-conversations")
    guardrail_id: str = os.getenv("GUARDRAIL_ID", "")
    guardrail_version: str = os.getenv("GUARDRAIL_VERSION", "DRAFT")
    handoff_queue_url: str = os.getenv("HUMAN_HANDOFF_QUEUE_URL", "")
    transcripts_bucket: str = os.getenv("TRANSCRIPTS_BUCKET", "")
    anthropic_secret_arn: str = os.getenv("ANTHROPIC_SECRET_ARN", "")
    region: str = os.getenv("AWS_REGION", "us-east-1")
    max_tool_cycles: int = int(os.getenv("MAX_TOOL_CYCLES", "6"))
    max_handoff_depth: int = int(os.getenv("MAX_HANDOFF_DEPTH", "4"))
    mock: bool = _bool("ANTHROPIC_MOCK")


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
