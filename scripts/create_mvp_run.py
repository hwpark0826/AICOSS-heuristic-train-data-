"""Create one immutable local MVP labeling run from the current master workbook."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.label_repository import LabelRepository
from src.master_loader import find_master_file, load_master
from src.master_validator import validate_master
from src.run_builder import build_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="New immutable run ID, e.g. run_005")
    parser.add_argument("--seed", required=True, type=int, help="Random seed recorded in the run manifest")
    parser.add_argument("--assignment-count", type=int, default=240)
    parser.add_argument("--mvp-store-count", type=int, default=30)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("--run-id may contain only letters, numbers, _ and -")
    if args.assignment_count <= 0 or args.assignment_count % 3:
        parser.error("--assignment-count must be a positive multiple of 3")
    return args


def main() -> Path:
    args = parse_args()
    source = find_master_file(Path("data/master"))
    validation = validate_master(load_master(source))
    if validation.errors:
        raise ValueError(f"Master validation failed: {'; '.join(validation.errors)}")
    run = build_run(
        source,
        Path("data/runs"),
        args.run_id,
        assignment_count=args.assignment_count,
        seed=args.seed,
        mvp_store_count=args.mvp_store_count,
    )
    LabelRepository(run / "labels.sqlite").initialize_from_run(run)
    print(run)
    return run


if __name__ == "__main__":
    main()
