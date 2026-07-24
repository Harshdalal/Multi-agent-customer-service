# Multi-agent customer service

A router-and-specialists customer support system built on the **Anthropic API**
and **AWS**. A small Router (Haiku) reads each incoming message and hands the
ticket to one specialist that knows a single job well. The customer sees one
continuous conversation; behind the scenes the baton gets passed.

This is the reference implementation behind the write-up *"When one bot tried to
do everything."* It runs end to end offline with a deterministic stub, and
deploys to AWS with a single SAM template.

```
        message
           |
           v
       +---------+
       | Router  |   Haiku - one tool: pick a specialist
       +----+----+
            |
   +--------+--------+---------+-----------+
   v        v        v         v
+-------+ +---------+ +-------+ +-----------+
|Billing| |Technical| |Account| |Escalation |   specialists (Sonnet / Haiku)
+-------+ +---------+ +-------+ +-----------+

Coordinator owns routing, handoffs, and streaming.
Conversation state lives in DynamoDB; agents are stateless.
```

## Why this shape

- **Specialization over generalization.** Each specialist has a narrow prompt,
  a focused tool belt (six tools max), and its own eval suite.
- **Explicit handoffs, not chained prompts.** A handoff is a structured tool
  call the coordinator can see and audit.
- **State lives in the platform, not the model.** History and the active agent
  live in DynamoDB; agents are stateless.

## Quickstart (offline, no keys)

```bash
python -m venv .venv && source .venv/bin/activate
make dev          # install dev deps
make test         # unit tests (stubbed model)
make evals        # routing accuracy + confusion matrix
make chat         # talk to it in your terminal
```

`make chat` example:

```
you > my card was charged twice this month
bot > Thanks for reaching out. I've looked into this ...
  [owned by: billing]
```

## Run against real Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MOCK=0
python scripts/local_chat.py
```

## Deploy to AWS

Prereqs: AWS credentials and the [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/).

1. Store your Anthropic key in Secrets Manager as JSON `{"api_key": "sk-ant-..."}`
   and note the ARN.
2. (Optional) Create an outbound guardrail: `python scripts/seed_guardrail.py`.
3. Deploy:

```bash
export ANTHROPIC_SECRET_ARN=arn:aws:secretsmanager:...:secret:anthropic-xxxx
export GUARDRAIL_ID=gr-xxxx        # optional
./scripts/deploy.sh
```

The stack prints a `wss://` URL. Send it JSON frames:

```json
{ "action": "message", "conversation_id": "c-123", "message": "hi, I need a refund" }
```

Replies come back as `{"type":"token"}` frames while streaming, then one
`{"type":"final"}` frame with the guardrailed text.

## Layout

```
src/
  shared/         config, models, client factory, store, streaming, guardrails
  router/         the Haiku router + its prompt and one tool
  agents/         base specialist loop, four specialists, tools, registry
  orchestrator/   coordinator (routing + handoffs) and the Lambda handler
tests/            unit tests (offline)
evals/            routing dataset + harness (CI-gated)
scripts/          local_chat, deploy, seed_guardrail
template.yaml     AWS SAM: WebSocket API, DynamoDB, SQS, coordinator Lambda
```

## Notes and trade-offs

- **One Lambda, modular inside.** The write-up describes each specialist as its
  own independently deployable Lambda. Here they run in-process behind
  `AGENT_MAP` so the reference is a single deployable. Module boundaries mirror
  the split, so promoting a specialist to its own function is a wiring change,
  not a rewrite.
- **Tool backends are stubs.** `src/agents/tools.py` returns canned data. Swap
  the `_impl_*` functions for calls to your real billing, identity, and
  knowledge-base systems.
- **Human handoff + transcripts.** Escalation tickets are queued to SQS for
  the human agent team, and completed conversations are archived to S3
  (both no-op locally). This matches the platform tier in the diagram.
- **Loop safety.** A hard cap of six tool cycles per turn, plus a handoff-depth
  cap, keep runaway conversations bounded.
- **Models.** Router and Account run on Haiku; Billing, Technical, and
  Escalation run on Sonnet. Pin these to dated snapshots for production.

## License

MIT. See [LICENSE](LICENSE).
