from pathlib import Path
from src.master_loader import find_master_file, load_master
from src.master_validator import validate_master


def test_current_master_passes_integrity_checks() -> None:
    master = load_master(find_master_file(Path("data/master")))
    report = validate_master(master)
    assert report.ok, report.errors
