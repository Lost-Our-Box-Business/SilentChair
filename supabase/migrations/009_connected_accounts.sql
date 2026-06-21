-- Connected Accounts: OAuth tokens for social and ad platform integrations.
-- Used by Marketing, Advertising, and Sales departments when connecting
-- platforms like Instagram, Facebook, Google Ads, Buffer, WordPress, etc.

create table if not exists connected_accounts (
  id               uuid        primary key default gen_random_uuid(),
  user_id          uuid        not null references auth.users(id) on delete cascade,
  business_id      uuid        references businesses(id) on delete cascade,
  platform         text        not null,  -- 'instagram'|'facebook'|'google_ads'|'meta_ads'|
                                          -- 'wordpress'|'ghost'|'buffer'|'linkedin'|'x'|'tiktok'
  access_token     text,
  refresh_token    text,
  token_expires_at timestamptz,
  account_name     text,
  account_id       text,
  metadata         jsonb       default '{}'::jsonb,
  is_active        boolean     not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  unique (user_id, business_id, platform)
);

create index if not exists connected_accounts_user_idx     on connected_accounts(user_id);
create index if not exists connected_accounts_business_idx on connected_accounts(business_id);

alter table connected_accounts enable row level security;

create policy "users manage own connected accounts"
  on connected_accounts for all
  using (user_id = auth.uid());
