# SilentChair — Development Roadmap

> Last updated: 2026-06-19
> Starting point: Current deployed codebase (see Current State below)

---

## Current State (as of June 2026)

### What's Built and Working

| Feature | Status | Notes |
|---|---|---|
| Google + email auth | ✅ Live | OAuth redirect fixed, working in production |
| Business interview (onboarding chat) | ✅ Live | Multi-turn AI interview, saves to `businesses` table |
| Business profile storage | ✅ Live | Static after creation — needs to become Living Document |
| Department suggestion + hiring flow | ✅ Live | UI exists, wired to content agency archetype |
| Budget allocation by department | ✅ Live | |
| Content agency pipeline | ✅ Live | Research → write → publish (blog + social + email) |
| Activity feed + approval queue | ✅ Live | |
| Website builder | ✅ Live | Subdomain hosting at `{slug}.silentchair.app` |
| Celery worker (background tasks) | ✅ Live | Running on Railway, connected to Upstash Redis |
| Serper web search | ✅ Live | API key connected |
| Resend email | ✅ Live | API key connected |
| Dashboard with business detail page | ✅ Live | |
| Stub pages (agents, tasks, analytics, settings) | ✅ Live | Placeholders, not functional |

### What's Missing for V1

Everything below needs to be built or significantly reworked before V1 launch.

---

## Phase 1 — Platform Foundation (Weeks 1–4)

The core systems that everything else depends on. Build these first.

### 1.1 Living Business Document

Transform the static `businesses.profile` JSON into a dynamic, versioned, agent-readable document.

- Add `business_context` JSONB column (structured: summary, products, customers, goals, priorities, recent_updates)
- Create an update mechanism: any agent can propose an update; a coordinator agent decides whether to commit it
- Add version history table (`business_context_history`)
- Build the user-facing simplified summary view on the Business Dashboard
- Build the "correct this" flow: user tells AI something is wrong → agent updates the document → summary refreshes

### 1.2 Dollar Balance System

Per-user AI spend balance powering all agent actions.

- `spend_ledger` table (user_id, amount, type: subscription_grant/top_up/debit, action_ref, actual_cost, created_at)
- Monthly balance grant on subscription renewal (via Stripe webhook)
- Actual AI cost tracked per action; platform markup applied at debit time
- Balance checked before every agent action; action blocked if insufficient
- After each task completes, cost written to the task record and visible on the Task Board
- Dashboard widget: balance remaining this month, spend by department, per-task cost history

### 1.3 Task Board

Sprint-board UI for the user to see all their AI tasks across departments.

- `tasks` table already exists (scaffolded) — activate it: add `department`, `cost`, `label_color`, `created_by` (user or agent) columns
- Kanban board page at `/dashboard/business/{id}/tasks` with four columns: Planned, In Progress, Blocked by User, Completed
- Department filter (chips/tabs at top of board)
- Color-coded label per department; secondary label for task type (content, outreach, report, etc.)
- Task card shows: title, department, status, cost (once completed), age
- Task detail drawer: full output, timestamps, cost breakdown, approve/reject button (for Blocked by User items)
- User-created tasks: "Add Task" button → free-text form → user selects department; agent interprets and queues
- Notification toggle (per business): on/off for push/email when task lands in Blocked by User. Stored in `businesses` table as `notify_blocked`. Default: on.
- Wire up existing approval queue logic to the Blocked by User column

### 1.4 Stripe Billing

- Products and prices set up in Stripe dashboard (4 tiers + AI spend top-up products)
- Checkout flow: new user selects plan, enters payment, subscription created
- Stripe webhooks: `subscription.created`, `subscription.updated`, `subscription.deleted`, `payment_failed`
- Billing settings page: current plan, AI spend balance, per-task cost history, upgrade/downgrade, cancel, top up
- 14-day free trial with $5 AI spend included (no card required at signup)
- Failed payment grace period (3 days) → agent actions paused → account suspended

### 1.5 Language / i18n

- Install and configure `next-intl`
- Externalize all UI strings into locale files
- Language auto-detection on first load (from browser `Accept-Language` header)
- **Language selector button always visible in the navbar** (every page); also available in profile settings
- Changing language takes effect immediately across the whole platform
- Launch with: English, Spanish, French, Portuguese, German
- AI agent responses: pass the user's language preference in every system prompt

### 1.6 Agent Architecture Refactor

Move from a single content pipeline to a modular per-department agent system that all departments can use.

- `AgentBase` class: reads Living Business Document, checks credits, logs to activity_log, handles approval queue
- `DepartmentRunner`: dispatches the right agent based on department type and schedule
- `ApprovalQueue`: stores pending actions, exposes them to dashboard, handles approve/reject/edit
- Per-business, per-department schedules stored in DB (user-configurable)
- Celery Beat dispatcher updated to use new system

---

## Phase 2 — Core Departments (Weeks 5–10)

Build each department as a self-contained agent module on top of the Phase 1 architecture.

### 2.1 Marketing Department (Refactor from existing)

Current content pipeline becomes the Marketing agent proper:
- Full persona: name, voice, personality
- Social platforms: connect Instagram, Facebook, LinkedIn, X via OAuth
- Blog publishing: WordPress REST API and Ghost Admin API
- Image generation: Fal.ai (Flux) as primary, DALL-E 3 as fallback; AI selects based on task
- Email campaigns: Resend for sends; basic template builder in UI
- Performance tracking: pull engagement metrics from connected platforms; report to activity feed
- Reads Living Business Document for every content piece (brand, voice, current goals)

### 2.2 Business Advisor Department

- Real-time conversational interface (user can chat anytime)
- Periodic proactive briefings: weekly strategic summary pushed to activity feed
- Access to full Living Business Document + activity history
- Generates suggestions, flags risks, celebrates milestones
- Can trigger updates to the Living Business Document when strategy shifts

### 2.3 Financial Advisor Department

- Conversational interface for Q&A (budget questions, cash flow, projections)
- User inputs financial data manually (expenses, revenue, payroll) via a simple form or by pasting into chat
- Monthly financial summary report generated and posted to activity feed
- Budget alerts: notifies user when department spend approaches limit
- V1.1: QuickBooks/Xero integration for automatic data sync

### 2.4 Client Acquisition Department

- Target client profile builder: AI asks user to describe their ideal client
- Research module: Serper searches for prospect lists based on profile
- Outreach sequence generator: personalized email sequences per prospect
- Sends via Resend when in Full Auto mode
- Tracks replies and updates pipeline in DB
- Pipeline view in dashboard (prospect → contacted → replied → meeting booked)

### 2.5 Sales Department

- **Outbound:** Email outreach campaigns; follows up on leads from Client Acquisition
- **Inbound chat widget:** Embeddable JS snippet (`<script src="silentchair.app/widget.js">`) that places a chat bubble on the user's site; Sales agent handles conversations in real time using business context
- Pipeline view: all active leads, their status, next action

### 2.6 Customer Service Department

- Inbound chat widget (shared infrastructure with Sales; routes based on intent)
- Email monitoring: user forwards their support inbox to a SilentChair-provided address; agent reads and responds
- Trained on products, services, policies from Living Business Document
- Escalation flow: flags conversation to user when it can't resolve

### 2.7 Advertising Department

- **Account connection:** OAuth flow for Meta Ads, Google Ads (TikTok in V1.1)
- **Campaign creation:** AI proposes campaign structure (objective, audience, budget, creative)
- **Creative generation:** Ad copy + image generated; shown to user for review before launch
- **Launch flow:** User approves → API calls create the campaign in the ad platform
- **Monitoring:** Pulls performance metrics daily; flags underperformers; suggests optimizations
- **Autonomy:** After initial approval, can make optimization changes within defined rules (no creative changes without approval; budget shifts up to 20% without approval)

---

## Phase 3 — Human Coaching and Connected Accounts (Weeks 11–13)

### 3.1 Coach Scheduling

- Calendly API integration (or embed): show available coach slots inside the app
- Booking confirmation: email to user + calendar invite
- Pre-session briefing: AI generates a document for the coach 2 hours before the session (business summary, recent activity, suggested topics)
- Post-session capture: after session, prompt user (or coach) to note key decisions → these update the Living Business Document
- Coach-side interface: simple view for coaches to see their upcoming sessions and pre-session briefings

### 3.2 Connected Accounts

- Social platforms (Instagram, Facebook, LinkedIn, X): OAuth connect/disconnect in Settings
- Ad platforms (Meta, Google): OAuth connect/disconnect
- Blog platforms (WordPress, Ghost): API key or OAuth connect
- Email (Resend or user's ESP): SMTP credentials or API key
- All credentials encrypted at rest; never exposed in API responses

### 3.3 Bring-Your-Own Keys (BYOK)

- Users who prefer to use their own Anthropic, Serper, Resend, etc. keys can enter them in Settings
- Platform keys used by default; BYOK overrides per-service
- BYOK users still consume credits (for platform overhead) but at a reduced rate

---

## Phase 4 — Beta and Hardening (Weeks 14–16)

### 4.1 Private Beta

- Invite 10–20 users from Brandon's network (game dev community, trusted contacts)
- Goal: complete end-to-end journey for each user (onboarding → active departments → coach session → subscription)
- Collect: where do users get confused? What actions fail? What's missing?
- Weekly feedback sessions; rapid iteration

### 4.2 Dollar Balance Calibration

- Measure actual AI token spend per action type during beta
- Confirm platform markup at each tier keeps margins positive as model costs change
- Confirm platform can sustain free trial economics ($5 included spend per new trial user)

### 4.3 Scale Testing

- Simulate 100 concurrent business pipeline runs
- Confirm Celery queue handles load without backing up
- Identify and fix any DB bottlenecks (check query plans on large tables)
- Confirm Railway worker can be horizontally scaled if needed

### 4.4 Security Review

- Audit all API endpoints for auth enforcement
- Confirm RLS policies cover all tables
- Confirm no user can access another user's business data
- Confirm credit system cannot be circumvented
- Review for common vulnerabilities (OWASP Top 10)
- Rotate all default/placeholder secrets

### 4.5 Payment Testing

- Test all Stripe flows: subscribe, upgrade, downgrade, cancel, failed payment, credit purchase
- Confirm webhook handling is idempotent (safe to receive same event twice)
- Confirm free trial → paid conversion works correctly

---

## Phase 5 — Public Launch (Week 17+)

### Pre-Launch Checklist

- [ ] All V1 departments working and tested by real beta users
- [ ] Stripe billing live and verified
- [ ] Dollar balance system accurate; per-task cost visible to users retrospectively
- [ ] Coach scheduling working end-to-end
- [ ] Living Business Document updating correctly
- [ ] Language support: 5 languages live
- [ ] Website builder publishing to live subdomains
- [ ] All secrets rotated (no defaults remaining)
- [ ] Error monitoring live (Sentry)
- [ ] Basic analytics live (PostHog)
- [ ] Terms of Service and Privacy Policy published
- [ ] Support channel established (email or in-app)
- [ ] Coach team briefed and calendars open

### Launch Strategy

- Start with a waitlist to control intake and onboard users in batches
- Personal onboarding for the first 50 users (Brandon or a coach joins their first session live)
- Prioritize a small number of success stories over large user counts initially

---

## Phase 6 — V1.1 (Post-Launch)

First expansion after a stable public launch:

- Voice: inbound and outbound calls for Sales and Customer Service (Vapi.ai)
- SMS outreach (Twilio)
- Video generation for Marketing and Advertising (Runway or Kling)
- QuickBooks/Xero sync for Financial Advisor
- TikTok ad management
- Additional UI languages (based on user demand)
- Agent memory (pgvector semantic search over past activity)

---

## Ongoing / Always

- Weekly: review activity logs for errors, agent failures, user friction
- Monthly: dollar balance calibration check (are platform margins correct as AI model costs shift?)
- Monthly: coach capacity review (enough coaches for subscriber count?)
- Quarterly: living roadmap review against user feedback and business goals
