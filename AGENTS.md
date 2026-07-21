# AGENTS.md

## 1. Project purpose

This repository implements a training-data construction system for
MUMUT, a store recommendation service for visitors near the Leeum
Museum and Hannam-dong commercial district.

The system does not collect real-world field observations.
All labeling cases are hypothetical virtual scenarios.

Three team members will label approximately 300 cases each,
for a total of approximately 900 human heuristic annotations.

The human annotations are seed labels for an MVP recommendation model.
They are not actual customer purchase or visit records.

## 2. Source of truth

The master Excel file is located at:

data/master/MUMUT_리움상권_MVP_데이터베이스_1차 수정.xlsx

Treat this Excel file as the source of truth for store, operating-hour,
origin, route, and rejection-code information.

Do not modify the original master Excel file unless explicitly requested.

Important sheets include:

- STORE
- STORE_HOUR
- ORIGIN
- ROUTE_MATRIX
- REASON_CODE
- REQUEST_SCHEMA

Excel headers begin on row 4, so pandas should generally read these
sheets with header=3.

## 3. Core domain rules

### 3.1 Stores

There are currently 74 stores.

Store attributes must consist of observable or factual information.
Do not invent subjective fields such as:

- family_friendly_score
- couple_friendly_score
- age_fit_score
- purpose_fit_score

The model should learn these relationships from human acceptance and
rejection labels.

### 3.2 User scenario fields

The virtual scenario contains:

- origin_id
- scenario_visit_at
- companion_type
- gender_code
- age_group
- available_time_code
- budget_code
- purpose_code
- atmosphere_code
- hill_preference
- parking_preference

Allowed values:

companion_type:
- FAMILY
- COUPLE
- FRIENDS
- ALONE

gender_code:
- MALE
- FEMALE

age_group:
- TEENS
- 20S
- 30S
- 40S
- 50S
- 60_PLUS

available_time_code:
- UNDER_60
- FROM_60_TO_120
- OVER_120
- NO_PREFERENCE

budget_code:
- FREE
- UNDER_10000
- UNDER_30000
- UNDER_50000
- NO_PREFERENCE

purpose_code:
- EAT
- REST
- BROWSE
- EXPERIENCE
- NO_PREFERENCE

atmosphere_code:
- QUIET
- LIVELY
- NO_PREFERENCE

hill_preference:
- AVOID
- NO_PREFERENCE

parking_preference:
- REQUIRED
- NO_PREFERENCE

Conditional rules:

- FAMILY: gender_code and age_group must be null.
- COUPLE: gender_code must be null; age_group is required.
- FRIENDS: gender_code must be null; age_group is required.
- ALONE: gender_code and age_group are required.

### 3.3 Human labels

Each row represents:

one virtual scenario
× one exposed store
× one annotator decision

Allowed outcomes:

- ACCEPTED
- REJECTED

Allowed rejection reasons:

- TOO_FAR
- PRICE_BURDEN
- MISMATCH
- INFO_INSUFFICIENT
- PARKING_TIGHT

reject_reason_code must be null when outcome is ACCEPTED.

A store that was not exposed must not be recorded as REJECTED.
Unexposed stores remain missing and do not create training rows.

### 3.4 Annotators

There are three annotators:

- A01
- A02
- A03

Each annotator should receive approximately 300 assignments.

A specific scenario-store assignment is judged by exactly one annotator
unless a separate agreement-study dataset is explicitly requested.

### 3.5 Scenario assignment

The initial assignment policy is BALANCED_RANDOM.

Do not use pure uniform random assignment.

First apply only objective hard filters, then prioritize stores with
lower exposure counts and randomly select from that balanced pool.

Possible hard filters include:

- inactive store
- origin store equals destination store
- definitely closed at scenario_visit_at
- parking is REQUIRED and parking_available is explicitly N
- walking time is objectively impossible within the available time
- FREE budget and the store is definitely paid

Do not hard-filter stores only because of:

- companion type
- age
- gender
- subjective purpose fit
- subjective atmosphere fit

Missing parking information must be treated as UNKNOWN, not N.

### 3.6 Opening hours

If close_time is earlier than open_time, interpret the interval as
crossing midnight.

For visits after midnight, also check the previous day's overnight
operating interval.

### 3.7 Master-data versioning

At the start of a labeling run, create an immutable snapshot of the
master Excel file.

Example:

data/runs/run_001/master_snapshot.xlsx

Every scenario, assignment, and annotation must reference:

- run_id
- master_version
- master_sha256

The labeling UI must display snapshot values, not live values from a
master file that may change during labeling.

Do not retroactively join completed labels to newer master values.

If a critical master-data error invalidates a label, preserve the old
label and mark it INVALIDATED instead of deleting it.

### 3.8 Synthetic data

GPT-generated data is not part of the first implementation phase.

Human data is the primary label source.

Future synthetic labels must be clearly separated with:

- label_source
- generator_model
- prompt_version
- generation_confidence
- validation_status

Never mix GPT labels into the human-only validation or test set.

## 4. Expected system

The repository should ultimately provide:

1. Master Excel validation
2. Immutable run snapshot creation
3. Virtual scenario generation
4. Balanced scenario-store assignment
5. Three-way annotator allocation
6. Mobile-friendly Streamlit labeling UI
7. Central database persistence
8. Progress dashboard
9. Final training-data export to CSV and Parquet
10. Automated tests

The UI is only for virtual evaluation.
Do not implement GPS, QR scanning, current-location detection,
or field-observation modes.

## 5. Preferred stack

- Python 3.11+
- pandas
- openpyxl
- pydantic
- Streamlit
- Supabase PostgreSQL
- pytest
- PyYAML

Use type hints throughout the Python code.

Use Pydantic or equivalent explicit validation for domain schemas.

Do not commit secrets.

Use environment variables for:

- SUPABASE_URL
- SUPABASE_KEY
- APP_ACCESS_CODE

## 6. Engineering rules

Before implementing a feature:

1. Inspect the current repository.
2. Inspect the actual Excel sheets and columns.
3. Do not assume column names that are not present.
4. Report schema conflicts before silently compensating for them.
5. Implement the smallest working vertical slice.
6. Add tests for core domain rules.
7. Run tests after changes.

Do not implement the full project in one uncontrolled pass.

Prefer the following implementation order:

1. master loading and validation
2. run snapshots
3. scenario generation
4. balanced assignment
5. local SQLite prototype
6. Streamlit UI
7. Supabase integration
8. final training export
9. synthetic-data extension

## 7. Required tests

At minimum, test:

- required Excel sheets exist
- store_id is unique
- origin-store references are valid
- route references are valid
- self-routes are absent
- scenario conditional fields are valid
- accepted labels have null rejection reasons
- rejected labels use an allowed rejection reason
- unexposed stores do not become negative labels
- each annotator receives the configured number of assignments
- store exposure counts are reasonably balanced
- overnight opening hours are calculated correctly
- a master snapshot remains unchanged after the live master is updated

## 8. Definition of done

A feature is complete only when:

- code is implemented
- tests are added
- tests pass
- relevant documentation is updated
- no secret or generated personal data is committed
