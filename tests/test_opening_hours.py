import pandas as pd

from src.opening_hours import opening_status


def test_overnight_interval_is_open_on_its_start_day_and_next_day() -> None:
    hours = pd.DataFrame([
        {"store_id": "S0001", "day_of_week": "금", "open_time": "18:00", "close_time": "01:00", "is_closed": "N"},
        {"store_id": "S0001", "day_of_week": "토", "open_time": "18:00", "close_time": "01:00", "is_closed": "N"},
    ])

    assert opening_status(hours, "S0001", "금", "23:00") == "OPEN"
    assert opening_status(hours, "S0001", "토", "00:30") == "OPEN"
    assert opening_status(hours, "S0001", "토", "01:30") == "CLOSED"


def test_previous_day_overnight_interval_overrides_current_day_closure() -> None:
    hours = pd.DataFrame([
        {"store_id": "S0001", "day_of_week": "금", "open_time": "18:00", "close_time": "01:00", "is_closed": "N"},
        {"store_id": "S0001", "day_of_week": "토", "open_time": None, "close_time": None, "is_closed": "Y"},
    ])

    assert opening_status(hours, "S0001", "토", "00:30") == "OPEN"
    assert opening_status(hours, "S0001", "토", "01:30") == "CLOSED"


def test_missing_times_remain_unknown() -> None:
    hours = pd.DataFrame([
        {"store_id": "S0001", "day_of_week": "금", "open_time": None, "close_time": None, "is_closed": "N"},
        {"store_id": "S0001", "day_of_week": "목", "open_time": "09:00", "close_time": "18:00", "is_closed": "N"},
    ])

    assert opening_status(hours, "S0001", "금", "12:00") == "UNKNOWN"
