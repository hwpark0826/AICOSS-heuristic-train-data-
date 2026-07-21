from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.label_repository import LabelRepository

run_dir = Path("data/runs/run_001")
repository = LabelRepository(run_dir / "labels.sqlite")
repository.initialize_from_run(run_dir)
print(repository.progress("A01"))
