-- Migration 010: task assignee field
-- assigned_to: 'agent' = pipeline picks it up, 'user' = user handles manually

alter table tasks
  add column if not exists assigned_to text not null default 'agent';

-- Back-fill: user-created tasks were always meant for the user
update tasks set assigned_to = 'user' where created_by = 'user';
