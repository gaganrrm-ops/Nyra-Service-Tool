"""ITIL priority = f(impact, urgency). Tenant-overridable; every override is audited with a reason."""

from __future__ import annotations

IMPACT_LABELS = {1: "High", 2: "Medium", 3: "Low"}
URGENCY_LABELS = {1: "High", 2: "Medium", 3: "Low"}
PRIORITY_LABELS = {1: "P1 - Critical", 2: "P2 - High", 3: "P3 - Medium", 4: "P4 - Low", 5: "P5 - Planning"}

# Standard ITIL matrix. rows = impact (1 high .. 3 low), cols = urgency (1 high .. 3 low)
_MATRIX = {
    (1, 1): 1, (1, 2): 2, (1, 3): 3,
    (2, 1): 2, (2, 2): 3, (2, 3): 4,
    (3, 1): 3, (3, 2): 4, (3, 3): 5,
}


def calculate(impact: int, urgency: int, matrix: dict[tuple[int, int], int] | None = None) -> int:
    if impact not in (1, 2, 3) or urgency not in (1, 2, 3):
        raise ValueError("impact and urgency must be 1, 2 or 3")
    return (matrix or _MATRIX)[(impact, urgency)]


def label(priority: int) -> str:
    return PRIORITY_LABELS.get(priority, f"P{priority}")


def matrix_as_table() -> list[dict]:
    return [
        {"impact": i, "impact_label": IMPACT_LABELS[i], "urgency": u, "urgency_label": URGENCY_LABELS[u], "priority": p}
        for (i, u), p in sorted(_MATRIX.items())
    ]
