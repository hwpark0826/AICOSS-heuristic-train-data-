"""Objective, reproducible MVP store selection from changing master data."""
from __future__ import annotations
import pandas as pd


EXCLUDED_MVP_CATEGORY_SUBS = {"미용실", "네일샵"}
# These stores are explicitly outside the MVP business scope even though their
# category remains eligible for other future selections.
EXCLUDED_MVP_STORE_IDS = {"S0038", "S0058", "S0060", "S0068"}
# Keep this explicit business decision separate from automatic category balancing:
# the renovation-driven removal of S0060 is replaced with a restaurant.
MVP_STORE_SUBSTITUTIONS = {"S0056": "S0022"}


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
    for outgoing_store_id, incoming_store_id in MVP_STORE_SUBSTITUTIONS.items():
        if outgoing_store_id not in set(result.store_id) or incoming_store_id in set(result.store_id):
            continue
        incoming = stores.loc[stores.store_id.eq(incoming_store_id)].copy()
        if incoming.empty:
            continue
        result = result.loc[~result.store_id.eq(outgoing_store_id)]
        incoming["selection_reason"] = f"manual MVP substitution for {outgoing_store_id}"
        result = pd.concat([result, incoming], ignore_index=True)
    return result.sort_values("store_id")
