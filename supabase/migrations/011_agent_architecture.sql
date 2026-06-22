-- Phase 1.6: Agent Architecture Refactor
-- Adds department manager state, agent micro-scheduling, business pause flag, and approval queue.

-- ── Department manager state ───────────────────────────────────────────────────
ALTER TABLE departments
  ADD COLUMN IF NOT EXISTS status_narrative       TEXT,
  ADD COLUMN IF NOT EXISTS manager_chat_history   JSONB NOT NULL DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS last_run_at            TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_run_status        TEXT,
  ADD COLUMN IF NOT EXISTS manager_next_eval_at   TIMESTAMPTZ;

-- ── Agent micro-scheduling: tasks can request a resume time ───────────────────
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS resume_at TIMESTAMPTZ;

-- ── Business-level pause flag ─────────────────────────────────────────────────
ALTER TABLE businesses
  ADD COLUMN IF NOT EXISTS is_paused BOOLEAN NOT NULL DEFAULT false;

-- ── Dedicated approval queue ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS approval_queue (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   UUID        NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  dept_type     TEXT        NOT NULL,
  action_type   TEXT        NOT NULL,           -- e.g. 'send_emails', 'publish_articles'
  payload       JSONB       NOT NULL DEFAULT '{}',
  status        TEXT        NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
  reject_reason TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at   TIMESTAMPTZ,
  resolved_by   UUID        REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS approval_queue_business_status
  ON approval_queue(business_id, status);

CREATE INDEX IF NOT EXISTS approval_queue_pending
  ON approval_queue(business_id)
  WHERE status = 'pending';
