# Evals

Each agent owns its own suite so a regression can be attributed to one place.

- `datasets/routing.jsonl` - labelled routing cases (`message` -> `expected`).
- `run_evals.py` - runs the router over the dataset and reports accuracy and a
  confusion matrix. Exits non-zero below 75% so CI can gate on it.
- `scorers.py` - accuracy and confusion helpers.

```bash
make evals          # offline, deterministic stub
ANTHROPIC_MOCK=0 ANTHROPIC_API_KEY=sk-ant-... python evals/run_evals.py
```

Add specialist-level suites (billing, technical, ...) the same way: a JSONL of
inputs plus expected tool calls or outcomes, and a scorer.
