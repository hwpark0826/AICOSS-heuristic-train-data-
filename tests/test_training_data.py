from pathlib import Path

import pandas as pd


def test_human_training_export_reclassifies_atmosphere_mismatch_as_low_appeal() -> None:
    labels = pd.read_csv(Path("data/training/heuristic selection data.csv"))
    assert len(labels) == 240
    assert "store_atmosphere" in labels.columns
    assert not (
        (labels["reject_reason_code"] == "MISMATCH")
        & (labels["mismatch_detail_code"] == "ATMOSPHERE_MISMATCH")
    ).any()
    assert (labels["reject_reason_code"] == "LOW_APPEAL").sum() >= 8
