-- SilentChair initial schema
-- Run this in your Supabase SQL editor or via supabase db push

-- Enable pgvector for agent memory
create extension if not exists vector;

-- ─────────────────────────────────────────────
-- businesses
-- ─────────────────────────────────────────────
create table if not exists businesses (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  name          text not null default 'Untitled Business',
  status        text not null default 'onboarding'
                  check (status in ('onboarding','active','paused','archived')),
  profile       jsonb,                    -- structured business profile from interview
  autonomy      text not null default 'major_decisions'
                  check (autonomy in ('full_auto','major_decisions','step_by_step')),
  comm_channel  text default 'email'
                  check (comm_channel in ('email','slack','discord','sms')),
  comm_config   jsonb default '{}'::jsonb, -- channel-specific config (webhook url, phone, etc.)
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- ─────────────────────────────────────────────
-- departments
-- ─────────────────────────────────────────────
create table if not exists departments (
  id            uuid primary key default gen_random_uuid(),
  business_id   uuid not null references businesses(id) on delete cascade,
  name          text not null,
  dept_type     text not null,  -- editorial, seo, social_media, distribution, analytics
  description   text,
  is_active     boolean default false,
  is_required   boolean default false,
  created_at    timestamptz default now()
);

-- ─────────────────────────────────────────────
-- agents
-- ─────────────────────────────────────────────
create table if not exists agents (
  id              uuid primary key default gen_random_uuid(),
  business_id     uuid not null references businesses(id) on delete cascade,
  department_id   uuid references departments(id) on delete set null,
  name            text not null,
  role            text not null,  -- manager, writer, researcher, etc.
  agent_type      text not null,  -- business_analyst, content_director, seo_strategist, etc.
  system_prompt   text,
  model           text default 'claude-sonnet-4-6',
  is_active       boolean default true,
  config          jsonb default '{}'::jsonb,
  created_at      timestamptz default now()
);

-- ─────────────────────────────────────────────
-- agent_tools
-- ─────────────────────────────────────────────
create table if not exists agent_tools (
  id              uuid primary key default gen_random_uuid(),
  business_id     uuid not null references businesses(id) on delete cascade,
  agent_id        uuid references agents(id) on delete cascade,
  tool_name       text not null,   -- serper, buffer, wordpress, anthropic, etc.
  key_source      text not null default 'platform'
                    check (key_source in ('platform','user')),
  encrypted_key   text,            -- only set when key_source = 'user'
  is_active       boolean default true,
  created_at      timestamptz default now()
);

-- ─────────────────────────────────────────────
-- tasks
-- ─────────────────────────────────────────────
create table if not exists tasks (
  id              uuid primary key default gen_random_uuid(),
  business_id     uuid not null references businesses(id) on delete cascade,
  agent_id        uuid references agents(id) on delete set null,
  title           text not null,
  description     text,
  status          text not null default 'pending'
                    check (status in ('pending','in_progress','awaiting_approval','completed','failed')),
  output          text,
  output_meta     jsonb,
  created_at      timestamptz default now(),
  completed_at    timestamptz
);

-- ─────────────────────────────────────────────
-- memory_chunks (agent long-term memory)
-- ─────────────────────────────────────────────
create table if not exists memory_chunks (
  id              uuid primary key default gen_random_uuid(),
  business_id     uuid not null references businesses(id) on delete cascade,
  agent_id        uuid references agents(id) on delete cascade,
  content         text not null,
  embedding       vector(1536),
  metadata        jsonb default '{}'::jsonb,
  created_at      timestamptz default now()
);

create index if not exists memory_chunks_embedding_idx
  on memory_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- ─────────────────────────────────────────────
-- activity_log
-- ─────────────────────────────────────────────
create table if not exists activity_log (
  id                  uuid primary key default gen_random_uuid(),
  business_id         uuid not null references businesses(id) on delete cascade,
  agent_id            uuid references agents(id) on delete set null,
  action_type         text not null,  -- content_published, research_completed, etc.
  summary             text,
  detail              jsonb,
  requires_approval   boolean default false,
  approved_by         uuid references auth.users(id),
  approved_at         timestamptz,
  created_at          timestamptz default now()
);

-- ─────────────────────────────────────────────
-- notifications
-- ─────────────────────────────────────────────
create table if not exists notifications (
  id              uuid primary key default gen_random_uuid(),
  business_id     uuid not null references businesses(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  channel         text not null,
  title           text,
  content         text not null,
  status          text default 'pending' check (status in ('pending','sent','failed')),
  sent_at         timestamptz,
  created_at      timestamptz default now()
);

-- ─────────────────────────────────────────────
-- usage_events (for billing)
-- ─────────────────────────────────────────────
create table if not exists usage_events (
  id              uuid primary key default gen_random_uuid(),
  business_id     uuid not null references businesses(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  event_type      text not null check (event_type in ('token','action','api_call')),
  units           integer not null default 1,
  cost_usd        numeric(10,6) default 0,
  metadata        jsonb,
  created_at      timestamptz default now()
);

-- ─────────────────────────────────────────────
-- Row Level Security
-- ─────────────────────────────────────────────
alter table businesses     enable row level security;
alter table departments    enable row level security;
alter table agents         enable row level security;
alter table agent_tools    enable row level security;
alter table tasks          enable row level security;
alter table memory_chunks  enable row level security;
alter table activity_log   enable row level security;
alter table notifications  enable row level security;
alter table usage_events   enable row level security;

-- Users can only see their own data
create policy "users_own_businesses"     on businesses     for all using (auth.uid() = user_id);
create policy "users_own_departments"    on departments    for all using (business_id in (select id from businesses where user_id = auth.uid()));
create policy "users_own_agents"         on agents         for all using (business_id in (select id from businesses where user_id = auth.uid()));
create policy "users_own_agent_tools"    on agent_tools    for all using (business_id in (select id from businesses where user_id = auth.uid()));
create policy "users_own_tasks"          on tasks          for all using (business_id in (select id from businesses where user_id = auth.uid()));
create policy "users_own_memory_chunks"  on memory_chunks  for all using (business_id in (select id from businesses where user_id = auth.uid()));
create policy "users_own_activity_log"   on activity_log   for all using (business_id in (select id from businesses where user_id = auth.uid()));
create policy "users_own_notifications"  on notifications  for all using (user_id = auth.uid());
create policy "users_own_usage_events"   on usage_events   for all using (user_id = auth.uid());

-- ─────────────────────────────────────────────
-- updated_at trigger
-- ─────────────────────────────────────────────
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger businesses_updated_at
  before update on businesses
  for each row execute function update_updated_at();
