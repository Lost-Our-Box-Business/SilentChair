# SilentChair — Platform Architecture

> Last updated: 2026-06-21

---

## Stack Overview

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 + TypeScript + shadcn/ui + Tailwind CSS |
| Backend | FastAPI (Python) + LangGraph |
| Database | Supabase (PostgreSQL + pgvector + Auth + Storage) |
| Task Queue | Celery + Upstash Redis |
| AI Models | Anthropic Claude (Sonnet for reasoning, Haiku for fast tasks) |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway (FastAPI + Celery worker as separate services) |
| Payments | Stripe |
| Email | Resend |
| Monitoring | Sentry + PostHog |

---

## Core Design Principles

1. **Wrap, don't rewrite.** Existing pipeline files are never modified. New departments wrap them via `BaseDepartmentAgent`.
2. **Add columns, never remove.** Every DB migration is additive-only. Existing queries always work.
3. **New routers, not modified routes.** New capabilities live in new files; existing API contracts don't change.
4. **One interface, many departments.** `BaseDepartmentAgent` is the only contract new departments implement.
5. **Async by default.** Agent work runs in Celery background tasks, never in the user's request cycle.

---

## Backend Structure

```
backend/app/
├── main.py                        # FastAPI app; registers all routers
├── config.py                      # Pydantic Settings (env vars)
├── worker.py                      # Celery app instance (broker: Upstash Redis)
│
├── db/client.py                   # Supabase client singleton (service role)
│
├── models/                        # Pydantic request/response schemas
│   ├── interview.py
│   ├── departments.py
│   ├── website.py
│   ├── tasks.py                   # Task Board models
│   ├── billing.py                 # Balance, subscription, spend ledger models
│   └── coaching.py                # Coach session models
│
├── agents/
│   ├── business_analyst.py        # Interview LangGraph agent
│   ├── department_suggester.py    # Archetype detection + dept catalog
│   ├── content_pipeline.py        # Content agency LangGraph pipeline (do not modify)
│   ├── lead_gen_pipeline.py       # Lead gen LangGraph pipeline (do not modify)
│   ├── client_acquisition_pipeline.py  # Client acq pipeline (do not modify)
│   ├── website_builder.py         # Website builder agent
│   └── departments/               # Modular department agent system
│       ├── base.py                # BaseDepartmentAgent abstract class
│       ├── marketing.py           # Wraps content_pipeline
│       ├── lead_generation.py     # Wraps lead_gen_pipeline
│       ├── client_acquisition.py  # Wraps client_acquisition_pipeline
│       ├── business_advisor.py
│       ├── financial_advisor.py
│       ├── sales.py
│       ├── customer_service.py
│       └── advertising.py
│
├── routers/                       # FastAPI route handlers (one file per resource)
│   ├── interview.py               # POST /api/interview/turn, GET /api/interview/session/{id}
│   ├── departments.py             # /api/departments/*
│   ├── activity.py                # /api/activity/*, /api/pipeline/*
│   ├── crm.py                     # /api/crm/*
│   ├── usage.py                   # /api/usage/* (legacy budget endpoints)
│   ├── website.py                 # /api/website/*
│   ├── tasks.py                   # /api/tasks/*
│   ├── balance.py                 # /api/balance/*
│   ├── billing.py                 # /api/billing/*
│   ├── webhooks.py                # /api/webhooks/stripe, /api/webhooks/calendly
│   ├── coaching.py                # /api/coaching/*
│   └── settings.py                # /api/settings/*
│
├── services/                      # Business logic (not HTTP-aware)
│   ├── activity.py                # Activity logging + notifications
│   ├── cost_tracker.py            # Token cost calculation + usage_events writes
│   ├── living_doc.py              # Living Business Document CRUD + versioning
│   ├── balance.py                 # Dollar balance: deduct, grant, check
│   └── stripe_service.py          # Stripe API wrapper (checkout, portal, webhooks)
│
└── tools/                         # External API wrappers
    ├── serper.py                  # Google Search
    ├── crm.py                     # leads/contracts/invoices DB helpers
    ├── email_outreach.py          # Resend email
    ├── buffer.py                  # Buffer social scheduling
    ├── wordpress.py               # WordPress REST API
    ├── storage.py                 # Supabase Storage
    ├── calendly.py                # Calendly scheduling
    ├── meta_ads.py                # Meta Ads (Facebook/Instagram)
    └── google_ads.py              # Google Ads
```

---

## Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx                          # Landing page
│   ├── auth/login/page.tsx               # Email + Google sign-in
│   ├── auth/callback/route.ts            # OAuth code exchange
│   ├── site/[subdomain]/route.ts         # Published website serving
│   └── dashboard/
│       ├── layout.tsx                    # Auth guard + AppSidebar
│       ├── page.tsx                      # Business card grid + stats
│       ├── agents/page.tsx               # Department management
│       ├── analytics/page.tsx            # (Post-V1)
│       ├── tasks/page.tsx                # Global Task Board (all businesses)
│       ├── settings/
│       │   ├── page.tsx                  # Settings hub
│       │   ├── profile/page.tsx          # Name, language, timezone
│       │   ├── billing/page.tsx          # Subscription, balance, top-up
│       │   ├── notifications/page.tsx    # Per-business notification toggles
│       │   └── connected-accounts/page.tsx  # OAuth connections
│       └── business/[businessId]/
│           ├── page.tsx                  # Activity, leads, contracts, invoices, usage
│           ├── tasks/page.tsx            # Per-business Task Board (Kanban)
│           ├── budget/page.tsx           # Dollar balance + spend history
│           ├── website/page.tsx          # Website builder (chat + preview)
│           └── coach/page.tsx            # Coach scheduling (Calendly embed)
│
├── components/
│   ├── ui/                               # shadcn/ui primitives (do not modify)
│   ├── dashboard/
│   │   ├── AppSidebar.tsx                # Main nav (add language selector here)
│   │   └── BalanceWidget.tsx             # Balance display + Top Up button
│   ├── tasks/
│   │   ├── TaskBoard.tsx                 # Kanban board (4 columns)
│   │   ├── TaskCard.tsx                  # Individual task card
│   │   └── DepartmentFilter.tsx          # Department filter chips
│   ├── billing/
│   │   ├── SubscriptionCard.tsx          # Current plan display
│   │   └── TopUpModal.tsx                # Stripe top-up flow
│   ├── settings/
│   │   └── ConnectedAccountsPanel.tsx    # OAuth platform connections
│   ├── interview/InterviewChat.tsx       # Business interview chat (do not modify)
│   └── website/WebsiteBuilderChat.tsx    # Website builder chat (do not modify)
│
└── lib/
    ├── api.ts                            # CRM + activity + pipeline endpoints
    ├── hiring-api.ts                     # Onboarding/department endpoints
    ├── usage-api.ts                      # Legacy budget endpoints
    ├── website-api.ts                    # Website builder endpoints
    ├── tasks-api.ts                      # Task Board CRUD
    ├── balance-api.ts                    # Balance + spend ledger
    ├── billing-api.ts                    # Stripe checkout, portal, top-up
    └── supabase/                         # Supabase client (client.ts + server.ts)
```

---

## Database Schema

### Existing Tables (Migrations 001–005)

| Table | Purpose |
|---|---|
| `businesses` | Core business entity (profile, archetype, autonomy, comm config, budgets) |
| `departments` | Active departments per business |
| `agents` | Individual agent instances (manager + staff) |
| `agent_tools` | Tool configurations per business (platform key vs BYOK) |
| `tasks` | Task records (scaffold, activated in Migration 007) |
| `memory_chunks` | pgvector semantic memory (populated post-V1) |
| `activity_log` | All agent actions + approval queue |
| `notifications` | Notification records (activated post-V1) |
| `usage_events` | Token-level cost tracking |
| `leads` | CRM lead records |
| `contracts` | Service agreements |
| `invoices` | Billing documents |
| `websites` | Website builder files + chat history |

### New Tables (Migrations 006–009)

| Table | Migration | Purpose |
|---|---|---|
| `business_context_history` | 006 | Version history of the Living Business Document |
| `user_balances` | 008 | Per-user dollar balance + Stripe subscription info |
| `spend_ledger` | 008 | Full debit/credit audit trail (links to tasks + businesses) |
| `connected_accounts` | 009 | OAuth tokens for social/ad platform connections |

### Column Additions to Existing Tables

| Table | Columns Added | Migration |
|---|---|---|
| `businesses` | `business_context JSONB`, `business_context_updated_at`, `notify_blocked BOOL` | 006 |
| `tasks` | `department TEXT`, `cost_usd NUMERIC`, `label_color TEXT`, `created_by TEXT`, `approved_by UUID` | 007 |
| `tasks` | Status value `pending` renamed to `planned` | 007 |

---

## Department Agent Interface

Every department (existing and future) implements `BaseDepartmentAgent`:

```python
class BaseDepartmentAgent(ABC):
    dept_type: str        # e.g. "marketing", "business_advisor"
    label_color: str      # hex color for Task Board cards
    model_primary: str    # claude-sonnet-4-6
    model_fast: str       # claude-haiku-4-5-20251001

    @abstractmethod
    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        ...

    # Shared helpers (provided by base class):
    async def get_business_context(business_id) -> BusinessContext
    async def create_task(business_id, title, description) -> task_id
    async def update_task(task_id, status, output, cost_usd)
    async def log_activity(business_id, summary, requires_approval, detail)
    async def check_balance(user_id) -> bool
    async def deduct_spend(user_id, business_id, task_id, amount_usd)
    async def request_approval(business_id, task_id, detail)
```

`DeptResult`:
```python
@dataclass
class DeptResult:
    status: str      # 'completed' | 'awaiting_approval' | 'failed'
    task_id: str
    summary: str
    output: dict
    cost_usd: float
```

**Adding a new department:** Create `agents/departments/{name}.py`, subclass `BaseDepartmentAgent`, implement `run()`, register in `DepartmentRunner` dispatch table and `department_suggester.ARCHETYPE_DEPARTMENTS`.

---

## Living Business Document

Stored as `businesses.business_context` JSONB. Structure:

```json
{
  "summary": "Plain-language description of the business",
  "products_services": [],
  "target_customers": [],
  "brand_voice": "...",
  "current_goals": [],
  "competitive_context": "...",
  "financials": {},
  "active_campaigns": [],
  "key_decisions": [],
  "last_updated": "ISO timestamp"
}
```

- **Populated:** On interview completion (`services/living_doc.initialize_from_profile`)
- **Updated by agents:** Any department can call `update_context()` after a significant event
- **Updated by user:** "Correct this" chat input → `propose_correction()` → Haiku interprets → `update_context()`
- **Versioned:** Every update snapshots old context to `business_context_history`
- **Shared context:** Every `BaseDepartmentAgent.get_business_context()` reads from this column

---

## Dollar Balance System

```
user_balances          ← one row per user (Stripe subscription + balance)
spend_ledger           ← every debit/credit (links to business + task)
usage_events           ← existing token-level detail (unchanged)
```

Flow:
1. User subscribes → Stripe webhook → `balance.grant(user_id, monthly_amount, 'subscription_grant')`
2. Agent runs → `cost_tracker.log_llm_usage()` → also calls `balance.deduct(user_id, business_id, task_id, cost)`
3. Balance hits zero → pipelines fail gracefully with "Insufficient balance" task status
4. User tops up → Stripe one-time checkout → webhook → `balance.grant(user_id, amount, 'top_up')`

Cost shown retroactively on completed Task Board cards (`tasks.cost_usd`).

---

## Task Board

Four Kanban columns mapped to `tasks.status`:

| Column | Status Value | Behavior |
|---|---|---|
| Planned | `planned` | Queued, not started |
| In Progress | `in_progress` | Agent actively working |
| Blocked by User | `awaiting_approval` | Highlighted; requires user action |
| Completed | `completed` | Done; shows cost |

Features:
- Department filter chips (per-department color coded via `tasks.label_color`)
- "Add Task" modal → `POST /api/tasks/{business_id}` with `created_by='user'`
- Approve button on Blocked cards → `POST /api/tasks/{id}/approve` → agent resumes
- Per-business notification toggle: `businesses.notify_blocked` (default true)

---

## Subscription Tiers

| Tier | Price | Monthly AI Spend | Coaching |
|---|---|---|---|
| Trial | Free | $5 (one-time) | — |
| Starter | $99/mo | $30/mo | 1 async/mo |
| Growth | $249/mo | $100/mo | 1 video/mo |
| Scale | $599/mo | $300/mo | 2 video/mo |
| Enterprise | Custom | Custom | Custom |

No business count limits on any tier. Top-ups available at any time ($10 minimum).

---

## Extension Points

| Future Feature | Where it plugs in |
|---|---|
| Voice (Vapi.ai) | New `tools/vapi.py` + `departments/sales_voice.py` |
| SMS (Twilio) | New `tools/twilio.py`; `comm_channel='sms'` already in schema |
| Video generation (Runway) | New `tools/runway.py`; imported by marketing + advertising agents |
| Persona Marketplace | New `personas` table + `routers/marketplace.py` + dynamic `BaseDepartmentAgent` loader |
| Talent Network | New `talent_listings` table + `routers/talent.py` |
| pgvector agent memory | `memory_chunks` table already exists; add `remember()`/`recall()` helpers to base |
| Additional UI languages | Drop `/messages/{locale}.json`; zero code changes |
| Additional archetypes | Add entry to `ARCHETYPE_DEPARTMENTS` in `department_suggester.py` |
| TikTok Ads | New `tools/tiktok_ads.py`; imported by `advertising.py` |
| QuickBooks/Xero | New `tools/quickbooks.py`; imported by `financial_advisor.py` |
| Teams / multi-user | Add `business_members` table; update RLS |

---

## Build Phase Summary

| Phase | What Ships | Duration |
|---|---|---|
| 0 | Cleanup: fix dead nav stubs | ½ day |
| 1 | Living Business Document | 3–4 days |
| 2 | Task Board (backend + Kanban UI) | 3–4 days |
| 3 | Department agent architecture (wrappers) | 4–5 days |
| 4 | Dollar balance system | 4–5 days |
| 5 | Stripe billing | 4–6 days |
| 6 | i18n + navbar language selector | 2–3 days |
| 7a | Business Advisor department | 3–4 days |
| 7b | Financial Advisor department | 3–4 days |
| 7c | Sales department | 4–5 days |
| 7d | Customer Service department | 4–5 days |
| 7e | Advertising department | 5–7 days |
| 8 | Settings + Connected Accounts | 4–5 days |
| 9 | Coach Scheduling | 3–4 days |
| 10 | Beta hardening + JWT auth | 1–2 weeks |

Each phase leaves the app fully functional. Nothing from a prior phase breaks when starting the next.
