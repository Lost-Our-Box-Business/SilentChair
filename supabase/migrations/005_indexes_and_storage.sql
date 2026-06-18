-- Performance indexes on frequently-queried foreign keys.
-- Every RLS policy resolves business ownership via businesses.user_id;
-- without this index each policy check is a full table scan.

create index if not exists businesses_user_id_idx      on businesses(user_id);
create index if not exists departments_business_idx    on departments(business_id);
create index if not exists agents_business_idx         on agents(business_id);
create index if not exists agent_tools_business_idx    on agent_tools(business_id);
create index if not exists tasks_business_idx          on tasks(business_id);
create index if not exists activity_log_business_idx   on activity_log(business_id);
create index if not exists notifications_business_idx  on notifications(business_id);
create index if not exists leads_business_idx          on leads(business_id);
create index if not exists contracts_business_idx      on contracts(business_id);
create index if not exists invoices_business_idx       on invoices(business_id);

-- NOTE: The Supabase Storage bucket "websites" must be created manually.
-- Go to Storage → New bucket → name: "websites" → Public: ON
-- This cannot be done via SQL migration.
