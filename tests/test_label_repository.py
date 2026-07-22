import json
from pathlib import Path
import pandas as pd
import pytest
from src.label_repository import LabelRepository


def test_labels_are_validated_and_progress_is_tracked(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "run_manifest.json").write_text(
        json.dumps({"run_id": "test_run", "master_sha256": "test_sha"}), encoding="utf-8"
    )
    pd.DataFrame([
        {"assignment_id": "ASN-0001", "scenario_id": "SCN-0001", "annotator_id": "A01", "shown_store_id": "S0001"},
        {"assignment_id": "ASN-0004", "scenario_id": "SCN-0002", "annotator_id": "A01", "shown_store_id": "S0002"},
        {"assignment_id": "ASN-0007", "scenario_id": "SCN-0003", "annotator_id": "A01", "shown_store_id": "S0003"},
    ]).to_csv(run / "assignments.csv", index=False)
    pd.DataFrame([
        {"assignment_id": "ASN-0001", "store_name": "Test store 1"},
        {"assignment_id": "ASN-0004", "store_name": "Test store 2"},
        {"assignment_id": "ASN-0007", "store_name": "Test store 3"},
    ]).to_csv(run / "shown_store_snapshot.csv", index=False)

    repo = LabelRepository(run / "labels.sqlite")
    repo.initialize_from_run(run)
    assert repo.progress("A01") == {"total": 3, "completed": 0, "remaining": 3}
    assert repo.next_assignment("A01")["assignment_id"] == "ASN-0001"
    repo.submit_label("ASN-0001", "A01", "ACCEPTED")
    assert repo.progress("A01") == {"total": 3, "completed": 1, "remaining": 2}
    assert repo.next_assignment("A01")["assignment_id"] == "ASN-0004"
    with pytest.raises(ValueError): repo.submit_label("ASN-0001", "A01", "REJECTED", "TOO_FAR")
    with pytest.raises(ValueError): repo.submit_label("ASN-0004", "A01", "REJECTED", None)
    with pytest.raises(ValueError): repo.submit_label("ASN-0004", "A01", "REJECTED", "MISMATCH")
    repo.submit_label("ASN-0004", "A01", "REJECTED", "MISMATCH", "HILL_MISMATCH")
    repo.submit_label("ASN-0007", "A01", "REJECTED", "LOW_APPEAL")
