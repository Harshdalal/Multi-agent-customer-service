"""Anthropic client factory. Returns a real async client, or an offline mock."""
from __future__ import annotations

import functools
import json
import os

from .config import get_settings


def _load_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    arn = get_settings().anthropic_secret_arn
    if arn:
        import boto3

        sm = boto3.client("secretsmanager", region_name=get_settings().region)
        secret = sm.get_secret_value(SecretId=arn)["SecretString"]
        try:
            return json.loads(secret)["api_key"]
        except (json.JSONDecodeError, KeyError):
            return secret
    raise RuntimeError("No Anthropic API key: set ANTHROPIC_API_KEY or ANTHROPIC_SECRET_ARN.")


@functools.lru_cache(maxsize=1)
def get_client():
    if get_settings().mock:
        from .mock_anthropic import MockAsyncAnthropic

        return MockAsyncAnthropic()
    from anthropic import AsyncAnthropic

    return AsyncAnthropic(api_key=_load_api_key())
