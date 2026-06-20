# SilentChair — Production V1 Specification

> Last updated: 2026-06-19
> Status: Planning

---

## V1 Goal

Ship a complete, stable, monetized platform that delivers real business value to real paying users. V1 is not a demo — it is a product that a user can rely on to run their business daily, week after week.

V1 is scoped to be achievable without building everything in the vision. It establishes the core loop that makes SilentChair useful and differentiated from day one, then expands from there.

---

## What's In V1

### 1. Authentication and Onboarding
- Email/password and Google OAuth sign-in
- New user onboarding interview: multi-turn AI conversation that gathers business context
- Living Business Document created and saved at end of onboarding
- User lands on their Business Dashboard after completing onboarding
- **Language:** Platform auto-detects system language; user can change it in profile settings

### 2. The Living Business Document
- AI-maintained profile of the business, updated throughout the user's time on the platform
- Updated automatically when the user shares new information with any agent
- User-facing summary displayed on their Business Dashboard in plain language
- User can request corrections or additions by telling the AI ("actually, our pricing changed to X")
- Full document accessible to all agents as shared context
- Version history tracked internally (user does not need to see this in V1)

### 3. Business Dashboard
- Overview of the Living Business Document (simplified)
- Quick access to each department
- AI spend tracker: balance remaining this month, spend by department, cost per task (retrospective)

### 4. Task Board

A **sprint-board style view** showing all planned, in-progress, and completed tasks across the business. This is the primary place a user manages their AI workforce day to day.

**Columns:**
- **Planned** — tasks queued but not yet started
- **In Progress** — tasks the AI is actively working on
- **Blocked by User** — tasks paused because they need the user's attention, approval, or input. This is prominently surfaced so nothing gets missed.
- **Completed** — finished tasks with outcomes and cost shown

**Features:**
- **Department filter:** chips or tabs to show tasks from one or all departments at once
- **Color-coded labels:** each department has a distinct color; task type (content, outreach, report, etc.) has a secondary label
- **User-created tasks:** users can add tasks manually — for themselves or assigned to a specific agent/department. Free-text description; the assigned agent interprets and executes.
- **Task detail:** click any task card to see the full output, cost, timestamps, and any required action
- **Notification toggle:** per-business setting to turn on/off push notifications and/or email when a task lands in "Blocked by User." Default: on. Can be toggled from the task board header or from notification settings.

### 5. AI Workforce — V1 Departments

All departments are accessible to all users on all tiers. All users can run unlimited businesses. Tier differences are AI spend budget and coaching volume only.

#### Marketing Department
- **Capabilities:** Social media content (draft + schedule + publish), blog posts (research + write + publish), email campaigns (design + send), performance tracking
- **Platforms:** Instagram, Facebook, LinkedIn, X (Twitter), blog (user's WordPress or Ghost site)
- **Email:** Campaign sends via Resend or user's own ESP
- **Autonomy:** User selects Full Auto or Approval Required per content type
- **Schedule:** Runs on user-defined schedule (daily, weekly, or custom)

#### Business Advisor Department
- **Capabilities:** Strategic review of business performance, proactive suggestions, goal-setting support, market observations, answering "what should I do about X?" questions
- **Mode:** Conversational (user can chat with the advisor at any time) + periodic proactive briefings pushed to the activity feed
- **Context:** Deeply informed by the Living Business Document

#### Financial Advisor Department
- **Capabilities:** Budget planning, expense tracking (from user-provided data), cash flow modeling, spending alerts, monthly financial summary
- **Data sources:** User manually provides financial data to start; future integrations with accounting tools (Phase 2)
- **Mode:** Conversational + periodic reports

#### Client Acquisition Department
- **Capabilities:** Research target client profiles, draft outreach sequences (email), manage follow-up timing, track pipeline status
- **Tools:** Serper (web research), email via Resend
- **Autonomy:** Full Auto (sends on user's behalf) or Approval Required

#### Sales Department
- **Capabilities:** Inbound lead management (via website chat widget), outbound email outreach, pipeline tracking, follow-up sequences
- **Website chat:** Embeddable chat widget users add to their site; Sales agent handles conversations
- **Mode:** Handles inbound in real-time; outbound runs on schedule

#### Customer Service Department
- **Capabilities:** Handles inbound queries via website chat and email; answers product/service questions using business context; escalates to user when genuinely unresolvable
- **Mode:** Real-time chat via embeddable widget; email monitoring and response
- **Context:** Informed by Living Business Document (products, policies, tone)

#### Advertising Department
- **Capabilities:** Creates ad campaigns (copy + image creative) for Facebook, Instagram, Google, and TikTok; sets up targeting recommendations; presents for approval or launches directly; monitors spend and performance; pauses underperforming campaigns
- **Autonomy:** Always presents campaign plan before first launch; after approval, can operate within budget autonomously
- **Image generation:** Uses best-available model for the brief (Flux, DALL-E 3)
- **Note:** Direct ad platform API connections require the user to connect their accounts (OAuth)

### 6. Human Business Coach
- Coach scheduling via Calendly embed inside the platform
- User selects from available coach time slots
- Pre-session: AI generates a briefing document for the coach (business summary, recent activity, suggested topics)
- Post-session: user's stated decisions/directions captured and used to update the Living Business Document
- Sessions conducted via Zoom (or user's preferred video tool; link provided in booking confirmation)
- Coach notes accessible to the AI after the session

### 7. Website Builder
- Natural language chat interface to build and modify a website
- Site hosted on `{slug}.silentchair.app` subdomain
- Custom domain support: user provides their domain, platform provides CNAME instructions
- Preview via iframe in the dashboard
- Publish to live URL with one click
- AI has full access to Living Business Document when building the site (brand, products, tone)

### 8. Subscription and Billing
- Stripe integration for all payments
- Monthly subscription tiers (see VISION.md for pricing)
- Dollar balance per user: subscription tier includes monthly AI spend allowance; every agent action deducts its actual cost from the balance
- After each task completes, the user sees what it cost (retrospective transparency)
- Top-up purchases available at any time in dollar increments ($10 minimum)
- No business count limits — unlimited businesses on any tier; more businesses consume more AI spend balance
- Free trial: 14 days, $5 in AI spend included, no credit card required
- Upgrade/downgrade/cancel self-service from the billing settings page

### 9. Language Support
- Auto-detect user's system language on first load
- **Language selector button always visible in the navbar on every page** — one click changes the language for the entire platform immediately
- Language setting also available in user profile settings for discoverability
- All AI agent responses in the user's selected language
- All generated content (posts, emails, blog articles) in the user's language
- UI translated for all major languages (i18n via next-intl)
- V1 launch languages: English, Spanish, French, Portuguese, German (expand based on user demand)

### 10. Settings and Account Management
- Profile settings (name, language, timezone, notification preferences)
- Connected accounts (social platforms, ad accounts, WordPress, etc.)
- API key management (bring your own keys for Anthropic, Serper, Resend, etc.)
- Subscription and billing management
- Business management (add, remove, switch between businesses)
- Notification preferences (email, in-app)

---

## What's NOT in V1

These are explicitly deferred to post-V1. Do not build them in V1 even if it seems easy:

| Feature | Reason Deferred |
|---|---|
| Voice calls (inbound/outbound) | Significant integration complexity; will be V1.1 |
| Video generation | Cost and quality not yet consistent enough for autonomous use |
| TikTok / YouTube video content | Requires video; deferred with video gen |
| Stripe payouts / marketplace | No marketplace yet |
| Persona Marketplace | No creator ecosystem yet |
| Talent Network / recruitment | Core platform must come first |
| pgvector agent memory | Living Business Document covers this for V1 |
| PDF generation for documents | HTML export is sufficient for V1 |
| SMS outreach | Twilio integration deferred to V1.1 |
| Phone number provisioning | Deferred with voice |
| SOC 2 / GDPR compliance program | Architecture supports it; formal program is post-revenue |
| Additional business archetypes (beyond content agency) | All new departments are the expansion |
| HR / Legal / Product departments | Post-V1 departments |
| Multi-language UI beyond 5 core languages | Expand based on demand |
| Accounting software integrations (QuickBooks, Xero) | Financial Advisor works from user-provided data in V1 |

---

## V1.1 (First Post-Launch Release)

Items to ship immediately after V1 stabilizes:

- Voice: inbound and outbound calls for Sales and Customer Service (via Vapi.ai or Twilio + ElevenLabs)
- SMS outreach (Twilio)
- Video generation for Marketing and Advertising (Runway or Kling)
- QuickBooks/Xero integration for Financial Advisor
- Expanded UI language support

---

## User Flows

### New User
1. Sign up → language detected
2. Business interview (AI-led multi-turn chat, ~10–15 minutes)
3. Living Business Document created
4. Dashboard: prompted to hire their first agents
5. Agent hiring flow: select departments, configure autonomy level, set budget
6. Website builder prompt: "Would you like to build your business website?"
7. Coach scheduling prompt: "Book your first coaching session"
8. Dashboard now active — agents begin working on their next scheduled run

### Returning User (Daily)
1. Log in → dashboard shows overnight activity feed
2. Pending approvals (if any) listed at top
3. User approves, rejects, or edits pending actions
4. User can chat with any agent directly at any time
5. Budget tracker shows month-to-date spend

### Agent Run (Automated, Background)
1. Celery Beat triggers scheduled task for each active business
2. Task dispatcher identifies which departments are active and due to run
3. Each department agent reads Living Business Document for current context
4. Agent executes its task (research → create → publish/send or queue for approval)
5. Results written to activity_log
6. Living Business Document updated if significant business event occurred
7. If approval required: item added to pending approvals queue
8. If Full Auto: action taken immediately; user notified via activity feed

---

## Technical Requirements for V1

### New Integrations Needed

| Integration | Purpose | Service |
|---|---|---|
| Stripe | Billing, subscriptions, credit purchases | Stripe API |
| Calendly | Coach session scheduling | Calendly embed / API |
| Zoom | Video call links in booking confirmations | Zoom API or manual link |
| Facebook/Instagram | Ad management, social posting | Meta Marketing API |
| Google Ads | Ad campaign management | Google Ads API |
| TikTok Ads | Ad campaign management (V1.1) | TikTok for Business API |
| WordPress | Blog post publishing | WordPress REST API |
| Ghost | Blog post publishing (alternative) | Ghost Admin API |
| Buffer | Social post scheduling (already partial) | Buffer API |
| Fal.ai or Replicate | Image generation (Flux) | Fal.ai API |
| DALL-E 3 | Image generation (fallback) | OpenAI API |
| i18n library | UI translation | next-intl |

### Key Architecture Work

| Work Item | Description |
|---|---|
| Living Business Document system | Structured JSONB in Supabase; versioned; read by all agents |
| Dollar balance system | Per-user monthly AI spend balance; actual cost deducted per action; retrospective cost shown; top-up via Stripe |
| Agent scheduling system | Per-business, per-department schedules; Celery Beat dispatcher |
| Approval queue | Pending actions stored in DB; user approves/rejects from dashboard |
| Chat widget (embeddable) | JavaScript snippet users embed on their site; connects to Sales/CS agents |
| i18n system | All UI strings externalized; language detection on first load |
| Connected accounts system | OAuth flows for social/ad platforms; credential storage |
| Stripe webhook handling | Subscription events, credit purchases, failed payments |

---

## Definition of Done for V1

V1 is production-ready when:

- [ ] All V1 departments are functional and have been used by at least 10 real users in beta
- [ ] Stripe billing is live and tested (subscribe, pay, cancel, overage charge)
- [ ] Dollar balance correctly reflects all agent actions (deductions visible retroactively per task)
- [ ] Coach scheduling flow works end-to-end (book → briefing generated → session held → notes captured)
- [ ] Living Business Document updates correctly across at least 3 different trigger types
- [ ] Website builder produces usable sites and publishes to live subdomain
- [ ] At least 5 V1 launch languages are fully translated
- [ ] The platform handles 100 concurrent businesses running pipeline tasks without degradation
- [ ] No critical security vulnerabilities in a basic security review
- [ ] All V1 features have been used successfully in a complete end-to-end user journey test
