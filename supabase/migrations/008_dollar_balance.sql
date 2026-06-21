-- Dollar Balance System: per-user subscription balance and full spend audit ledger.
-- usage_events (existing) tracks token-level detail; this adds the account balance layer.

create table if not exists user_balances (
  id                      uuid        primary key default gen_random_uuid(),
  user_id                 uuid        not null unique references auth.users(id) on delete cascade,
  balance_usd             numeric(12,2) not null default 0,
  monthly_grant_usd       numeric(10,2) not null default 0,
  subscription_tier       text        default 'trial',  -- 'trial'|'starter'|'growth'|'scale'|'enterprise'
  stripe_customer_id      text        unique,
  stripe_subscription_id  text        unique,
  trial_ends_at           timestamptz,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);

alter table user_balances enable row level security;

-- Users can read their own balance; backend (service role) handles writes
create policy "users read own balance"
  on user_balances for select
  using (user_id = auth.uid());

create table if not exists spend_ledger (
  id            uuid          primary key default gen_random_uuid(),
  user_id       uuid          not null references auth.users(id) on delete cascade,
  business_id   uuid          references businesses(id) on delete set null,
  task_id       uuid          references tasks(id) on delete set null,
  amount_usd    numeric(12,8) not null,   -- positive = credit, negative = debit
  type          text          not null check (type in ('subscription_grant', 'top_up', 'debit', 'refund')),
  description   text,
  balance_after numeric(12,2),
  created_at    timestamptz   not null default now()
);

create index if not exists spend_ledger_user_idx     on spend_ledger(user_id, created_at desc);
create index if not exists spend_ledger_business_idx on spend_ledger(business_id, created_at desc);

alter table spend_ledger enable row level security;

create policy "users read own ledger"
  on spend_ledger for select
  using (user_id = auth.uid());
