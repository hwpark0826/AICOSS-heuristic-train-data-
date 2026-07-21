from pathlib import Path
import shutil
import tempfile
import pytest
from src.label_repository import LabelRepository


def test_labels_are_validated_and_progress_is_tracked() -> None:
    with tempfile.TemporaryDirectory() as directory:
        source = Path("data/runs/run_003")
        run = Path(directory) / "run"
        shutil.copytree(source, run)
        (run / "labels.sqlite").unlink(missing_ok=True)
        repo = LabelRepository(run / "labels.sqlite")
        repo.initialize_from_run(run)
        assert repo.progress("A01") == {"total": 80, "completed": 0, "remaining": 80}
        assert repo.next_assignment("A01")["assignment_id"] == "ASN-0001"
        repo.submit_label("ASN-0001", "A01", "ACCEPTED")
        assert repo.progress("A01") == {"total": 80, "completed": 1, "remaining": 79}
        assert repo.next_assignment("A01")["assignment_id"] == "ASN-0004"
        with pytest.raises(ValueError): repo.submit_label("ASN-0001", "A01", "REJECTED", "TOO_FAR")
        with pytest.raises(ValueError): repo.submit_label("ASN-0004", "A01", "REJECTED", None)
