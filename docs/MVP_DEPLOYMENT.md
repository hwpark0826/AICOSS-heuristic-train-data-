# MUMUT 팀 평가 MVP 배포 절차

## 목표

팀원 A01, A02, A03이 하나의 Streamlit 링크에서 평가하고, 판단 결과를 하나의 Supabase Postgres DB에 즉시 저장한다. 이 문서는 신뢰된 소규모 팀을 위한 PIN 기반 MVP 절차다.

## 구조

```text
팀원 브라우저 → Streamlit Community Cloud → Supabase Postgres
```

- Streamlit은 화면과 PIN 확인만 담당한다.
- Supabase는 run, assignment, 화면 표시 스냅샷, label, 감사 이벤트의 중앙 저장소다.
- `data/runs/run_004`의 SQLite는 로컬 개발용이며, 배포 후 원본 저장소가 아니다.

## 1. Supabase 설정

1. Supabase에서 새 프로젝트를 만든다.
2. SQL Editor에서 `supabase/migrations/001_mvp_labeling.sql` 전체를 한 번 실행한다.
3. Project Settings → API에서 아래 두 값을 확인한다.
   - Project URL
   - `service_role` key
4. `service_role` key는 Streamlit 서버의 Secrets에만 둔다. 브라우저·Git·채팅에 공유하지 않는다.

## 2. run_004 업로드

로컬 PowerShell에서 아래 환경 변수를 일시적으로 설정하고 실행한다.

```powershell
$env:SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co'
$env:SUPABASE_SERVICE_ROLE_KEY = 'YOUR_SERVICE_ROLE_KEY'
$env:MUMUT_RUN_ID = 'run_004'
python scripts/upload_run_to_supabase.py
```

업로드가 끝나면 Supabase Table Editor에서 다음을 확인한다.

- `runs`: 1행 (`run_004`)
- `assignments`: 240행
- 평가자별 assignment: A01/A02/A03 각 80행
- `labels`: 0행

이미 같은 `run_id`가 있어도 마스터 SHA-256이 다르면 업로드는 실패한다.

## 3. Streamlit Cloud 배포

1. 코드 저장소를 GitHub에 올린다. `.streamlit/secrets.toml`은 절대 커밋하지 않는다.
2. Streamlit Community Cloud에서 **Create app**을 선택한다.
3. 해당 GitHub 저장소, 브랜치, 엔트리 파일 `app.py`를 선택한다.
4. Advanced settings → Secrets에 아래 값을 넣는다. 실제 PIN은 팀원별로 다르게 정한다.

```toml
MUMUT_STORAGE = "supabase"
MUMUT_RUN_ID = "run_004"
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"
MUMUT_EVALUATOR_PINS = '{"A01":"A01_PIN","A02":"A02_PIN","A03":"A03_PIN"}'
```

5. 배포 후 공유 링크를 팀원에게 전달한다.
6. 팀원에게는 본인 평가자 코드와 본인 PIN만 따로 전달한다.

## 4. 운영 규칙

- 팀원은 자신의 코드와 PIN만 사용한다.
- 제출된 라벨은 중앙 DB의 `labels`와 `label_events`에 동시에 기록된다.
- 같은 assignment는 DB 제약과 `submit_label` 함수 때문에 두 번 저장되지 않는다.
- 완료된 라벨을 수정하지 않는다. 중대한 오류는 삭제 대신 `INVALIDATED` 처리한다.
- 새 run은 로컬에서 생성·검증 후 별도 `run_id`로 업로드한다. 시작된 run의 시나리오, master snapshot, seed, 표시값은 바꾸지 않는다.

## 5. 배포 전 체크

- [ ] `requirements.txt`에 `supabase`가 포함되어 있다.
- [ ] Supabase migration 실행 완료
- [ ] `run_004` 240건 업로드 완료
- [ ] Streamlit Secrets 설정 완료
- [ ] A01 PIN으로 1건 제출 테스트
- [ ] Supabase `labels`와 `label_events`에서 1건 확인
- [ ] A02로 접속 시 A01 assignment가 보이지 않는지 확인

## MVP 한계와 다음 단계

- PIN은 팀 내부의 실수 방지 수단이며 정식 사용자 인증은 아니다.
- 외부 평가자나 민감한 데이터가 포함되면 Supabase Auth 이메일 로그인과 RLS 사용자 정책으로 전환한다.
- 현재 `parking_available` 결측, 가격 결측은 중앙 DB 전환으로 해결되지 않는다. 데이터 보완 후 새 master snapshot과 새 run으로 반영한다.
