create table if not exists websites (
  id              uuid        primary key default gen_random_uuid(),
  business_id     uuid        not null references businesses(id) on delete cascade,
  subdomain       text        unique not null,
  custom_domain   text,
  files           jsonb       not null default '[]'::jsonb,
  chat_history    jsonb       not null default '[]'::jsonb,
  published_url   text,
  status          text        not null default 'draft',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists websites_business_idx on websites(business_id);
create index if not exists websites_subdomain_idx on websites(subdomain);

alter table websites enable row level security;

create policy "users manage their websites"
  on websites for all
  using (business_id in (select id from businesses where user_id = auth.uid()));
