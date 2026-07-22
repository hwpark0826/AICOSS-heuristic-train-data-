"""MUMUT virtual-scenario labeling UI."""
from pathlib import Path
import math
import os

import streamlit as st

from src.label_repository import LabelRepository
from src.supabase_repository import SupabaseLabelRepository

RUN_DIR = Path("data/runs") / os.getenv("MUMUT_RUN_ID", "run_006")
STORAGE_BACKEND = os.getenv("MUMUT_STORAGE", "sqlite").lower()
EVALUATORS = {"A01": "\ubc15\ud604\uc6b0", "A02": "\uc774\uc11d\ud6c8", "A03": "\ub178\uc720\uc815"}

TIME_LABELS = {"UNDER_60": "1\uc2dc\uac04 \uc774\ud558", "FROM_60_TO_120": "1~2\uc2dc\uac04", "OVER_120": "2\uc2dc\uac04 \ucd08\uacfc", "NO_PREFERENCE": "\uc2dc\uac04 \uc81c\ud55c \uc5c6\uc74c"}
BUDGET_LABELS = {"FREE": "\ubb34\ub8cc", "UNDER_10000": "1\ub9cc \uc6d0 \uc774\ud558", "UNDER_30000": "3\ub9cc \uc6d0 \uc774\ud558", "UNDER_50000": "5\ub9cc \uc6d0 \uc774\ud558", "NO_PREFERENCE": "\uc608\uc0b0 \uc81c\ud55c \uc5c6\uc74c"}
PURPOSE_LABELS = {"EAT": "\uc2dd\uc0ac", "REST": "\uc26c\uae30", "BROWSE": "\uad6c\uacbd", "EXPERIENCE": "\uc0c8\ub85c\uc6b4 \uacbd\ud5d8", "NO_PREFERENCE": "\ub2e4\uc74c \ud65c\ub3d9 \uc815\ud558\uc9c0 \uc54a\uc74c"}
ATMOSPHERE_LABELS = {"QUIET": "\uc870\uc6a9\ud568", "LIVELY": "\ud65c\uae30\ucc38", "NO_PREFERENCE": "\ubd84\uc704\uae30 \uc0c1\uad00\uc5c6\uc74c"}
HILL_LABELS = {"AVOID": "\uc624\ub974\ub9c9\uc740 \ud53c\ud558\uace0 \uc2f6\uc74c", "NO_PREFERENCE": "\uacbd\uc0ac \uc0c1\uad00\uc5c6\uc74c"}
PARKING_LABELS = {"REQUIRED": "\uc8fc\ucc28\uac00 \uaf2d \ud544\uc694\ud568", "NO_PREFERENCE": "\uc8fc\ucc28 \uc0c1\uad00\uc5c6\uc74c"}
COMPANION_LABELS = {"FAMILY": "\uac00\uc871\uacfc", "COUPLE": "\uc5f0\uc778\u00b7\ubc30\uc6b0\uc790\uc640", "FRIENDS": "\uce5c\uad6c\ub4e4\uacfc", "ALONE": "\ud63c\uc790"}
AGE_LABELS = {"TEENS": "10\ub300", "20S": "20\ub300", "30S": "30\ub300", "40S": "40\ub300", "50S": "50\ub300", "60_PLUS": "60\ub300 \uc774\uc0c1"}
GENDER_LABELS = {"MALE": "\ub0a8\uc131", "FEMALE": "\uc5ec\uc131"}
OUTCOME_LABELS = {"\ucd94\ucc9c\ud574\uc694": "ACCEPTED", "\ucd94\ucc9c\ud558\uc9c0 \uc54a\uc544\uc694": "REJECTED"}
REASON_LABELS = {
    "\uac70\ub9ac\uac00 \uba40\uc5b4\uc694": "TOO_FAR",
    "\uac00\uaca9\uc774 \ubd80\ub2f4\ub3fc\uc694": "PRICE_BURDEN",
    "\uc120\ud0dd\ud55c \uc870\uac74\uacfc \ub2ec\ub77c\uc694": "MISMATCH",
    "\ud654\uba74\uc5d0 \uc81c\uacf5\ub41c \uc815\ubcf4\uac00 \ubd80\uc871\ud574\uc694": "INFO_INSUFFICIENT",
    "\uc774\uacf3\uc740 \ub04c\ub9ac\uc9c0 \uc54a\uc544\uc694": "LOW_APPEAL",
}
MISMATCH_DETAIL_LABELS = {
    "\ubaa9\uc801\uc774 \ub2ec\ub77c\uc694": "PURPOSE_MISMATCH",
    "\ubd84\uc704\uae30\uac00 \ub2ec\ub77c\uc694": "ATMOSPHERE_MISMATCH",
    "\ub3d9\ud589\u00b7\uc5f0\ub839 \uc870\uac74\uacfc \uc5b4\uc6b8\ub9ac\uc9c0 \uc54a\uc544\uc694": "PROFILE_MISMATCH",
    "\uacbd\uc0ac\uac00 \ubd80\ub2f4\ub3fc\uc694": "HILL_MISMATCH",
    "\uc8fc\ucc28 \uc870\uac74\uacfc \ub2ec\ub77c\uc694": "PARKING_MISMATCH",
    "\uae30\ud0c0 \uc870\uac74\uacfc \ub2ec\ub77c\uc694": "OTHER_CONDITION_MISMATCH",
}


def secret_value(name: str) -> str | None:
    if name in st.secrets:
        return str(st.secrets[name])
    return os.getenv(name)


def make_repository():
    if STORAGE_BACKEND == "supabase":
        url = secret_value("SUPABASE_URL")
        key = secret_value("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            st.error("\uc911\uc559 DB \uc5f0\uacb0 \uc124\uc815\uc774 \ube60\uc838 \uc788\uc2b5\ub2c8\ub2e4.")
            st.stop()
        return SupabaseLabelRepository(url, key, RUN_DIR.name)
    repository = LabelRepository(RUN_DIR / "labels.sqlite")
    repository.initialize_from_run(RUN_DIR)
    return repository


def display(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)) or str(value).lower() == "nan":
        return "UNKNOWN"
    return str(value)


def state_key(kind: str, annotator: str) -> str:
    return f"mumut:{RUN_DIR.name}:{annotator}:{kind}"


repo = make_repository()
st.set_page_config(page_title="MUMUT \uac00\uc0c1 \uc2dc\ub098\ub9ac\uc624 \ud3c9\uac00", page_icon="\U0001f4cd", layout="centered")
st.markdown("""
<style>
  .block-container {max-width: 820px; padding-top: 2.2rem; padding-bottom: 3rem;}
  [data-testid="stMetric"] {background: #F7F8FA; border-radius: 10px; padding: 0.7rem;}
</style>
""", unsafe_allow_html=True)
st.title("MUMUT \uac00\uc0c1 \uc2dc\ub098\ub9ac\uc624 \ud3c9\uac00")
st.caption("\uc2e4\uc81c \ubc29\ubb38\uc774 \uc544\ub2cc \uac00\uc0c1 \uc0c1\ud669\uc785\ub2c8\ub2e4. \uc815\ubcf4\ub97c \ubcf4\uace0 \uc810\ud3ec\ub97c \ucd94\ucc9c\ud560\uc9c0 \ud310\ub2e8\ud574 \uc8fc\uc138\uc694.")

annotator = st.sidebar.selectbox("\ud3c9\uac00\uc790", list(EVALUATORS), format_func=lambda code: EVALUATORS[code])
progress_key = state_key("progress", annotator)
assignment_key = state_key("assignment", annotator)
if progress_key not in st.session_state:
    st.session_state[progress_key] = repo.progress(annotator)
if assignment_key not in st.session_state:
    st.session_state[assignment_key] = repo.next_assignment(annotator)
progress = st.session_state[progress_key]
assignment = st.session_state[assignment_key]
st.progress(progress["completed"] / progress["total"] if progress["total"] else 0)
st.write(f"**{EVALUATORS[annotator]}** \u00b7 {progress['completed']} / {progress['total']} \uc644\ub8cc \u00b7 {progress['remaining']}\uac74 \ub0a8\uc74c")

if assignment is None:
    st.success("\ubaa8\ub4e0 \ubc30\uc815\uc744 \uc644\ub8cc\ud588\uc2b5\ub2c8\ub2e4.")
    st.stop()

data = assignment["snapshot"]
with st.container(border=True):
    st.subheader("1. \uac00\uc0c1 \uc0c1\ud669")
    profile = ""
    if display(data.get("age_group")) != "UNKNOWN":
        profile += AGE_LABELS.get(display(data.get("age_group")), "") + " "
    if display(data.get("gender_code")) != "UNKNOWN":
        profile += GENDER_LABELS.get(display(data.get("gender_code")), "") + " "
    companion = COMPANION_LABELS.get(display(data.get("companion_type")), display(data.get("companion_type")))
    st.write(f"**{display(data.get('day_of_week'))}\uc694\uc77c {display(data.get('visit_time'))}**, **{profile}{companion}** \uc0c1\ud669\uc785\ub2c8\ub2e4.")
    left, right = st.columns(2)
    left.write(f"\u23f1\ufe0f \ub0a8\uc740 \uc2dc\uac04: **{TIME_LABELS.get(display(data.get('available_time_code')), 'UNKNOWN')}**")
    right.write(f"\U0001F4B3 \uc608\uc0b0: **{BUDGET_LABELS.get(display(data.get('budget_code')), 'UNKNOWN')}**")
    left.write(f"\U0001F3AF \ub2e4\uc74c \ud65c\ub3d9: **{PURPOSE_LABELS.get(display(data.get('purpose_code')), 'UNKNOWN')}**")
    right.write(f"\U0001F33F \uc6d0\ud558\ub294 \ubd84\uc704\uae30: **{ATMOSPHERE_LABELS.get(display(data.get('atmosphere_code')), 'UNKNOWN')}**")
    left.write(f"\U0001FAA8 \uc774\ub3d9 \uc870\uac74: **{HILL_LABELS.get(display(data.get('hill_preference')), 'UNKNOWN')}**")
    right.write(f"\U0001F697 \uc8fc\ucc28 \uc870\uac74: **{PARKING_LABELS.get(display(data.get('parking_preference')), 'UNKNOWN')}**")

with st.container(border=True):
    st.subheader("2. \ud3c9\uac00\ud560 \uc810\ud3ec")
    st.markdown(f"### {display(data.get('store_name'))}")
    st.caption(f"{display(data.get('category_group'))} \u00b7 {display(data.get('category_main'))} \u00b7 {display(data.get('category_sub'))}")
    st.write(f"\ub300\ud45c \uc815\ubcf4: **{display(data.get('representative_item'))}** \u00b7 \ub300\ud45c \uac00\uaca9 **{display(data.get('representative_price_krw'))}\uc6d0**")
    col1, col2, col3 = st.columns(3)
    col1.metric("\ub3c4\ubcf4", f"{display(data.get('estimated_walking_time_min'))}\ubd84")
    col2.metric("\uac70\ub9ac", f"{display(data.get('estimated_walking_distance_m'))}m")
    col3.metric("\uacbd\uc0ac", display(data.get("slope_level")))
    st.info(f"\uc601\uc5c5 \uc0c1\ud0dc: {display(data.get('opening_status'))}  |  \uc8fc\ucc28 \uc815\ubcf4: {display(data.get('parking_status'))}")
    place_url = display(data.get("place_url"))
    if place_url != "UNKNOWN":
        st.link_button("\ub124\uc774\ubc84 \uc9c0\ub3c4\uc5d0\uc11c \uc810\ud3ec \uc815\ubcf4 \ubcf4\uae30", place_url, use_container_width=True)

with st.container(border=True):
    st.subheader("3. \ud310\ub2e8")
    with st.form(key=f"decision:{assignment['assignment_id']}", clear_on_submit=True):
        outcome_label = st.radio("\uc774 \uc810\ud3ec\ub97c \ucd94\ucc9c\ud560\uae4c\uc694?", list(OUTCOME_LABELS), index=None, horizontal=True)
        reason_label = st.radio("\ucd94\ucc9c\ud558\uc9c0 \uc54a\uc744 \uacbd\uc6b0\uc5d0\ub9cc \uc774\uc720\ub97c \ud558\ub098 \uace0\ub974\uc138\uc694. \ucd94\ucc9c\ud560 \uacbd\uc6b0 \ube44\uc6cc \ub450\uc138\uc694.", list(REASON_LABELS), index=None)
        mismatch_detail_label = st.radio("'선택한 조건과 달라요'를 골랐을 때만, 어떤 조건인지 하나 고르세요.", list(MISMATCH_DETAIL_LABELS), index=None)
        submitted = st.form_submit_button("\uc81c\ucd9c\ud558\uace0 \ub2e4\uc74c \uac74 \ubcf4\uae30", use_container_width=True)

if submitted:
    outcome = OUTCOME_LABELS.get(outcome_label)
    reason = REASON_LABELS.get(reason_label)
    mismatch_detail = MISMATCH_DETAIL_LABELS.get(mismatch_detail_label)
    if outcome is None:
        st.warning("\ucd94\ucc9c \uc5ec\ubd80\ub97c \uba3c\uc800 \uc120\ud0dd\ud574 \uc8fc\uc138\uc694.")
    elif outcome == "REJECTED" and reason is None:
        st.warning("\uac70\uc808 \uc774\uc720\ub97c \ud558\ub098 \uc120\ud0dd\ud574 \uc8fc\uc138\uc694.")
    elif outcome == "REJECTED" and reason == "MISMATCH" and mismatch_detail is None:
        st.warning("\uc120\ud0dd\ud55c \uc870\uac74 \uc911 \uc5b4\ub5a4 \uc810\uc774 \ub2ec\ub790\ub294\uc9c0 \uc120\ud0dd\ud574 \uc8fc\uc138\uc694.")
    elif outcome == "REJECTED" and reason != "MISMATCH" and mismatch_detail is not None:
        st.warning("\uc138\ubd80 \uc870\uac74\uc740 '선택한 조건과 달라요'를 고른 경우에만 선택해 주세요.")
    elif outcome == "ACCEPTED" and (reason is not None or mismatch_detail is not None):
        st.warning("\ucd94\ucc9c\ud560 \uacbd\uc6b0\uc5d0\ub294 \uac70\uc808 \uc774\uc720\uc640 \uc138\ubd80 \uc870\uac74\uc744 \ube44\uc6cc \ub450\uc138\uc694.")
    else:
        try:
            repo.submit_label(assignment["assignment_id"], annotator, outcome, reason, mismatch_detail)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.pop(progress_key, None)
            st.session_state.pop(assignment_key, None)
            st.rerun()
