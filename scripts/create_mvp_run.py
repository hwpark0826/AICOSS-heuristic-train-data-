from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.master_loader import find_master_file
from src.run_builder import build_run
from src.label_repository import LabelRepository

run = build_run(find_master_file(Path("data/master")), Path("data/runs"), "run_004", assignment_count=240, seed=43, mvp_store_count=30)
LabelRepository(run / "labels.sqlite").initialize_from_run(run)
print(run)
