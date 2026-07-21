# MUMUT 마스터 DB 실제 구조 분석

분석일: 2026-07-22. 대상은 `data/master/MUMUT_리움상권_MVP_데이터베이스_1차 수정.xlsx`이며, 원본은 읽기만 수행했다. SHA-256은 `48d2c0d4972a11b9a8ea6e19e29944b7c448a80a38321dcc3b9266b1181dde8d`이다.

## 분석 기준

- 워크시트의 서식상 최대 행은 모두 1,000행이지만, 데이터 행 수에는 실제 값이 있는 행만 포함했다.
- 표 형식 시트의 주 헤더는 모두 실제 **4행**에서 확인했다. `REASON_CODE`는 22행에 별도 재추천 트리거 표의 헤더가 있다.
- 최초 분석 시 작업공간의 `README.md`, `AGENTS.md`, `docs/MUMUT_DATA_SPEC.md`는 0바이트였다. 이후 전달된 원문을 각각 실제 파일로 정리했다. 이 보고서의 Excel 수치와 첨부 AGENTS 명세 대조는 반영되어 있으나, 새로 배치된 데이터 명세에 대한 추가 대조는 별도 갱신 시 수행한다.

## 실제 Excel 시트 목록

|시트|용도|실제 데이터 행|
|---|---|---:|
|안내|마스터 범위·구축 원칙·MVP 경로 산식 안내|설명 7행|
|STORE|점포 마스터|74|
|STORE_HOUR|점포별 요일 영업시간|518|
|ORIGIN|점포별 QR 출발점|74|
|ROUTE_MATRIX|점포 간 이동 추정치|5,402|
|REASON_CODE|거절·순위·미선택 사유 16개와 재추천 트리거 2개|16 + 2|
|SESSION_SCHEMA|운영 `SESSION` 빈 스키마|0|
|REQUEST_SCHEMA|운영 `RECOMMENDATION_REQUEST` 빈 스키마|0|
|CANDIDATE_SCHEMA|운영 `CANDIDATE_DECISION` 빈 스키마|0|
|RESULT_SCHEMA|운영 `RESULT` 빈 스키마|0|
|USER_EVENT_SCHEMA|운영 `USER_EVENT` 빈 스키마|0|
|컬럼정의|일부 운영 컬럼의 타입·nullable 설명|16|
|수집점검|분위기 근거·영업시간 수집 점검|74 + 제외 1행|

## 시트별 실제 컬럼, 타입, 키

### STORE (4행 헤더, 74행 데이터, 16열)

`store_id TEXT` (PK), `naver_place_id TEXT` (후보 자연키), `store_name TEXT`, `category_group TEXT`, `category_main TEXT`, `category_sub TEXT`, `road_address TEXT`, `latitude DECIMAL`, `longitude DECIMAL`, `phone TEXT`, `place_url TEXT`, `representative_item TEXT`, `representative_price_krw INTEGER`, `atmosphere TEXT`, `parking_available TEXT`, `active_yn TEXT`.

학습·화면 조인에 필요한 컬럼은 `store_id`, 이름·업종·주소, 대표 항목/가격, 분위기, 주차, 활성 여부다. 좌표·전화·URL은 상세 표시 또는 운영 참고용이며, 전화는 학습 생성에 필요하지 않다. 코드값은 `category_group={F&B, 소매, 뷰티, 문화·체험}`, `active_yn={Y}`, `atmosphere={조용함, 활기참, NULL}`, `parking_available={NULL}`다.

결측(74건 기준): `phone` 10 (13.51%), `representative_item` 41 (55.41%), `representative_price_krw` 45 (60.81%), `atmosphere` 33 (44.59%), `parking_available` 74 (100%). 그 밖의 컬럼은 0건이다. 가격이 있는 29건은 정수 원 단위(0~200,000)이며 범위값·통화·가격 종류 컬럼은 없다.

### STORE_HOUR (4행 헤더, 518행 데이터, 9열)

`store_id TEXT` + `day_of_week TEXT` (복합 PK), `open_time TIME(TEXT HH:MM)`, `close_time TIME(TEXT HH:MM)`, `break_start TIME`, `break_end TIME`, `last_order TIME`, `is_closed TEXT`, `raw_text TEXT`.

가상 방문시각의 영업 여부 계산에는 전 컬럼 중 `store_id`, 요일, 개점/폐점, 브레이크, 휴무가 필요하다. `last_order`와 `raw_text`는 표시·해석 보조다. 요일 코드는 `{월, 화, 수, 목, 금, 토, 일}`, 휴무 표기 코드는 `{Y, N, NULL}`이다.

결측: `open_time`/`close_time` 각 191 (36.87%), `break_start`/`break_end` 각 491 (94.79%), `last_order` 434 (83.78%), `is_closed`/`raw_text` 각 142 (27.41%). `store_id`, 요일은 결측이 없다. `00:00`, `00:05`, `24:00` 표기는 있으나 `close_time < open_time`인 자정 넘김 사례는 0건이다.

### ORIGIN (4행 헤더, 74행 데이터, 7열)

`origin_id TEXT` (PK), `store_id TEXT` (FK → STORE), `origin_name TEXT`, `latitude DECIMAL`, `longitude DECIMAL`, `qr_url TEXT`, `active_yn TEXT`.

가상 시나리오의 출발점 및 ROUTE_MATRIX 조인에는 `origin_id`, `store_id`, 활성 여부가 필요하다. 이름·좌표·QR URL은 화면/운영 참고다. 모든 컬럼 결측은 0건이고 `active_yn={Y}`다.

### ROUTE_MATRIX (4행 헤더, 5,402행 데이터, 11열)

`origin_id TEXT` (FK → ORIGIN), `origin_store_id TEXT` (FK → STORE), `destination_store_id TEXT` (FK → STORE), `straight_line_distance_m INTEGER`, `estimated_walking_distance_m INTEGER`, `estimated_walking_time_min INTEGER`, `origin_elevation_m INTEGER`, `destination_elevation_m INTEGER`, `estimated_uphill_gain_m INTEGER`, `estimated_slope_percent DECIMAL`, `slope_level TEXT`.

식별자는 `(origin_id, destination_store_id)` 또는 `(origin_store_id, destination_store_id)`다. 거리·시간·경사는 객관적 필터와 화면 표시용이며, 고도 원값은 계산 근거용이다. `estimated_slope_percent`와 `slope_level`만 각 54건(1.00%) 결측이고 나머지는 결측 0건이다. `slope_level={평탄, 완만, 경사, 가파름, NULL}`. 직선/보행 추정거리 0m인 경로는 60건이므로, 동일 좌표 점포 간 경로로 해석할지 데이터 오류로 취급할지 정책이 필요하다.

### REASON_CODE (두 개의 실제 표)

1. 4행 헤더, 5~20행: `reason_code TEXT` (PK), `stage TEXT`, `reason_label TEXT`, `description TEXT`. 16개 모두 결측 0건이다. `stage={후보 제외, 순위 하락, 순위 조정, 사용자 미선택}`.
2. 22행 헤더, 23~24행: `reroll_trigger_type TEXT` (PK), `stage TEXT`, `trigger_label TEXT`, `description TEXT`. `EXCLUDE_VISITED`, `RESET_CONDITION` 두 값이며 모두 `재추천 트리거`다.

이 시트는 평가자가 선택하는 사유 코드·표시 문구·집계 기준용이다. 안내 시트에는 “원인 코드 19”라고 쓰였지만 실제 사유 코드는 16개이고 트리거 2개는 별도 구조이므로, 19라는 수치와 일치하지 않는다.

### 빈 운영 스키마 (모두 4행 헤더, 0행 데이터)

|시트|실제 컬럼|추정 키·참조|
|---|---|---|
|SESSION_SCHEMA|`session_id, start_origin_id, started_at, ended_at, session_status`|`session_id` PK, `start_origin_id → ORIGIN`|
|REQUEST_SCHEMA|`request_id, session_id, origin_id, sequence_no, remaining_time_min, budget_max, purpose, avoid_hill, waiting, requested_at, model_version`|`request_id` PK, `session_id → SESSION`, `origin_id → ORIGIN`|
|CANDIDATE_SCHEMA|`request_id, store_id, primary_reason_code, filter_status, purpose_score, price_score, distance_score, slope_score, fairness_score, total_score, rank`|`(request_id, store_id)` 복합 PK, 사유 → REASON_CODE|
|RESULT_SCHEMA|`request_id, store_id, reason, reason_data, shown_at`|`request_id`/`store_id` 참조; 실제 PK는 미명시|
|USER_EVENT_SCHEMA|`event_id, session_id, request_id, store_id, reason_code, event_type, screen_name, event_data, created_at`|`event_id` PK로 추정; 나머지 참조|

빈 스키마는 운영 DB 설계 참고용일 뿐 현재 마스터 데이터로서 학습 행을 생성하는 입력은 아니다. 실제 REQUEST_SCHEMA에는 허용값·필수/선택·조건부 규칙이 없지만, 첨부 AGENTS 명세가 이를 보완한다: `companion_type={FAMILY, COUPLE, FRIENDS, ALONE}` 및 gender/age 조건부 규칙, 방문시각·예산·목적·분위기·경사·주차 코드의 허용값이 정의되어 있다. 그러므로 해당 **가상 시나리오 입력 검증은 명세를 근거로 구현 가능**하다. 다만 이 필드들은 현 Excel의 REQUEST_SCHEMA 컬럼과 다르므로, 가상 시나리오/assignment 전용 스키마로 별도 설계해야 한다.

### 컬럼정의 및 수집점검

`컬럼정의`은 16개 핵심 컬럼의 선언형 설명만 제공하며 전수 데이터 사전은 아니다. `수집점검`은 `store_id`, `store_name`, 분위기 근거 수(quiet/comfortable/lively), `selected_atmosphere`, 공개 리뷰 수, `hours_days`, 상태를 갖는다. 실제 점포 74행 외에 “제외/문화와사람들” 1행이 있으므로 점포 조인에서는 제외해야 한다. 이는 근거·수집 상태용이지 평가용 정규 테이블은 아니다.

## 키와 참조 무결성

- STORE `store_id` 74개는 모두 고유하며 모두 활성(`Y`)이다.
- ORIGIN `origin_id` 74개는 모두 고유이고 모든 `store_id`가 STORE에 존재한다. 비활성 점포를 참조하는 ORIGIN은 없다.
- ROUTE_MATRIX의 `origin_id`, 출발/도착 `store_id`는 모두 유효하다. `origin_id`와 `origin_store_id`의 매핑 불일치는 0건이다.
- self-route 0건, 중복 `(origin_id, origin_store_id, destination_store_id)` 0건, 중복 출발·도착 점포 쌍 0건이다.
- 활성 점포 수 `N=74` 기준 예상 비자기 방향 경로는 `N×(N-1)=5,402`건이며 실제도 5,402건이다.
- STORE_HOUR는 74×7=518건이며, 모든 점포가 정확히 7개 요일 행을 가진다. `(store_id, day_of_week)` 중복 0건, 존재하지 않는 점포 참조 0건이다.
- `is_closed=Y`인데 시간값이 있거나 `is_closed=N`인데 개·폐점 중 한쪽만 있는 충돌은 0건이다. 브레이크 시작/종료의 단측 결측 0건, last order가 폐점 이후인 사례 0건이다.

## 발견된 불일치·불확실성

1. 최초 AGENTS 명세는 `data/master/MUMUT_master.xlsx`를 가리켰으나, 현재 루트 `AGENTS.md`와 `README.md`는 실제 파일 `data/master/MUMUT_리움상권_MVP_데이터베이스_1차 수정.xlsx`를 가리키도록 정리했다.
2. STORE의 분위기는 `조용함` 36, `활기참` 5, NULL 33이지만, 수집점검의 `selected_atmosphere`는 `편안함` 27, `조용함` 9, `활기참` 5, NULL 33이다. 27점포가 `STORE=조용함`/`수집점검=편안함`으로 불일치한다. 결정: 평가·학습에서는 `편안함`을 `조용함(QUIET)`으로 정규화하며, 별도 분위기 범주를 만들지 않는다.
3. `parking_available`는 74/74 결측이다. `FILTER_PARKING` 코드는 있으나 실제 주차 필터는 판정 불가다.
4. 영업시간이 전부 미상인 요일 행이 142건이고, `is_closed`도 NULL이다. 이는 휴무가 아니라 **UNKNOWN**이다. 결정: 결측은 불가로 바꾸지 않고 UNKNOWN으로 유지한다.
5. 가격은 대표 항목 1개에 대한 정수 원화일 뿐, 가격대·변동가격·서비스 가격의 의미를 표준화하지 않는다. 45점포는 가격이 없다.
6. 대표 설명 컬럼은 없고 `representative_item`만 있으며 41점포가 결측이다. 평가 화면의 설명 품질은 보장할 수 없다.
7. ROUTE_MATRIX는 안내 시트에 따라 직선거리×1.25 및 75m/분으로 만든 MVP 추정치이며 실제 길찾기 결과가 아니다. 경사도 역시 추정치다. 0m 경로 60건과 경사 결측 54건의 처리 정책이 필요하다.
8. REASON_CODE의 “19개” 안내 수치와 실제 16개 사유 + 2개 트리거 구조가 다르다. 첨부 AGENTS가 라벨 거절 사유로 허용한 5개(`TOO_FAR`, `PRICE_BURDEN`, `MISMATCH`, `INFO_INSUFFICIENT`, `PARKING_TIGHT`)는 실제 16개 사유 코드에 모두 존재한다.
9. 첨부 AGENTS의 가상 시나리오 필드(`scenario_visit_at`, companion/gender/age 등)는 실제 REQUEST_SCHEMA의 컬럼 집합과 일치하지 않는다. 이는 가상 평가용 새 스키마를 만들라는 의도로 해석할 수 있으나, 기존 운영 요청과의 관계는 명시적으로 결정해야 한다.

## 학습데이터 구축 가능성

|기능|판정|근거/제약|
|---|---|---|
|가상 시나리오 생성|현재 데이터와 첨부 명세로 구현 가능|AGENTS가 필드·허용값·조건부 규칙을 제공하고, STORE/ORIGIN/ROUTE가 후보 정보를 제공한다. 코드별 실제 시각·금액·시간 한계의 매핑 분포는 운영 정책으로 정해야 한다.|
|방문 시각 기준 영업 여부|UNKNOWN 처리 시 가능|요일·개폐점·브레이크는 있으나 142건의 영업 상태가 미상이다. 결측은 UNKNOWN으로 유지하며, `24:00` 해석만 명시하면 된다.|
|객관적 하드 필터|UNKNOWN 처리 시 가능|가격·영업·거리·경사 컬럼은 있으나 가격/영업/경사 결측과 주차 100% 결측이 있다. 결측은 UNKNOWN으로 유지하고, 목적 적합은 하드 필터로 쓰지 않는다.|
|BALANCED_RANDOM 점포 배정|현재 데이터로 가능|활성 STORE 74개와 완전한 방향 ROUTE_MATRIX가 있다. 난수 시드, 목표 균형 허용오차만 구현 정책으로 정하면 된다.|
|A01/A02/A03 각 300건 배정|현재 데이터로 가능|평가자 식별자는 마스터에 없으나 고정 운영 설정으로 900개 assignment를 생성할 수 있다.|
|평가 화면 표시 점포 정보|UNKNOWN 처리 시 가능|이름·업종·주소·거리·시간은 있으나 대표 항목/가격/분위기/주차의 결측 또는 불일치가 있다.|
|점포별 노출 횟수 균형화|현재 데이터로 가능|74개 활성 점포 기준 900건은 점포당 12 또는 13회로 정확히 균형화할 수 있다(12회×62점포 + 13회×12점포).|
|최종 학습데이터 조인|현재 데이터와 첨부 명세로 구현 가능|AGENTS가 `ACCEPTED`/`REJECTED`, 허용 거절 사유, 미노출 점포 행 금지, INVALIDATED 원칙을 제공한다. assignment/annotation 물리 스키마는 별도로 만든다.|

## 권장 마스터 버전 관리

요구한 구조는 현재 마스터만으로 충분히 설계 가능하다. labeling run 시작 시 원본을 읽기 전용으로 복사하여 `master_snapshot.xlsx`를 만들고, 원본 SHA-256·`run_id`·`master_version`·스냅샷 생성 시각을 run 메타데이터에 기록한다. assignment 생성 시점에는 화면에 표시한 점포·경로·영업 판정 값을 assignment snapshot으로 저장한다. 완료 라벨은 최신 마스터로 재조인하거나 소급 변경하지 않는다. 중대한 오류는 기존 라벨을 삭제하지 말고 `INVALIDATED` 상태와 사유·처리 시각으로 별도 이력화한다.

이 방식은 원본 Excel 변경 금지, 가상 시나리오 평가, “실제 노출 점포 × 평가자 판단”만 학습 행으로 만든다는 전제와 양립한다.
