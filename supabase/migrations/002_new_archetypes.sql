-- Migration 002: multi-archetype support
-- Adds archetype to businesses, and leads / contracts / invoices tables.

-- ─────────────────────────────────────────────
-- archetype column on businesses
-- ─────────────────────────────────────────────
alter table businesses
  add column if not exists archetype text not null default 'content_agency'
    check (archetype in ('content_agency','lead_generation','client_acquisition'));

-- ─────────────────────────────────────────────
-- leads
-- ─────────────────────────────────────────────
create table if not exists leads (
  id            uuid primary key default gen_random_uuid(),
  business_id   uuid not null references businesses(id) on delete cascade,
  name          text not null,
  company       text,
  email         text,
  phone         text,
  source        text,           -- how the lead was found (serper search, etc.)
  status        text not null default 'new'
                  check (status in ('new','contacted','qualified','proposal_sent','won','lost')),
  score         integer,        -- 1-10 qualification score
  notes         text,
  created_at    timestamptz default now()
);

-- ─────────────────────────────────────────────
-- contracts
-- ─────────────────────────────────────────────
create table if not exists contracts (
  id            uuid primary key default gen_random_uuid(),
  business_id   uuid not null references businesses(id) on delete cascade,
  lead_id       uuid references leads(id) on delete set null,
  title         text not null,
  content       text not null,  -- full HTML document
  status        text not null default 'draft'
                  check (status in ('draft','sent','signed')),
  created_at    timestamptz default now()
);

-- ─────────────────────────────────────────────
-- invoices
-- ─────────────────────────────────────────────
create table if not exists invoices (
  id            uuid primary key default gen_random_uuid(),
  business_id   uuid not null references businesses(id) on delete cascade,
  lead_id       uuid references leads(id) on delete set null,
  contract_id   uuid references contracts(id) on delete set null,
  title         text not null,
  content       text not null,  -- full HTML invoice
  amount        numeric(10,2) default 0,
  status        text not null default 'draft'
                  check (status in ('draft','sent','paid')),
  created_at    timestamptz default now()
);

-- ─────────────────────────────────────────────
-- Row Level Security
-- ─────────────────────────────────────────────
alter table leads      enable row level security;
alter table contracts  enable row level security;
alter table invoices   enable row level security;

create policy "users_own_leads"
  on leads for all
  using (business_id in (select id from businesses where user_id = auth.uid()));

create policy "users_own_contracts"
  on contracts for all
  using (business_id in (select id from businesses where user_id = auth.uid()));

create policy "users_own_invoices"
  on invoices for all
  using (business_id in (select id from businesses where user_id = auth.uid()));
