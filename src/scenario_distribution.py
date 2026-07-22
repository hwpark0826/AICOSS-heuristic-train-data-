"""Versioned, run-level probability policy for virtual scenarios."""
from __future__ import annotations

from random import Random

POLICY_VERSION = "v2"


def _bounded_weights(rng: Random, bounds: dict[str, tuple[float, float]]) -> dict[str, float]:
    """Draw a categorical distribution inside inclusive per-category bounds."""
    for _ in range(10_000):
        raw = {key: rng.uniform(low, high) for key, (low, high) in bounds.items()}
        total = sum(raw.values())
        weights = {key: value / total for key, value in raw.items()}
        if all(bounds[key][0] <= weights[key] <= bounds[key][1] for key in weights):
            return weights
    raise ValueError("Could not draw a valid bounded distribution")


def _conditional_budget_weights(rng: Random, ranges: dict[str, tuple[float, float]]) -> dict[str, float]:
    """Draw non-NO_PREFERENCE budget weights and assign the remainder."""
    for _ in range(10_000):
        weights = {key: rng.uniform(low, high) for key, (low, high) in ranges.items()}
        remainder = 1 - sum(weights.values())
        if 0 <= remainder <= 0.40:
            weights["NO_PREFERENCE"] = remainder
            return weights
    raise ValueError("Could not draw a valid conditional budget distribution")


def draw_distribution_policy(seed: int) -> dict[str, object]:
    """Draw one reproducible v1 policy. The returned object is persisted in a run manifest."""
    rng = Random(seed)
    return {
        "version": POLICY_VERSION,
        "parking_preference": {"REQUIRED": rng.uniform(0.10, 0.20), "NO_PREFERENCE": None},
        "hill_preference": {"AVOID": rng.uniform(0.15, 0.35), "NO_PREFERENCE": None},
        "companion_type": _bounded_weights(rng, {
            "FAMILY": (0.15, 0.35), "COUPLE": (0.15, 0.35), "FRIENDS": (0.15, 0.35), "ALONE": (0.15, 0.35),
        }),
        "available_time_code": _bounded_weights(rng, {
            "UNDER_60": (0.15, 0.30), "FROM_60_TO_120": (0.25, 0.40),
            "OVER_120": (0.10, 0.25), "NO_PREFERENCE": (0.20, 0.35),
        }),
        "purpose_code": _bounded_weights(rng, {
            "EAT": (0.10, 0.30), "REST": (0.10, 0.30), "BROWSE": (0.10, 0.30),
            "EXPERIENCE": (0.10, 0.30), "NO_PREFERENCE": (0.10, 0.30),
        }),
        "weekday_share": rng.uniform(0.50, 0.65),
        "time_bucket": _bounded_weights(rng, {
            "MORNING": (0.10, 0.20), "LUNCH": (0.20, 0.35), "AFTERNOON": (0.20, 0.35), "EVENING": (0.25, 0.40),
        }),
        "budget_by_purpose": {
            "EAT": _conditional_budget_weights(rng, {"FREE": (0, 0), "UNDER_10000": (0.10, 0.25), "UNDER_30000": (0.40, 0.60), "UNDER_50000": (0.10, 0.25)}),
            "REST": _conditional_budget_weights(rng, {"FREE": (0, 0.05), "UNDER_10000": (0.25, 0.45), "UNDER_30000": (0.25, 0.45), "UNDER_50000": (0.05, 0.15)}),
            "BROWSE": _conditional_budget_weights(rng, {"FREE": (0.35, 0.60), "UNDER_10000": (0.05, 0.20), "UNDER_30000": (0.05, 0.20), "UNDER_50000": (0, 0.10)}),
            "EXPERIENCE": _conditional_budget_weights(rng, {"FREE": (0.10, 0.30), "UNDER_10000": (0.10, 0.25), "UNDER_30000": (0.25, 0.45), "UNDER_50000": (0.05, 0.20)}),
            "NO_PREFERENCE": _conditional_budget_weights(rng, {"FREE": (0, 0.20), "UNDER_10000": (0.10, 0.30), "UNDER_30000": (0.20, 0.40), "UNDER_50000": (0.05, 0.20)}),
        },
    }


def finalize_binary_weights(policy: dict[str, object]) -> dict[str, object]:
    """Replace binary complements before persisting or sampling."""
    for key in ("parking_preference", "hill_preference"):
        values = policy[key]
        values["NO_PREFERENCE"] = 1 - values[next(code for code in values if code != "NO_PREFERENCE")]
    return policy
