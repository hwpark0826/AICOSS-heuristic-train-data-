-- Apply this once to an existing Supabase project that already ran 001.
alter table public.labels add column if not exists mismatch_detail_code text;

-- Preserve any historical parking labels as a condition mismatch before the
-- old constraint is replaced. Current MVP runs have no labels yet.
update public.labels
set reject_reason_code = 'MISMATCH', mismatch_detail_code = 'PARKING_MISMATCH'
where reject_reason_code = 'PARKING_TIGHT';

do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select conname
    from pg_constraint
    where conrelid = 'public.labels'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%reject_reason_code%'
  loop
    execute format('alter table public.labels drop constraint %I', constraint_name);
  end loop;
end $$;

alter table public.labels
add constraint labels_reject_reason_payload_check check (
  (outcome = 'ACCEPTED' and reject_reason_code is null and mismatch_detail_code is null)
  or (outcome = 'REJECTED' and (
    (reject_reason_code = 'MISMATCH' and mismatch_detail_code in ('PURPOSE_MISMATCH', 'ATMOSPHERE_MISMATCH', 'PROFILE_MISMATCH', 'HILL_MISMATCH', 'PARKING_MISMATCH', 'OTHER_CONDITION_MISMATCH'))
    or (reject_reason_code in ('TOO_FAR', 'PRICE_BURDEN', 'INFO_INSUFFICIENT', 'LOW_APPEAL') and mismatch_detail_code is null)
  ))
);

create or replace function public.submit_label(
  p_assignment_id text,
  p_annotator_id text,
  p_outcome text,
  p_reject_reason_code text default null,
  p_mismatch_detail_code text default null
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
  if p_outcome = 'ACCEPTED' and (p_reject_reason_code is not null or p_mismatch_detail_code is not null) then raise exception 'ACCEPTED must not have rejection details'; end if;
  if p_outcome = 'REJECTED' and p_reject_reason_code not in ('TOO_FAR', 'PRICE_BURDEN', 'MISMATCH', 'INFO_INSUFFICIENT', 'LOW_APPEAL') then raise exception 'REJECTED needs an allowed rejection reason'; end if;
  if p_reject_reason_code = 'MISMATCH' and p_mismatch_detail_code not in ('PURPOSE_MISMATCH', 'ATMOSPHERE_MISMATCH', 'PROFILE_MISMATCH', 'HILL_MISMATCH', 'PARKING_MISMATCH', 'OTHER_CONDITION_MISMATCH') then raise exception 'MISMATCH needs an allowed condition detail'; end if;
  if p_reject_reason_code <> 'MISMATCH' and p_mismatch_detail_code is not null then raise exception 'Only MISMATCH may have a condition detail'; end if;
  insert into labels (assignment_id, outcome, reject_reason_code, mismatch_detail_code) values (p_assignment_id, p_outcome, p_reject_reason_code, p_mismatch_detail_code);
  insert into label_events (assignment_id, event_type, event_data) values (p_assignment_id, 'LABEL_SUBMITTED', jsonb_build_object('outcome', p_outcome, 'reject_reason_code', p_reject_reason_code, 'mismatch_detail_code', p_mismatch_detail_code));
end;
$$;
