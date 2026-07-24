"""Create a minimal Bedrock Guardrail for outbound PII masking. Prints its id.

    python scripts/seed_guardrail.py --region us-east-1
"""
from __future__ import annotations

import argparse

import boto3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--name", default="cs-outbound")
    args = ap.parse_args()

    client = boto3.client("bedrock", region_name=args.region)
    resp = client.create_guardrail(
        name=args.name,
        description="Outbound PII masking for customer support replies.",
        blockedInputMessaging="Blocked.",
        blockedOutputsMessaging="[redacted]",
        sensitiveInformationPolicyConfig={
            "piiEntitiesConfig": [
                {"type": "EMAIL", "action": "ANONYMIZE"},
                {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "ANONYMIZE"},
                {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
            ]
        },
    )
    print("GuardrailId:", resp["guardrailId"])
    print("Version    :", resp.get("version", "DRAFT"))


if __name__ == "__main__":
    main()
