"""Run the routing eval and print accuracy plus a confusion matrix.

Offline by default (ANTHROPIC_MOCK=1). Point it at the real router by exporting
ANTHROPIC_API_KEY and ANTHROPIC_MOCK=0.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from scorers import accuracy, confusion  # noqa: E402

from router.router import route  # noqa: E402

DATASET = pathlib.Path(__file__).resolve().parent / "datasets" / "routing.jsonl"


async def main() -> int:
    rows = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    pairs: list[tuple[str, str]] = []
    for row in rows:
        pred = await route(row["message"], [])
        pairs.append((pred, row["expected"]))

    acc = accuracy(pairs)
    print(f"routing accuracy: {acc:.1%}  ({len(pairs)} cases)\n")
    print("confusion (rows = expected, cols = predicted):")
    for gold, preds in sorted(confusion(pairs).items()):
        cells = ", ".join(f"{p}:{n}" for p, n in sorted(preds.items()))
        print(f"  {gold:11s} -> {cells}")

    # A regression gate you can wire into CI.
    return 0 if acc >= 0.75 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
