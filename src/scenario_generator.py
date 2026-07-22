"""Virtual scenarios and balanced, objective-only store assignments."""
from __future__ import annotations

from random import Random
import pandas as pd

from .opening_hours import opening_status
from .scenario_distribution import draw_distribution_policy, finalize_binary_weights

ANNOTATORS = ("A01", "A02", "A03")
DAYS = ("\uc6d4", "\ud654", "\uc218", "\ubaa9", "\uae08", "\ud1a0", "\uc77c")


def _weighted_choice(rng: Random, weights: dict[str, float]) -> str:
    codes, values = zip(*weights.items())
    return rng.choices(codes, weights=values, k=1)[0]


def _visit_time(rng: Random, buckets: dict[str, float]) -> str:
    bucket = _weighted_choice(rng, buckets)
    hours = {"MORNING": range(9, 12), "LUNCH": range(12, 15), "AFTERNOON": range(15, 18), "EVENING": range(18, 21)}
    return f"{rng.choice(list(hours[bucket])):02d}:00"


def _day_of_week(rng: Random, weekday_share: float) -> str:
    return rng.choice(DAYS[:5] if rng.random() < weekday_share else DAYS[5:])


def generate_scenarios(origins: pd.DataFrame, count: int = 900, seed: int = 42, distribution_policy: dict[str, object] | None = None) -> pd.DataFrame:
    rng = Random(seed)
    policy = finalize_binary_weights(distribution_policy or draw_distribution_policy(seed))
    rows = []
    for number in range(1, count + 1):
        companion = _weighted_choice(rng, policy["companion_type"])
        gender = rng.choice(["MALE", "FEMALE"]) if companion == "ALONE" else None
        age = rng.choice(["TEENS", "20S", "30S", "40S", "50S", "60_PLUS"]) if companion != "FAMILY" else None
        purpose = _weighted_choice(rng, policy["purpose_code"])
        rows.append({"scenario_id": f"SCN-{number:04d}", "origin_id": rng.choice(origins.origin_id.tolist()), "day_of_week": _day_of_week(rng, policy["weekday_share"]), "visit_time": _visit_time(rng, policy["time_bucket"]), "companion_type": companion, "gender_code": gender, "age_group": age, "available_time_code": _weighted_choice(rng, policy["available_time_code"]), "budget_code": _weighted_choice(rng, policy["budget_by_purpose"][purpose]), "purpose_code": purpose, "atmosphere_code": _weighted_choice(rng, policy["atmosphere_code"]), "hill_preference": _weighted_choice(rng, policy["hill_preference"]), "parking_preference": _weighted_choice(rng, policy["parking_preference"])})
    return pd.DataFrame(rows)


def _definitely_open(hours: pd.DataFrame, store_id: str, day: str, at_time: str) -> bool:
    # UNKNOWN is not a hard filter. Only objectively closed stores are excluded.
    return opening_status(hours, store_id, day, at_time) != "CLOSED"


def _route_meets_hard_constraints(route: pd.Series, scenario: pd.Series) -> bool:
    if scenario.hill_preference == "AVOID" and str(route.get("slope_level", "")).upper() == "STEEP":
        return False
    maximum_walking_minutes = {"UNDER_60": 60, "FROM_60_TO_120": 120}.get(scenario.available_time_code)
    walking_minutes = pd.to_numeric(route.get("estimated_walking_time_min"), errors="coerce")
    return maximum_walking_minutes is None or pd.isna(walking_minutes) or walking_minutes <= maximum_walking_minutes


def _store_meets_hard_constraints(store: pd.Series, scenario: pd.Series) -> bool:
    # Eating is the only purpose with an unambiguous category boundary. Other
    # purposes remain available for human preference learning.
    return scenario.purpose_code != "EAT" or store.category_group == "F&B"


def assign_balanced(master_tables: dict[str, pd.DataFrame], scenarios: pd.DataFrame, seed: int = 42, candidate_store_ids: set[str] | None = None) -> pd.DataFrame:
    stores, origins, routes, hours = (master_tables[x] for x in ("STORE", "ORIGIN", "ROUTE_MATRIX", "STORE_HOUR"))
    active = stores[stores.active_yn == "Y"].set_index("store_id")
    if candidate_store_ids is not None: active = active.loc[active.index.intersection(candidate_store_ids)]
    origin_stores = origins.set_index("origin_id").store_id.to_dict(); exposure = {store_id: 0 for store_id in active.index}; rng = Random(seed); rows = []
    for index, scenario in scenarios.iterrows():
        origin_store = origin_stores[scenario.origin_id]; candidates = []
        for store_id, store in active.iterrows():
            if store_id == origin_store or not _definitely_open(hours, store_id, scenario.day_of_week, scenario.visit_time): continue
            if not _store_meets_hard_constraints(store, scenario): continue
            if scenario.parking_preference == "REQUIRED" and store.get("parking_available") == "N": continue
            if scenario.budget_code == "FREE" and store.category_group == "F&B" and pd.notna(store.get("representative_price_krw")) and store.representative_price_krw > 0: continue
            route_rows = routes[(routes.origin_store_id == origin_store) & (routes.destination_store_id == store_id)]
            if route_rows.empty or not _route_meets_hard_constraints(route_rows.iloc[0], scenario): continue
            candidates.append(store_id)
        if not candidates: raise ValueError(f"No objectively eligible store for {scenario.scenario_id}")
        minimum = min(exposure[x] for x in candidates); chosen = rng.choice([x for x in candidates if exposure[x] == minimum]); exposure[chosen] += 1
        rows.append({"assignment_id": f"ASN-{index + 1:04d}", "scenario_id": scenario.scenario_id, "annotator_id": ANNOTATORS[index % len(ANNOTATORS)], "shown_store_id": chosen, "assignment_policy": "BALANCED_RANDOM"})
    return pd.DataFrame(rows)
