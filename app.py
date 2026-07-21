"""Local virtual-scenario labeling UI for a fixed MUMUT run."""
from pathlib import Path
import hmac
import json
import math
import os
import streamlit as st
from src.label_repository import LabelRepository, REJECTION_REASONS
from src.supabase_repository import SupabaseLabelRepository

RUN_DIR = Path("data/runs") / os.getenv("MUMUT_RUN_ID", "run_004")
STORAGE_BACKEND = os.getenv("MUMUT_STORAGE", "sqlite").lower()


def secret_value(name: str) -> str | None:
    if name in st.secrets:
        return str(st.secrets[name])
    return os.getenv(name)


if STORAGE_BACKEND == "supabase":
    supabase_url = secret_value("SUPABASE_URL")
    service_role_key = secret_value("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        st.error("Central storage secrets are not configured.")
        st.stop()
    repo = SupabaseLabelRepository(supabase_url, service_role_key, RUN_DIR.name)
else:
    repo = LabelRepository(RUN_DIR / "labels.sqlite")
    repo.initialize_from_run(RUN_DIR)


def display(value: object) -> str:
    return "UNKNOWN" if value is None or (isinstance(value, float) and math.isnan(value)) or str(value).lower() == "nan" else str(value)


TIME_LABELS = {"UNDER_60": "1시간 이하", "FROM_60_TO_120": "1~2시간", "OVER_120": "2시간 이상", "NO_PREFERENCE": "시간 제약 없음"}
BUDGET_LABELS = {"FREE": "무료", "UNDER_10000": "1만 원 이하", "UNDER_30000": "3만 원 이하", "UNDER_50000": "5만 원 이하", "NO_PREFERENCE": "예산 제한 없음"}
PURPOSE_LABELS = {"EAT": "식사", "REST": "쉬기", "BROWSE": "구경", "EXPERIENCE": "새로운 경험", "NO_PREFERENCE": "특별히 정한 활동 없음"}
ATMOSPHERE_LABELS = {"QUIET": "조용한 분위기", "LIVELY": "활기찬 분위기", "NO_PREFERENCE": "분위기 상관없음"}
HILL_LABELS = {"AVOID": "오르막은 피하고 싶음", "NO_PREFERENCE": "경사 상관없음"}
PARKING_LABELS = {"REQUIRED": "주차가 꼭 필요함", "NO_PREFERENCE": "주차 상관없음"}
AGE_LABELS = {"TEENS": "10대", "20S": "20대", "30S": "30대", "40S": "40대", "50S": "50대", "60_PLUS": "60대 이상"}
GENDER_LABELS = {"MALE": "남성", "FEMALE": "여성"}
OUTCOME_LABELS = {"추천해요": "ACCEPTED", "추천하지 않아요": "REJECTED"}
REASON_LABELS = {
    "정보가 부족해서 판단하기 어려워요": "INFO_INSUFFICIENT",
    "원하는 활동이나 분위기와 맞지 않아요": "MISMATCH",
    "주차하기 불편할 것 같아요": "PARKING_TIGHT",
    "가격이 부담돼요": "PRICE_BURDEN",
    "이동 거리가 멀게 느껴져요": "TOO_FAR",
}

st.set_page_config(page_title="MUMUT 라벨링", page_icon="🧭", layout="centered")
st.markdown("""
<style>
  .block-container {max-width: 820px; padding-top: 2.2rem; padding-bottom: 3rem;}
  [data-testid="stMetric"] {background: #F7F8FA; border-radius: 10px; padding: 0.7rem;}
</style>
""", unsafe_allow_html=True)
st.title("MUMUT 가상 시나리오 평가")
st.caption("실제 방문이 아닌 가상 상황입니다. 아래 정보를 보고 이 점포를 추천할지 판단해 주세요.")

annotator = st.sidebar.selectbox("평가자", ["A01", "A02", "A03"])
if STORAGE_BACKEND == "supabase":
    pins_json = secret_value("MUMUT_EVALUATOR_PINS")
    try:
        evaluator_pins = json.loads(pins_json or "{}")
    except json.JSONDecodeError:
        st.error("Evaluator PIN configuration is invalid.")
        st.stop()
    pin = st.sidebar.text_input("평가자 PIN", type="password")
    expected_pin = str(evaluator_pins.get(annotator, "")).encode("utf-8")
    entered_pin = str(pin or "").encode("utf-8")
    if not expected_pin or not hmac.compare_digest(entered_pin, expected_pin):
        st.info("평가자 PIN을 입력해 주세요.")
        st.stop()
progress = repo.progress(annotator)
st.progress(progress["completed"] / progress["total"])
st.write(f"**{annotator}** · {progress['completed']} / {progress['total']} 완료 · {progress['remaining']}건 남음")

assignment = repo.next_assignment(annotator)
if assignment is None:
    st.success("모든 배정을 완료했습니다.")
    st.stop()

data = assignment["snapshot"]
with st.container(border=True):
    st.subheader("① 가상 상황")
    person = ""
    if display(data.get("age_group")) != "UNKNOWN": person += AGE_LABELS.get(display(data.get("age_group")), "") + " "
    if display(data.get("gender_code")) != "UNKNOWN": person += GENDER_LABELS.get(display(data.get("gender_code")), "") + " "
    st.write(
        f"**{display(data.get('day_of_week'))}요일 {display(data.get('visit_time'))}**, "
        f"**{person}{display(data.get('companion_type'))}** 상황입니다."
    )
    left, right = st.columns(2)
    left.write(f"⏱️ 남은 시간: **{TIME_LABELS.get(display(data.get('available_time_code')), 'UNKNOWN')}**")
    right.write(f"💳 예산: **{BUDGET_LABELS.get(display(data.get('budget_code')), 'UNKNOWN')}**")
    left.write(f"🎯 다음 활동: **{PURPOSE_LABELS.get(display(data.get('purpose_code')), 'UNKNOWN')}**")
    right.write(f"🌿 원하는 분위기: **{ATMOSPHERE_LABELS.get(display(data.get('atmosphere_code')), 'UNKNOWN')}**")
    left.write(f"⛰️ 이동 조건: **{HILL_LABELS.get(display(data.get('hill_preference')), 'UNKNOWN')}**")
    right.write(f"🚗 주차 조건: **{PARKING_LABELS.get(display(data.get('parking_preference')), 'UNKNOWN')}**")

st.write("")
with st.container(border=True):
    st.subheader("② 검토할 점포")
    st.markdown(f"### {display(data.get('store_name'))}")
    st.caption(f"{display(data.get('category_group'))} · {display(data.get('category_main'))} · {display(data.get('category_sub'))}")
    st.write(f"대표 정보: **{display(data.get('representative_item'))}** · 대표 가격: **{display(data.get('representative_price_krw'))}원**")
    col1, col2, col3 = st.columns(3)
    col1.metric("도보", f"{display(data.get('estimated_walking_time_min'))}분")
    col2.metric("거리", f"{display(data.get('estimated_walking_distance_m'))}m")
    col3.metric("경사", display(data.get("slope_level")))
    st.info(f"영업 상태: {display(data.get('opening_status'))}  |  주차 정보: {display(data.get('parking_status'))}")
    place_url = display(data.get("place_url"))
    if place_url != "UNKNOWN": st.link_button("네이버 지도에서 점포 정보 보기", place_url, use_container_width=True)

st.write("")
with st.container(border=True):
    st.subheader("③ 판단")
    outcome_label = st.radio(
        "이 점포를 추천할까요?",
        list(OUTCOME_LABELS),
        index=None,
        horizontal=True,
        key=f"outcome_{assignment['assignment_id']}",
    )
    outcome = OUTCOME_LABELS.get(outcome_label)
    reason_label = None
    if outcome == "REJECTED":
        reason_label = st.radio(
            "추천하지 않는 가장 큰 이유를 하나 골라주세요.",
            list(REASON_LABELS),
            index=None,
            key=f"reason_{assignment['assignment_id']}",
        )
    reason = REASON_LABELS.get(reason_label)
    submitted = st.button("저장하고 다음 건 보기", use_container_width=True)
if submitted:
    if outcome is None:
        st.warning("ACCEPTED 또는 REJECTED를 먼저 선택해 주세요.")
    elif outcome == "REJECTED" and reason is None:
        st.warning("거절 사유를 하나 선택해 주세요.")
    else:
        try:
            repo.submit_label(assignment["assignment_id"], annotator, outcome, reason)
        except ValueError as error:
            st.error(str(error))
        else:
            st.rerun()
