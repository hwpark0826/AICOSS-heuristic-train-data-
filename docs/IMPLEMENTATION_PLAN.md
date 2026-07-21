# MUMUT 가상 시나리오 인간 휴리스틱 데이터 구축 계획

전제: 실제 현장 기능(GPS/QR 스캔/현재 위치/현장 관찰)은 구현하지 않는다. 한 학습 행은 “가상 시나리오 1개 × 실제 노출 점포 1개 × 평가자 1명의 ACCEPTED 또는 REJECTED 판단”이다. 미노출 점포에는 REJECTED 행을 만들지 않는다.

본 계획은 구현 코드가 아니라, 구현 전 확정해야 할 산출물·검증 기준이다. 파일 경로는 권장 구조이며 아직 생성하지 않았다.

## Phase 1: Excel 로더, 검증기, 마스터 스냅샷

- 목적: 원본 마스터를 수정하지 않고 읽어 정규화·검증하며, run별 불변 스냅샷을 만든다.
- 입력: `data/master/*.xlsx`, `MASTER_DB_SCHEMA.md`의 실제 헤더 행·키·검증 규칙.
- 출력: 로드된 마스터 객체, 검증 보고서, `runs/<run_id>/master_snapshot.xlsx`, SHA-256, `master_version` 메타데이터.
- 구현 파일: `src/master_loader.py`, `src/master_validator.py`, `src/snapshot.py`, `tests/test_master_validator.py`, `runs/`.
- 핵심 함수: `load_master()`, `validate_master()`, `compute_sha256()`, `create_master_snapshot()`.
- 테스트: 4행 헤더 탐지, 74가 아닌 실제 활성 수 기반의 `N×(N-1)` 경로 검증, 키/FK/중복/self-route/요일 7건 검증, 결측을 보존하는지, 원본 SHA가 실행 전후 동일한지.
- 완료 조건: 오류와 경고를 구분한 재현 가능한 검증 보고서 및 불변 스냅샷이 생성된다.
- 선행 의존성: 실제 원본 파일명과 분위기 불일치·UNKNOWN 영업시간·0m 경로 처리 정책 확정.

## Phase 2: 가상 시나리오와 900건 균형 배정

- 목적: A01/A02/A03에 각 300건씩, 실제 노출 점포만 포함하는 가상 시나리오 assignment 900건을 생성한다.
- 입력: Phase 1 snapshot, 시나리오 분포/허용값/UNKNOWN 처리 정책, 평가자 목록 `{A01,A02,A03}`. 결측은 UNKNOWN으로 유지하며 `UNDER_60`은 60분 이하로 해석한다.
- 출력: run 고정 `scenario`, `assignment`, `shown_store_snapshot` 데이터. 점포별 총 노출은 12 또는 13회가 되도록 한다.
- 구현 파일: `src/scenario_generator.py`, `src/assignment_balancer.py`, `src/display_snapshot.py`, `tests/test_assignment_balancer.py`.
- 핵심 함수: `generate_scenarios()`, `is_open_at_virtual_time()`, `apply_hard_filters()`, `assign_balanced_random()`, `freeze_display_values()`.
- 테스트: 총 900건, 평가자별 300건, 점포 노출 12/13회, 고정 seed 재현성, 미노출 점포 행 0건, UNKNOWN이 REJECTED로 암묵 변환되지 않는지.
- 완료 조건: 모든 assignment가 snapshot과 seed로 재현되고, 화면 표시값이 마스터 변경과 분리된다.
- 선행 의존성: Phase 1 및 목적/예산/경사/주차/영업 UNKNOWN 정책. 시나리오 허용값·조건부 규칙과 ACCEPTED·REJECTED/거절 사유는 첨부 AGENTS 명세를 적용한다.

## Phase 3: SQLite 기반 모바일 Streamlit 평가 앱

- 목적: 오프라인/단일 운영 환경에서 가상 시나리오와 1개 노출 점포를 보여 주고 평가자의 판단을 저장한다.
- 입력: Phase 2 assignment 및 표시값 snapshot, 평가자 인증/진행 규칙, 사유 코드 사용 정책.
- 출력: SQLite의 평가 상태, `ACCEPTED`/`REJECTED`, 사유 코드, 타임스탬프, `INVALIDATED` 이력.
- 구현 파일: `app.py`, `src/sqlite_repository.py`, `src/label_service.py`, `src/models.py`, `tests/test_label_service.py`.
- 핵심 함수: `next_assignment()`, `submit_label()`, `invalidate_label()`, `resume_evaluator_progress()`.
- 테스트: A01~A03 권한 분리, assignment 단 한 번만 완료, 표시 snapshot 불변성, 중복 제출 방지, INVALIDATED가 삭제가 아닌 상태 이력인지.
- 완료 조건: 모바일 폭에서 900건을 중단·재개 가능하게 평가하고, 실제 현장 권한/기능 없이 판단을 저장한다.
- 선행 의존성: Phase 2, 라벨·필수 사유·수정/무효화 정책.

## Phase 4: Supabase 중앙 저장소 연동

- 목적: 다중 기기에서 assignment와 라벨 상태를 중앙화하고 동시성·감사를 지원한다.
- 입력: SQLite 스키마와 데이터 계약, Supabase 프로젝트/인증/RLS 정책.
- 출력: 중앙 `runs`, `assignments`, `labels`, `label_events`, `master_snapshots` 테이블 및 동기화.
- 구현 파일: `src/supabase_repository.py`, `sql/schema.sql`, `sql/rls.sql`, `scripts/migrate_sqlite_to_supabase.py`, `tests/test_supabase_repository.py`.
- 핵심 함수: `claim_assignment()`, `upsert_label()`, `append_label_event()`, `sync_pending_labels()`.
- 테스트: 동시 claim 충돌, 평가자별 접근 제한, 재전송 idempotency, snapshot hash 보존, INVALIDATED 감사 이력.
- 완료 조건: 세 평가자가 서로 다른 기기에서 중복 없이 900건을 완주하며 상태 이력을 조회할 수 있다.
- 선행 의존성: Phase 3의 확정 데이터 계약 및 Supabase 접근 권한.

## Phase 5: 최종 학습데이터 CSV/Parquet 생성

- 목적: 노출·판단·스냅샷을 조인해 모델 학습 가능하고 추적 가능한 데이터셋을 만든다.
- 입력: 완료/무효화 상태가 확정된 labels, assignments, scenario와 `shown_store_snapshot`.
- 출력: `outputs/<run_id>/human_heuristic_labels.csv`, 동등한 Parquet, 데이터 사전, 품질 보고서.
- 구현 파일: `src/dataset_builder.py`, `src/dataset_validator.py`, `tests/test_dataset_builder.py`, `outputs/`.
- 핵심 함수: `build_training_rows()`, `exclude_non_shown_stores()`, `exclude_or_flag_invalidated()`, `export_csv_parquet()`.
- 테스트: 행 단위가 scenario×shown store×evaluator인지, 미노출 점포가 없는지, 최신 마스터 재조인이 없는지, 라벨/assignment 수 reconciliation, CSV/Parquet 스키마 일치.
- 완료 조건: 900개의 유효 판단(무효화가 있으면 별도 수치로 보고)이 snapshot 근거와 함께 export된다.
- 선행 의존성: Phase 3 또는 4의 라벨 데이터, INVALIDATED 포함/제외 정책.

## Phase 6: 인간 데이터 기반 베이스라인 모델

- 목적: 인간 라벨만 사용해 기준 성능과 데이터 품질을 측정한다.
- 입력: Phase 5의 유효 학습데이터, 누수 방지 분할 정책, 지표 정의.
- 출력: 베이스라인 모델, 평가 리포트, 피처/라벨 정의와 재현 설정.
- 구현 파일: `src/baseline_features.py`, `src/train_baseline.py`, `src/evaluate_baseline.py`, `tests/test_feature_leakage.py`, `reports/`.
- 핵심 함수: `build_features_from_snapshot()`, `split_by_scenario_or_evaluator()`, `train_baseline()`, `evaluate()`.
- 테스트: 평가자/시나리오 누수, UNKNOWN 인코딩, 클래스 불균형, seed 재현성, snapshot 외 최신값 미사용.
- 완료 조건: 사람 데이터만 사용한 검증 지표와 오류 분석이 남고, 임의 적합도 점수는 피처나 라벨로 만들지 않는다.
- 선행 의존성: Phase 5 및 학습 목표/평가 지표 확정.

## Phase 7: GPT 합성 데이터 실험

- 목적: 인간 데이터와 명확히 분리된 합성 데이터가 성능·편향에 미치는 영향을 실험한다.
- 입력: Phase 5 human-only 기준 데이터, 승인된 프롬프트·안전/품질 정책, 비교 실험 설계.
- 출력: 합성 데이터 provenance, human-only 대비 실험표, 편향/오염 점검 결과.
- 구현 파일: `src/synthetic_experiment.py`, `prompts/`, `tests/test_synthetic_provenance.py`, `reports/`.
- 핵심 함수: `generate_synthetic_examples()`, `tag_provenance()`, `run_ablation()`, `compare_to_human_baseline()`.
- 테스트: human/synthetic 혼입 방지, 프롬프트/모델 버전 기록, 원본 라벨 변경 금지, Phase 6 기준선 대비 분리 평가.
- 완료 조건: 합성 데이터는 별도 산출물·명시적 provenance로 관리되고, 인간 데이터 기반 결과와 혼동되지 않는다.
- 선행 의존성: Phase 6 완료 및 GPT 사용 범위/비용/정책 승인.

## 구현 시작 전 우선 결정 사항

1. 분위기 정규화: 수집점검의 `편안함`은 모두 `조용함(QUIET)`으로 처리한다.
2. 영업시간·가격·주차·경사 결측은 `UNKNOWN`으로 표시하고, 불가·거절로 임의 변환하지 않는다.
3. `24:00`, 0m 경로, 추정 경사/도보시간의 표시 및 필터 적용 원칙.
4. `UNDER_60`은 60분 이하로 사용한다. `FREE` 예산 하드 필터는 구매가 필수인 F&B 점포에만 적용하며, 소매·뷰티·문화체험 점포는 가격이 있어도 둘러보기 가능성 때문에 제외하지 않는다. 나머지 예산·시간 코드의 실제 경계와 객관적 필터 임계치는 정해야 한다.
5. INVALIDATED의 권한·사유·최종 데이터셋 포함 규칙.
