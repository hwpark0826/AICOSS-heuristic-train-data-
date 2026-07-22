"""Build a reproducible virtual-labeling run from an immutable master snapshot."""
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from .master_loader import file_sha256, load_master
from .opening_hours import opening_status
from .scenario_generator import assign_balanced, generate_scenarios
from .scenario_distribution import draw_distribution_policy, finalize_binary_weights
from .snapshot import create_master_snapshot
from .mvp_selection import select_mvp_stores


def build_run(source_master: Path, runs_dir: Path, run_id: str, assignment_count: int = 900, seed: int = 42, mvp_store_count: int | None = None) -> Path:
    snapshot_path = create_master_snapshot(source_master, runs_dir, run_id)
    master = load_master(snapshot_path)
    selected = select_mvp_stores(master.tables, mvp_store_count) if mvp_store_count else master.tables["STORE"]
    candidate_ids = set(selected.store_id)
    distribution_policy = finalize_binary_weights(draw_distribution_policy(seed))
    scenarios = generate_scenarios(master.tables["ORIGIN"][master.tables["ORIGIN"].store_id.isin(candidate_ids)], count=assignment_count, seed=seed, distribution_policy=distribution_policy)
    assignments = assign_balanced(master.tables, scenarios, seed=seed, candidate_store_ids=candidate_ids)
    store = master.tables["STORE"].copy()
    route = master.tables["ROUTE_MATRIX"].copy()
    origin = master.tables["ORIGIN"][["origin_id", "store_id"]].rename(columns={"store_id": "origin_store_id"})
    shown = assignments.merge(scenarios, on="scenario_id", validate="one_to_one")
    shown = shown.merge(origin, on="origin_id", validate="many_to_one")
    shown = shown.merge(route, left_on=["origin_store_id", "shown_store_id"], right_on=["origin_store_id", "destination_store_id"], validate="many_to_one")
    shown = shown.merge(store, left_on="shown_store_id", right_on="store_id", suffixes=("", "_store"), validate="many_to_one")
    hours = master.tables["STORE_HOUR"]
    shown["opening_status"] = shown.apply(lambda row: opening_status(hours, row.shown_store_id, row.day_of_week, row.visit_time), axis=1)
    shown["parking_status"] = shown["parking_available"].fillna("UNKNOWN")
    shown["price_status"] = shown["representative_price_krw"].notna().map({True: "KNOWN", False: "UNKNOWN"})
    shown["atmosphere_display"] = shown["atmosphere"].fillna("UNKNOWN")
    run_dir = snapshot_path.parent
    scenarios.to_csv(run_dir / "scenarios.csv", index=False, encoding="utf-8-sig")
    selected.to_csv(run_dir / "mvp_store_selection.csv", index=False, encoding="utf-8-sig")
    assignments.to_csv(run_dir / "assignments.csv", index=False, encoding="utf-8-sig")
    shown.to_csv(run_dir / "shown_store_snapshot.csv", index=False, encoding="utf-8-sig")
    manifest = {"run_id": run_id, "master_sha256": master.sha256, "seed": seed, "scenario_count": len(scenarios), "assignment_count": len(assignments), "mvp_store_count": len(selected), "annotator_counts": assignments.annotator_id.value_counts().sort_index().to_dict(), "distribution_policy": distribution_policy, "generated_counts": {column: scenarios[column].fillna("NONE").value_counts().sort_index().to_dict() for column in ["day_of_week", "visit_time", "companion_type", "available_time_code", "budget_code", "purpose_code", "hill_preference", "parking_preference"]}}
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_dir
