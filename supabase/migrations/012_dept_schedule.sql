-- Phase 1.6: User-configurable department schedules
-- Adds schedule_config JSONB to departments. NULL = manager-controlled (default).
--
-- Supported shapes:
--   {"type": "interval", "hours": N}      -- run every N hours
--   {"type": "daily",    "hour":  N}      -- run daily at N:00 UTC
--   {"type": "weekdays", "hour":  N}      -- run Mon-Fri at N:00 UTC

ALTER TABLE departments
  ADD COLUMN IF NOT EXISTS schedule_config JSONB DEFAULT NULL;
