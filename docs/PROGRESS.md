# SilentChair — Roadmap Progress

> Updated automatically after each roadmap task is completed.
> Mirrors the structure in `ROADMAP.md`. Add a completion date and brief note for each item.

---

## Standing Rules (Lessons Learned — Always Follow)

Rules discovered from real bugs. Check this before writing new components or backend logic.

### TypeScript / React

- **`!!` prefix for `unknown` fields in JSX conditions.** Any field from a `Record<string, unknown>` type (e.g., `lead.email`, `mr?.icp`) is typed `unknown`. Using it directly as a JSX condition (e.g., `{lead.email && <p>…</p>}`) causes a Vercel build error: `Type 'unknown' is not assignable to type 'ReactNode'`. Always write `{!!lead.email && <p>…</p>}`. Affects any component that renders dynamic data from JSONB columns.

- **Check `frontend/components/ui/` before importing a UI component.** Not all shadcn components are installed. If a component file doesn't exist there, use a native HTML element instead (e.g., `<input type="checkbox">` instead of `<Checkbox>`).

### Backend / LLM

- **Strip markdown code fences before `json.loads()`.** Claude models sometimes wrap JSON output in ` ```json … ``` ` even when instructed not to. Always strip fences before parsing. Pattern:
  ```python
  clean = raw.strip()
  if clean.startswith("```"):
      lines = clean.splitlines()
      inner = lines[1:] if len(lines) > 1 else lines
      if inner and inner[-1].strip() == "```":
          inner = inner[:-1]
      clean = "\n".join(inner).strip()
  parsed = json.loads(clean)
  ```

- **After creating a task from manager chat, trigger evaluation immediately.** Inserting a `planned` task row does not execute it — the background scheduler only fires on its own cadence. After any `create_task` action in `department_manager.chat()`, spin up a background thread to call `evaluate()` then `run_task()` so the agent picks it up right away.

### Git / Deployment

- **Always update `PROGRESS.md` before committing roadmap work.** CLAUDE.md rule. Prior sessions missed this for out-of-band fixes; they had to be added retroactively in separate commits.

---

## Pre-Roadmap Baseline (Live at June 2026)

These were already built and deployed before the roadmap was written.

| Feature | Status | Notes |
|---|---|---|
| Google + email auth | ✅ Live | OAuth redirect fixed |
| Business interview (onboarding chat) | ✅ Live | Multi-turn AI, saves to `businesses` table |
| Business profile storage | ✅ Live | Static JSON in `businesses.profile` |
| Department suggestion + hiring flow | ✅ Live | UI + content agency archetype wired |
| Budget allocation by department | ✅ Live | |
| Content agency pipeline | ✅ Live | Research → write → publish |
| Activity feed + approval queue | ✅ Live | Feed exists; approval buttons in departments page |
| Website builder | ✅ Live | Subdomain hosting at `{slug}.silentchair.app` |
| Serper web search | ✅ Live | |
| Resend email | ✅ Live | |
| Dashboard + business detail page | ✅ Live | |
| Stub pages (agents, tasks, analytics, settings) | ✅ Live | Placeholders only |

---

## Phase 1 — Platform Foundation

### 1.1 Living Business Document
- [ ] Not started

### 1.2 Dollar Balance System
- [ ] Not started

### 1.3 Task Board
- [ ] Not started

### 1.4 Stripe Billing
- [ ] Not started

### 1.5 Language / i18n
- [ ] Not started

### 1.6 Agent Architecture Refactor
- **Status:** Mostly complete (2026-06-28)
- [x] `BaseDepartmentAgent` — reads business context, checks credits, logs activity, handles approval queue inserts
- [x] `DepartmentRunner` — AGENT_REGISTRY, `run_task()`, `tick()`, `start()`, `pause()`, `resume()`
- [x] `DepartmentManager` — macro-scheduler; evaluates tasks and schedules via `manager_next_eval_at`
- [x] `ApprovalQueue` backend — `list_pending`, `approve`, `reject`; API endpoints in `routers/agents.py`
- [x] Per-dept schedules stored in DB (`departments.manager_next_eval_at`)
- [x] Background dispatcher — replaced Celery+Redis with APScheduler + `threading.Timer` (2026-06-28)
- [ ] User-configurable schedules UI (let users set when each dept runs)
- [x] "Edit" action in approval flow — edit-and-approve mode in `ApprovalReviewSheet`; only shown when `task.output_meta.queue_id` exists. `ApprovalEditForm` handles per-type editing (email subjects, article titles/slugs, lead include/exclude). Saves edited payload via `PATCH /api/tasks/{id}/approval-content` before approving. (2026-07-10)
- [x] Standalone approval queue page — `/dashboard/business/[businessId]/approvals`; polls every 15s; amber card per pending task; opens `ApprovalReviewSheet` inline; Approvals sub-item added to sidebar for all 6 locales. (2026-07-10)

### 1.7 Website Builder Quality Upgrade
- [ ] Not started — implementation plan: [docs/plans/1.7-website-builder.md](plans/1.7-website-builder.md)

---

## Phase 2 — Core Departments

### 2.1 Marketing Department
- [ ] Not started

### 2.2 Business Advisor Department
- [ ] Not started

### 2.3 Financial Advisor Department
- [ ] Not started

### 2.4 Client Acquisition Department
- [ ] Not started

### 2.5 Sales Department
- [ ] Not started

### 2.6 Customer Service Department
- [ ] Not started

### 2.7 Advertising Department
- [ ] Not started

---

## Phase 3 — Human Coaching and Connected Accounts

### 3.1 Coach Scheduling
- [ ] Not started

### 3.2 Connected Accounts
- [ ] Not started

### 3.3 Bring-Your-Own Keys (BYOK)
- [ ] Not started

---

## Phase 4 — Beta and Hardening

### 4.1 Private Beta
- [ ] Not started

### 4.2 Dollar Balance Calibration
- [ ] Not started

### 4.3 Scale Testing
- [ ] Not started

### 4.4 Security Review
- [ ] Not started

### 4.5 Payment Testing
- [ ] Not started

---

## Phase 5 — Public Launch
- [ ] Not started

## Phase 6 — V1.1 (Post-Launch)
- [ ] Not started

---

## Out-of-Band Fixes (not in roadmap)

| Date | Fix | Files |
|---|---|---|
| 2026-06-28 | Lead gen agent now reads assigned task from DB; stops fabricating contact names/emails | `agents/departments/lead_generation.py`, `services/department_runner.py`, `agents/lead_gen_pipeline.py` |
| 2026-06-28 | Replaced Celery+Redis with APScheduler+threading to eliminate Upstash command limit exhaustion | `app/scheduler.py`, `app/worker.py`, `app/tasks/pipeline.py`, `services/department_runner.py`, `requirements.txt` |
| 2026-07-10 | Added ApprovalReviewSheet — "Blocked by User" tasks now show full content preview (emails, leads, articles) before approve/decline. Base agent stores `queue_id` in `tasks.output_meta`; `approve_task()` routes through `approval_queue.approve()`; decline fires immediate agent retry with rejection notes prepended. | `agents/departments/base.py`, `routers/tasks.py`, `frontend/components/tasks/ApprovalReviewSheet.tsx`, `ApprovalDetail.tsx`, `TaskCard.tsx`, `lib/tasks-api.ts` |
| 2026-07-10 | Fixed pending approvals not clearing after task board approval — dashboard now queries `tasks` with `status=awaiting_approval` (same source as task board) and refetches on tab visibility change. | `frontend/app/dashboard/business/[businessId]/page.tsx` |
| 2026-07-10 | Activity feed cards are now expandable — click any card to see structured step data (companies found, lead scores/rejection reasons, ICP, email drafts). Backend now attaches structured `detail` to each pipeline log entry via `_detail_for_log_entry()`. Dept entries show "Discuss with manager →" link. | `services/activity.py`, `frontend/lib/activity-api.ts`, `frontend/app/dashboard/business/[businessId]/page.tsx`, `frontend/components/activity/ActivityDetailPanel.tsx` |
