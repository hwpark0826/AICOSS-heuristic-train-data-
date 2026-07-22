"""Objective, reproducible MVP store selection from changing master data."""
from __future__ import annotations
from pathlib import Path
import pandas as pd


EXCLUDED_MVP_CATEGORY_SUBS = {"미용실", "네일샵"}
# These stores are explicitly outside the MVP business scope even though their
# category remains eligible for other future selections.
EXCLUDED_MVP_STORE_IDS = {"S0038", "S0058", "S0060", "S0068"}
MVP_ROSTER_PATH = Path(__file__).resolve().parents[1] / "config" / "mvp_store_roster.csv"
MVP_ROSTER_COLUMNS = {"selection_order", "store_id", "store_name", "enabled", "note"}


def load_mvp_store_roster(path: Path = MVP_ROSTER_PATH) -> pd.DataFrame:
    """Load the reviewed MVP roster; store_id is the only runtime reference key."""
    roster = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing_columns = MVP_ROSTER_COLUMNS - set(roster.columns)
    if missing_columns:
        raise ValueError(f"MVP roster is missing columns: {', '.join(sorted(missing_columns))}")
    roster = roster.loc[roster.enabled.str.upper().eq("Y")].copy()
    if roster.empty:
        raise ValueError("MVP roster has no enabled stores")
    if roster.store_id.duplicated().any():
        raise ValueError("MVP roster has duplicate store_id values")
    roster["selection_order"] = pd.to_numeric(roster.selection_order, errors="raise")
    if roster.selection_order.duplicated().any():
        raise ValueError("MVP roster has duplicate selection_order values")
    return roster.sort_values("selection_order", kind="stable").reset_index(drop=True)


def select_mvp_stores(tables: dict[str, pd.DataFrame], target_count: int = 30) -> pd.DataFrame:
    stores = tables["STORE"].copy()
    known_hours = tables["STORE_HOUR"].dropna(subset=["open_time", "close_time"]).groupby("store_id").size()
    stores = stores[
        (stores.active_yn == "Y")
        & (~stores.category_sub.isin(EXCLUDED_MVP_CATEGORY_SUBS))
        & (~stores.store_id.isin(EXCLUDED_MVP_STORE_IDS))
    ].copy()
    stores["known_hours_days"] = stores.store_id.map(known_hours).fillna(0).astype(int)
    stores["information_completeness"] = stores[["representative_item", "representative_price_krw", "atmosphere", "phone"]].notna().sum(axis=1) + stores.known_hours_days.gt(0).astype(int)
    roster = load_mvp_store_roster()
    roster_ids = tuple(roster.store_id)
    if target_count == len(roster_ids):
        available_ids = set(stores.store_id)
        unavailable_ids = [store_id for store_id in roster_ids if store_id not in available_ids]
        if unavailable_ids:
            raise ValueError(f"Reviewed MVP stores are missing, inactive, or excluded: {', '.join(unavailable_ids)}")
        result = stores.set_index("store_id").loc[list(roster_ids)].reset_index()
        result["selection_reason"] = "reviewed MVP roster config"
        return result
    groups = sorted(stores.category_group.unique())
    quotas = {group: min(len(stores[stores.category_group == group]), target_count // len(groups)) for group in groups}
    while sum(quotas.values()) < min(target_count, len(stores)):
        choices = [group for group in groups if quotas[group] < len(stores[stores.category_group == group])]
        group = min(choices, key=lambda item: (quotas[item], item))
        quotas[group] += 1
    selected = []
    for group in groups:
        frame = stores[stores.category_group == group].sort_values(["information_completeness", "known_hours_days", "store_id"], ascending=[False, False, True])
        buckets = {main: list(part.index) for main, part in frame.groupby("category_main", sort=True)}
        while len([idx for idx in selected if stores.loc[idx, "category_group"] == group]) < quotas[group]:
            for main in sorted(buckets):
                if buckets[main] and len([idx for idx in selected if stores.loc[idx, "category_group"] == group]) < quotas[group]: selected.append(buckets[main].pop(0))
    result = stores.loc[selected].copy()
    result["selection_reason"] = "active store; excluded MVP category/store; balanced category group; objective information completeness"
    return result.sort_values("store_id")
