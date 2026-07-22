"""Opening-hour evaluation, including operating intervals that cross midnight."""
from __future__ import annotations

from datetime import datetime, time
from typing import Any
import pandas as pd


WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


def _time_code(value: Any) -> str | None:
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        value = value.time()
    if isinstance(value, time):
        return f"{value.hour:02d}:{value.minute:02d}"
    text = str(value).strip()
    if " " in text:
        text = text.rsplit(" ", 1)[-1]
    parts = text.split(":")
    if len(parts) < 2:
        return None
    try:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    except ValueError:
        return None


def _row_for(hours: pd.DataFrame, store_id: str, day: str) -> pd.Series | None:
    rows = hours[(hours.store_id == store_id) & (hours.day_of_week == day)]
    return None if rows.empty else rows.iloc[0]


def _is_open_from_current_day(row: pd.Series | None, at_time: str) -> bool | None:
    """Return current-day interval status, or None when its times are unknown."""
    if row is None:
        return None
    if row.is_closed == "Y":
        return False
    open_time, close_time = _time_code(row.open_time), _time_code(row.close_time)
    if open_time is None or close_time is None:
        return None
    if open_time <= close_time:
        return open_time <= at_time <= close_time
    # An overnight interval starts this day. Its after-midnight part is checked
    # from the previous day's row, so a future evening interval never opens now.
    return at_time >= open_time


def _is_open_from_previous_day(row: pd.Series | None, at_time: str) -> bool | None:
    """Return whether a previous-day overnight interval continues into now."""
    if row is None:
        return None
    if row.is_closed == "Y":
        return False
    open_time, close_time = _time_code(row.open_time), _time_code(row.close_time)
    if open_time is None or close_time is None:
        return None
    return open_time > close_time and at_time <= close_time


def opening_status(hours: pd.DataFrame, store_id: str, day: str, at_time: str) -> str:
    """Return OPEN, CLOSED, or UNKNOWN for a visit time in local weekday context."""
    visit_time = _time_code(at_time)
    if visit_time is None or day not in WEEKDAYS:
        return "UNKNOWN"
    current = _is_open_from_current_day(_row_for(hours, store_id, day), visit_time)
    previous_day = WEEKDAYS[(WEEKDAYS.index(day) - 1) % len(WEEKDAYS)]
    previous = _is_open_from_previous_day(_row_for(hours, store_id, previous_day), visit_time)
    if current is True or previous is True:
        return "OPEN"
    if current is None or previous is None:
        return "UNKNOWN"
    return "CLOSED"
