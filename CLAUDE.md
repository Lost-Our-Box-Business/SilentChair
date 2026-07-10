# SilentChair — Claude Instructions

## Project Overview

AI business workforce SaaS. Users hire AI departments (Marketing, Sales, Lead Gen, etc.) that run autonomously on a schedule. MVP archetype is a content agency.

- **Backend:** FastAPI + LangGraph + Anthropic Claude, deployed on Railway
- **Frontend:** Next.js (App Router) + Tailwind, deployed on Vercel
- **DB:** Supabase (Postgres + Auth + Storage)
- **Scheduler:** APScheduler + `threading.Timer` (replaced Celery+Redis)
- **Docs:** `docs/` — ROADMAP.md, PROGRESS.md, ARCHITECTURE.md, V1_SPEC.md, VISION.md

## Progress Tracking Rule

**Before starting any roadmap work, read `docs/PROGRESS.md` to understand what's already done and what gaps remain. Never assume — check the file.**

**After completing any roadmap task — a numbered item (1.1, 1.2, 2.3, etc.) or a full phase — update `docs/PROGRESS.md` immediately.**

How to update it:
- Mark completed sub-bullets with `[x]`
- Add a completion date next to the section heading: `- **Status:** Complete (YYYY-MM-DD)`
- If a section is only partially done, list the remaining gaps as `[ ]` items
- For out-of-band fixes (bugs, infra changes not in the roadmap), add a row to the "Out-of-Band Fixes" table at the bottom

Do this before committing — the commit message and `PROGRESS.md` update go together.

## Key Conventions

- All agent classes extend `BaseDepartmentAgent` (`backend/app/agents/departments/base.py`)
- All agent execution goes through `DepartmentRunner.run_task()` (`backend/app/services/department_runner.py`)
- Background tick runs every 5 min via `python -m app.scheduler` (Railway: `eloquent-fulfillment` service)
- Task state lives in the `tasks` Supabase table; department state in `departments`
- Cost tracking goes through `app/services/cost_tracker.py`; never deduct spend manually
- Approval flow: agent calls `self.request_approval()` → inserts to `approval_queue` → task status = `awaiting_approval` → user approves via dashboard → `approval_queue.approve()` executes the action
