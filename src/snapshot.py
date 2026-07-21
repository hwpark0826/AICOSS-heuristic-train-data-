"""Immutable per-run master snapshot creation."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json, shutil
from .master_loader import file_sha256


def create_master_snapshot(source: Path, runs_dir: Path, run_id: str) -> Path:
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    target = run_dir / "master_snapshot.xlsx"
    shutil.copy2(source, target)
    metadata = {"run_id": run_id, "master_version": source.stem, "master_sha256": file_sha256(source), "snapshot_created_at": datetime.now(timezone.utc).isoformat()}
    (run_dir / "master_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
