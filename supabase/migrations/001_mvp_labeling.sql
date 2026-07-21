-- MUMUT MVP central-labeling schema. Run this once in Supabase SQL Editor.
create table if not exists public.runs (
  run_id text primary key,
  master_sha256 text not null,
  manifest jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.assignments (
  assignment_id text primary key,
  run_id text not null references public.runs(run_id),
  scenario_id text not null,
  annotator_id text not null check (annotator_id in ('A01', 'A02', 'A03')),
  shown_store_id text not null,
  snapshot jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists assignments_run_annotator_idx on public.assignments(run_id, annotator_id, assignment_id);

create table if not exists public.labels (
  assignment_id text primary key references public.assignments(assignment_id),
  outcome text not null check (outcome in ('ACCEPTED', 'REJECTED')),
  reject_reason_code text,
  status text not null default 'COMPLETED' check (status in ('COMPLETED', 'INVALIDATED')),
  labeled_at timestamptz not null default now(),
  check ((outcome = 'ACCEPTED' and reject_reason_code is null) or (outcome = 'REJECTED' and reject_reason_code in ('TOO_FAR', 'PRICE_BURDEN', 'MISMATCH', 'INFO_INSUFFICIENT', 'PARKING_TIGHT')))
);

create table if not exists public.label_events (
  event_id bigint generated always as identity primary key,
  assignment_id text not null references public.assignments(assignment_id),
  event_type text not null,
  event_data jsonb,
  created_at timestamptz not null default now()
);

create or replace function public.submit_label(
  p_assignment_id text,
  p_annotator_id text,
  p_outcome text,
  p_reject_reason_code text default null
) returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_annotator_id text;
begin
  select annotator_id into v_annotator_id from assignments where assignment_id = p_assignment_id;
  if v_annotator_id is null then raise exception 'Unknown or unexposed assignment'; end if;
  if v_annotator_id <> p_annotator_id then raise exception 'Assignment belongs to a different annotator'; end if;
  if exists (select 1 from labels where assignment_id = p_assignment_id) then raise exception 'Assignment already labeled'; end if;
  if p_outcome not in ('ACCEPTED', 'REJECTED') then raise exception 'Invalid outcome'; end if;
  if p_outcome = 'ACCEPTED' and p_reject_reason_code is not null then raise exception 'ACCEPTED must not have a rejection reason'; end if;
  if p_outcome = 'REJECTED' and p_reject_reason_code not in ('TOO_FAR', 'PRICE_BURDEN', 'MISMATCH', 'INFO_INSUFFICIENT', 'PARKING_TIGHT') then raise exception 'REJECTED needs an allowed rejection reason'; end if;
  insert into labels (assignment_id, outcome, reject_reason_code) values (p_assignment_id, p_outcome, p_reject_reason_code);
  insert into label_events (assignment_id, event_type, event_data) values (p_assignment_id, 'LABEL_SUBMITTED', jsonb_build_object('outcome', p_outcome, 'reject_reason_code', p_reject_reason_code));
end;
$$;

-- The Streamlit server uses the service-role key, kept only in deployment secrets.
-- Do not expose this key in a browser, source code, or a committed file.
alter table public.runs enable row level security;
alter table public.assignments enable row level security;
alter table public.labels enable row level security;
alter table public.label_events enable row level security;
