from __future__ import annotations

import math


def is_finite_number(value: object) -> bool:
    if value is None:
        return False
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def safe_optional_float(value: object) -> float | None:
    if not is_finite_number(value):
        return None
    return float(value)  # type: ignore[arg-type]


def safe_unit_score(value: object, default: float = 0.0) -> float:
    if not is_finite_number(value):
        return default
    return float(min(1.0, max(0.0, float(value))))  # type: ignore[arg-type]


def safe_probability(value: object, default: float = 0.5) -> float:
    if not is_finite_number(value):
        return default
    return float(min(1.0, max(0.0, float(value))))  # type: ignore[arg-type]
