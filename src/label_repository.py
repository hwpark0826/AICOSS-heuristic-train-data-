"""SQLite persistence for immutable run assignments and human labels."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from contextlib import closing
import json
import sqlite3
import pandas as pd

OUTCOMES = {"ACCEPTED", "REJECTED"}
REJECTION_REASONS = {"TOO_FAR", "PRICE_BURDEN", "MISMATCH", "INFO_INSUFFICIENT", "PARKING_TIGHT"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LabelRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize_from_run(self, run_dir: Path) -> None:
        metadata = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        assignments = pd.read_csv(run_dir / "assignments.csv", dtype=str)
        shown = pd.read_csv(run_dir / "shown_store_snapshot.csv", dtype=str).set_index("assignment_id")
        with closing(self.connect()) as con, con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, master_sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS assignments (assignment_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), scenario_id TEXT NOT NULL, annotator_id TEXT NOT NULL, shown_store_id TEXT NOT NULL, snapshot_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS labels (assignment_id TEXT PRIMARY KEY REFERENCES assignments(assignment_id), outcome TEXT NOT NULL CHECK(outcome IN ('ACCEPTED','REJECTED')), reject_reason_code TEXT, status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('COMPLETED','INVALIDATED')), labeled_at TEXT NOT NULL, CHECK((outcome='ACCEPTED' AND reject_reason_code IS NULL) OR (outcome='REJECTED' AND reject_reason_code IS NOT NULL)));
                CREATE TABLE IF NOT EXISTS label_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, assignment_id TEXT NOT NULL REFERENCES assignments(assignment_id), event_type TEXT NOT NULL, event_data TEXT, created_at TEXT NOT NULL);
            """)
            con.execute("INSERT OR IGNORE INTO runs VALUES (?, ?, ?)", (metadata["run_id"], metadata["master_sha256"], _now()))
            for assignment in assignments.itertuples(index=False):
                snapshot = shown.loc[assignment.assignment_id].dropna().to_dict()
                con.execute("INSERT OR IGNORE INTO assignments VALUES (?, ?, ?, ?, ?, ?)", (assignment.assignment_id, metadata["run_id"], assignment.scenario_id, assignment.annotator_id, assignment.shown_store_id, json.dumps(snapshot, ensure_ascii=False)))

    def submit_label(self, assignment_id: str, annotator_id: str, outcome: str, reject_reason_code: str | None = None) -> None:
        if outcome not in OUTCOMES: raise ValueError("Invalid outcome")
        if outcome == "ACCEPTED" and reject_reason_code is not None: raise ValueError("ACCEPTED must not have a rejection reason")
        if outcome == "REJECTED" and reject_reason_code not in REJECTION_REASONS: raise ValueError("REJECTED needs an allowed rejection reason")
        with closing(self.connect()) as con, con:
            assignment = con.execute("SELECT annotator_id FROM assignments WHERE assignment_id=?", (assignment_id,)).fetchone()
            if assignment is None: raise ValueError("Unknown or unexposed assignment")
            if assignment["annotator_id"] != annotator_id: raise ValueError("Assignment belongs to a different annotator")
            if con.execute("SELECT 1 FROM labels WHERE assignment_id=?", (assignment_id,)).fetchone(): raise ValueError("Assignment already labeled")
            con.execute("INSERT INTO labels VALUES (?, ?, ?, 'COMPLETED', ?)", (assignment_id, outcome, reject_reason_code, _now()))
            con.execute("INSERT INTO label_events (assignment_id,event_type,event_data,created_at) VALUES (?, 'LABEL_SUBMITTED', ?, ?)", (assignment_id, json.dumps({"outcome": outcome, "reject_reason_code": reject_reason_code}), _now()))

    def progress(self, annotator_id: str) -> dict[str, int]:
        with closing(self.connect()) as con, con:
            total = con.execute("SELECT COUNT(*) FROM assignments WHERE annotator_id=?", (annotator_id,)).fetchone()[0]
            done = con.execute("SELECT COUNT(*) FROM labels l JOIN assignments a USING(assignment_id) WHERE a.annotator_id=? AND l.status='COMPLETED'", (annotator_id,)).fetchone()[0]
        return {"total": total, "completed": done, "remaining": total - done}

    def next_assignment(self, annotator_id: str) -> dict[str, object] | None:
        with closing(self.connect()) as con:
            row = con.execute("""
                SELECT a.assignment_id, a.scenario_id, a.shown_store_id, a.snapshot_json
                FROM assignments a LEFT JOIN labels l USING(assignment_id)
                WHERE a.annotator_id=? AND l.assignment_id IS NULL
                ORDER BY a.assignment_id LIMIT 1
            """, (annotator_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["snapshot"] = json.loads(result.pop("snapshot_json"))
        return result
