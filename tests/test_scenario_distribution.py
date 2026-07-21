from pathlib import Path

from src.master_loader import find_master_file, load_master
from src.scenario_distribution import draw_distribution_policy, finalize_binary_weights
from src.scenario_generator import generate_scenarios


def test_distribution_policy_is_reproducible_and_bounded() -> None:
    first = finalize_binary_weights(draw_distribution_policy(43))
    second = finalize_binary_weights(draw_distribution_policy(43))
    assert first == second
    assert 0.10 <= first["parking_preference"]["REQUIRED"] <= 0.20
    assert 0.15 <= first["hill_preference"]["AVOID"] <= 0.35
    assert abs(sum(first["atmosphere_code"].values()) - 1) < 1e-12


def test_scenarios_follow_conditional_budget_and_demographics() -> None:
    master = load_master(find_master_file(Path("data/master")))
    origins = master.tables["ORIGIN"].head(3)
    scenarios = generate_scenarios(origins, count=500, seed=43)
    assert not ((scenarios.purpose_code == "EAT") & (scenarios.budget_code == "FREE")).any()
    assert scenarios.loc[scenarios.companion_type == "FAMILY", "age_group"].isna().all()
    assert scenarios.loc[scenarios.companion_type != "FAMILY", "age_group"].notna().all()
    assert scenarios.loc[scenarios.companion_type == "ALONE", "gender_code"].notna().all()
    assert scenarios.loc[scenarios.companion_type != "ALONE", "gender_code"].isna().all()
