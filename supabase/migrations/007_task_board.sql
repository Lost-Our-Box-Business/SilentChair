-- Task Board: expand the existing tasks table with department, cost tracking,
-- labels, Task Board status values, and activity link for approval flow.

alter table tasks drop constraint if exists tasks_status_check;
update tasks set status = 'planned' where status = 'pending';
alter table tasks add constraint tasks_status_check
  check (status in ('planned', 'in_progress', 'awaiting_approval', 'completed', 'failed'));

alter table tasks
  add column if not exists department      text,
  add column if not exists cost_usd        numeric(12,8) default 0,
  add column if not exists label_color     text,
  add column if not exists created_by      text default 'agent',
  add column if not exists approved_by     uuid references auth.users(id),
  add column if not exists activity_log_id uuid references activity_log(id) on delete set null;

create index if not exists tasks_status_idx on tasks(business_id, status);
create index if not exists tasks_dept_idx   on tasks(business_id, department, created_at desc);
