#!/usr/bin/env bash
# Build and deploy the stack. Requires the AWS SAM CLI and credentials.
set -euo pipefail

: "${ANTHROPIC_SECRET_ARN:?Set ANTHROPIC_SECRET_ARN to your Secrets Manager ARN}"

echo "1/2  Building..."
sam build

echo "2/2  Deploying..."
sam deploy \
  --parameter-overrides "AnthropicSecretArn=${ANTHROPIC_SECRET_ARN} GuardrailId=${GUARDRAIL_ID:-}" \
  --no-confirm-changeset

echo "Done. The WebSocket URL is in the stack outputs above."
