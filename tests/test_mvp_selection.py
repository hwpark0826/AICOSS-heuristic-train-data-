from pathlib import Path
import pytest
from src.master_loader import find_master_file, load_master
from src.mvp_selection import EXCLUDED_MVP_CATEGORY_SUBS, EXCLUDED_MVP_STORE_IDS, MVP_TARGET_STORE_IDS, select_mvp_stores


def test_mvp_selection_is_diverse_and_has_requested_size() -> None:
    master = load_master(find_master_file(Path("data/master")))
    selected = select_mvp_stores(master.tables, 30)
    assert len(selected) == 30
    assert selected.store_id.is_unique
    assert "미용실" not in set(selected.category_sub)
    assert "네일샵" not in set(selected.category_sub)
    assert not set(selected.store_id).intersection(EXCLUDED_MVP_STORE_IDS)
    assert tuple(selected.store_id) == MVP_TARGET_STORE_IDS
    eligible = master.tables["STORE"].loc[
        ~master.tables["STORE"].category_sub.isin(EXCLUDED_MVP_CATEGORY_SUBS)
        & ~master.tables["STORE"].store_id.isin(EXCLUDED_MVP_STORE_IDS)
    ]
    assert set(selected.category_group) == set(eligible.category_group)


def test_fixed_mvp_roster_fails_when_a_reviewed_store_is_inactive() -> None:
    master = load_master(find_master_file(Path("data/master")))
    tables = dict(master.tables)
    stores = tables["STORE"].copy()
    stores.loc[stores.store_id.eq(MVP_TARGET_STORE_IDS[0]), "active_yn"] = "N"
    tables["STORE"] = stores

    with pytest.raises(ValueError, match=MVP_TARGET_STORE_IDS[0]):
        select_mvp_stores(tables, 30)
