"""Upload an immutable local run snapshot to the MVP central database."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys

import pandas as pd
from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def clean(value: object) -> object:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return value.item() if hasattr(value, "item") else value


def upload(run_dir: Path, url: str, service_role_key: str) -> None:
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assignments = pd.read_csv(run_dir / "assignments.csv", dtype=str)
    shown = pd.read_csv(run_dir / "shown_store_snapshot.csv", dtype=str).set_index("assignment_id")
    client = create_client(url, service_role_key)
    existing = client.table("runs").select("master_sha256").eq("run_id", manifest["run_id"]).execute().data
    if existing and existing[0]["master_sha256"] != manifest["master_sha256"]:
        raise ValueError("A different master snapshot already exists for this run_id")
    client.table("runs").upsert({"run_id": manifest["run_id"], "master_sha256": manifest["master_sha256"], "manifest": manifest}).execute()
    payload = []
    for assignment in assignments.itertuples(index=False):
        snapshot = {key: clean(value) for key, value in shown.loc[assignment.assignment_id].to_dict().items()}
        payload.append({"assignment_id": assignment.assignment_id, "run_id": manifest["run_id"], "scenario_id": assignment.scenario_id, "annotator_id": assignment.annotator_id, "shown_store_id": assignment.shown_store_id, "snapshot": snapshot})
    for start in range(0, len(payload), 100):
        client.table("assignments").upsert(payload[start:start + 100]).execute()


if __name__ == "__main__":
    run_id = os.environ["MUMUT_RUN_ID"]
    url = os.environ["SUPABASE_URL"]
    service_role_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    upload(Path("data/runs") / run_id, url, service_role_key)
    print(f"Uploaded {run_id}")
