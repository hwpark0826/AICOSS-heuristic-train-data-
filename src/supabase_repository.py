"""Central Supabase persistence for the small trusted-team MVP."""
from __future__ import annotations

from typing import Any

from .label_repository import validate_label_payload


class SupabaseLabelRepository:
    def __init__(self, url: str, service_role_key: str, run_id: str) -> None:
        try:
            from supabase import create_client
        except ImportError as error:
            raise RuntimeError("Install the 'supabase' package before using central storage") from error
        self.client = create_client(url, service_role_key)
        self.run_id = run_id

    def _assignments(self, annotator_id: str) -> list[dict[str, Any]]:
        response = self.client.table("assignments").select("assignment_id,scenario_id,shown_store_id,snapshot").eq("run_id", self.run_id).eq("annotator_id", annotator_id).order("assignment_id").execute()
        return response.data or []

    def _completed_ids(self, assignment_ids: list[str]) -> set[str]:
        if not assignment_ids:
            return set()
        response = self.client.table("labels").select("assignment_id").in_("assignment_id", assignment_ids).eq("status", "COMPLETED").execute()
        return {row["assignment_id"] for row in response.data or []}

    def progress(self, annotator_id: str) -> dict[str, int]:
        assignments = self._assignments(annotator_id)
        completed = len(self._completed_ids([row["assignment_id"] for row in assignments]))
        return {"total": len(assignments), "completed": completed, "remaining": len(assignments) - completed}

    def next_assignment(self, annotator_id: str) -> dict[str, object] | None:
        assignments = self._assignments(annotator_id)
        completed = self._completed_ids([row["assignment_id"] for row in assignments])
        for row in assignments:
            if row["assignment_id"] not in completed:
                return {"assignment_id": row["assignment_id"], "scenario_id": row["scenario_id"], "shown_store_id": row["shown_store_id"], "snapshot": row["snapshot"]}
        return None

    def submit_label(self, assignment_id: str, annotator_id: str, outcome: str, reject_reason_code: str | None = None, mismatch_detail_code: str | None = None) -> None:
        validate_label_payload(outcome, reject_reason_code, mismatch_detail_code)
        try:
            self.client.rpc("submit_label", {"p_assignment_id": assignment_id, "p_annotator_id": annotator_id, "p_outcome": outcome, "p_reject_reason_code": reject_reason_code, "p_mismatch_detail_code": mismatch_detail_code}).execute()
        except Exception as error:
            raise ValueError(str(error)) from error
