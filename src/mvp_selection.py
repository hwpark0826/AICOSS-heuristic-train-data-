"""Objective, reproducible MVP store selection from changing master data."""
from __future__ import annotations
import pandas as pd


EXCLUDED_MVP_CATEGORY_SUBS = {"미용실", "네일샵"}
# These stores are explicitly outside the MVP business scope even though their
# category remains eligible for other future selections.
EXCLUDED_MVP_STORE_IDS = {"S0038", "S0058", "S0060", "S0068"}
# The initial MVP must use this reviewed roster exactly.  A changed master must
# not silently substitute another store for one of these IDs.
MVP_TARGET_STORE_IDS = (
    "S0002", "S0003", "S0005", "S0006", "S0010", "S0012", "S0014", "S0017", "S0018", "S0019",
    "S0020", "S0021", "S0023", "S0024", "S0034", "S0035", "S0036", "S0033", "S0043", "S0044",
    "S0057", "S0042", "S0059", "S0022", "S0062", "S0063", "S0064", "S0070", "S0069", "S0052",
)


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
    if target_count == len(MVP_TARGET_STORE_IDS):
        available_ids = set(stores.store_id)
        unavailable_ids = [store_id for store_id in MVP_TARGET_STORE_IDS if store_id not in available_ids]
        if unavailable_ids:
            raise ValueError(f"Reviewed MVP stores are missing, inactive, or excluded: {', '.join(unavailable_ids)}")
        result = stores.set_index("store_id").loc[list(MVP_TARGET_STORE_IDS)].reset_index()
        result["selection_reason"] = "reviewed fixed MVP roster"
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
