from pathlib import Path
import tempfile
import pandas as pd
from src.master_loader import find_master_file
from src.run_builder import build_run


def test_run_has_snapshot_and_900_balanced_assignments() -> None:
    with tempfile.TemporaryDirectory() as directory:
        run = build_run(find_master_file(Path("data/master")), Path(directory), "test_run", assignment_count=90, seed=7)
        assignments = pd.read_csv(run / "assignments.csv")
        shown = pd.read_csv(run / "shown_store_snapshot.csv")
        assert (run / "master_snapshot.xlsx").exists()
        assert len(assignments) == len(shown) == 90
        assert assignments.annotator_id.value_counts().to_dict() == {"A01": 30, "A02": 30, "A03": 30}
        assert set(shown.opening_status) <= {"OPEN", "UNKNOWN"}
