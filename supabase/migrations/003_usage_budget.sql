-- Add budget columns to businesses
alter table businesses
  add column if not exists daily_budget numeric(10, 4),
  add column if not exists dept_budgets jsonb default '{}'::jsonb;

-- Drop and recreate usage_events to guarantee correct schema
drop table if exists usage_events cascade;

create table usage_events (
  id                uuid        primary key default gen_random_uuid(),
  business_id       uuid        not null references businesses(id) on delete cascade,
  dept_type         text,
  model             text        not null default 'claude-opus-4-7',
  event_type        text        not null default 'llm_call',
  input_tokens      integer     not null default 0,
  output_tokens     integer     not null default 0,
  cache_read_tokens integer     not null default 0,
  cache_write_tokens integer    not null default 0,
  cost_usd          numeric(12, 8) not null default 0,
  created_at        timestamptz not null default now()
);

create index usage_events_business_date_idx
  on usage_events(business_id, created_at desc);

create index usage_events_dept_idx
  on usage_events(business_id, dept_type, created_at desc);

alter table usage_events enable row level security;

create policy "users manage their usage_events"
  on usage_events for all
  using (business_id in (select id from businesses where user_id = auth.uid()));
