from pathlib import Path
from src.master_loader import find_master_file, load_master
from src.scenario_generator import assign_balanced, generate_scenarios


def test_assignments_are_balanced_and_split_by_annotator() -> None:
    master = load_master(find_master_file(Path("data/master")))
    scenarios = generate_scenarios(master.tables["ORIGIN"], count=90, seed=7)
    assignments = assign_balanced(master.tables, scenarios, seed=7)
    assert assignments.annotator_id.value_counts().to_dict() == {"A01": 30, "A02": 30, "A03": 30}
    assert assignments.shown_store_id.value_counts().max() - assignments.shown_store_id.value_counts().min() <= 1
