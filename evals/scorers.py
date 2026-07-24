"""Scoring helpers for the routing eval."""
from __future__ import annotations

from collections import defaultdict


def accuracy(pairs: list[tuple[str, str]]) -> float:
    if not pairs:
        return 0.0
    correct = sum(1 for pred, gold in pairs if pred == gold)
    return correct / len(pairs)


def confusion(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pred, gold in pairs:
        matrix[gold][pred] += 1
    return {g: dict(row) for g, row in matrix.items()}
