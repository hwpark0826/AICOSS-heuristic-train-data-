from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.master_loader import find_master_file
from src.run_builder import build_run

if __name__ == "__main__":
    source = find_master_file(Path("data/master"))
    print(build_run(source, Path("data/runs"), "run_001"))
