from pathlib import Path
from src.master_loader import find_master_file, load_master
from src.mvp_selection import select_mvp_stores


def test_mvp_selection_is_diverse_and_has_requested_size() -> None:
    master = load_master(find_master_file(Path("data/master")))
    selected = select_mvp_stores(master.tables, 30)
    assert len(selected) == 30
    assert selected.store_id.is_unique
    assert "미용실" not in set(selected.category_sub)
    assert "네일샵" not in set(selected.category_sub)
    assert set(selected.category_group) == set(master.tables["STORE"].category_group)
