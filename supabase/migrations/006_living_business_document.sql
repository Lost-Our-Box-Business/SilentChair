-- Living Business Document: adds dynamic business context to businesses table
-- and creates version history for auditing/rollback.

alter table businesses
  add column if not exists business_context jsonb default '{}'::jsonb,
  add column if not exists business_context_updated_at timestamptz,
  add column if not exists notify_blocked boolean not null default true;

create table if not exists business_context_history (
  id                uuid        primary key default gen_random_uuid(),
  business_id       uuid        not null references businesses(id) on delete cascade,
  context_snapshot  jsonb       not null,
  change_summary    text,
  triggered_by      text,       -- 'interview' | 'agent' | 'user_correction'
  created_at        timestamptz not null default now()
);

create index if not exists bch_business_idx
  on business_context_history(business_id, created_at desc);

alter table business_context_history enable row level security;

create policy "users own context history"
  on business_context_history for all
  using (business_id in (select id from businesses where user_id = auth.uid()));
