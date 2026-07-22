import pandas as pd

from src.scenario_generator import _route_meets_hard_constraints, _store_meets_hard_constraints


def test_steep_route_is_excluded_when_hills_are_avoided() -> None:
    route = pd.Series({"slope_level": "STEEP", "estimated_walking_time_min": 10})
    scenario = pd.Series({"hill_preference": "AVOID", "available_time_code": "NO_PREFERENCE"})
    assert not _route_meets_hard_constraints(route, scenario)


def test_gentle_route_and_unknown_walk_time_are_not_hard_filtered() -> None:
    route = pd.Series({"slope_level": "GENTLE", "estimated_walking_time_min": None})
    scenario = pd.Series({"hill_preference": "AVOID", "available_time_code": "UNDER_60"})
    assert _route_meets_hard_constraints(route, scenario)


def test_walking_time_over_available_time_is_excluded() -> None:
    route = pd.Series({"slope_level": "FLAT", "estimated_walking_time_min": 61})
    scenario = pd.Series({"hill_preference": "NO_PREFERENCE", "available_time_code": "UNDER_60"})
    assert not _route_meets_hard_constraints(route, scenario)


def test_eating_purpose_excludes_non_fnb_store() -> None:
    scenario = pd.Series({"purpose_code": "EAT"})
    assert _store_meets_hard_constraints(pd.Series({"category_group": "F&B"}), scenario)
    assert not _store_meets_hard_constraints(pd.Series({"category_group": "소매"}), scenario)
