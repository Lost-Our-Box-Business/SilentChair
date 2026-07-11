"""
Website Builder Agent

Two modes:
  1. auto_build_website(website_id)  — full multi-page build triggered on website creation.
     Runs: plan → shared CSS → shared JS → one HTML per page → initial dynamic content.
     Each step is a separate LLM call with its own full token budget.

  2. run_website_turn(website_id, message, current_files)  — single-turn chat for refinements.
     Uses the same sentinel-block file protocol as before.

File protocol for chat mode:
    __WEBSITE_FILES__
    ---index.html---
    <!DOCTYPE html>...
    ---styles.css---
    body { ... }
    __END_FILES__
"""
import json
import re
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.config import settings
from app.db.client import get_supabase


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _llm(max_tokens: int = 16000) -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=max_tokens,
    )


def _call(system: str, user: str, max_tokens: int = 16000) -> str:
    response = _llm(max_tokens).invoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])
    return response.content


def _parse_json(raw: str) -> dict | list:
    """Strip markdown fences and parse JSON."""
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        clean = "\n".join(inner).strip()
    return json.loads(clean)


# ── Business profile loader ───────────────────────────────────────────────────

def _load_business(website_id: str) -> tuple[str, dict]:
    """Return (business_id, profile_dict) for the given website."""
    sb = get_supabase()
    row = sb.table("websites").select("business_id").eq("id", website_id).single().execute()
    business_id: str = row.data["business_id"]
    biz = sb.table("businesses").select("profile, name").eq("id", business_id).single().execute()
    profile: dict = biz.data.get("profile") or {}
    if not profile.get("name") and biz.data.get("name"):
        profile["name"] = biz.data["name"]
    return business_id, profile


def _profile_text(profile: dict) -> str:
    labels = {
        "name": "Business name",
        "niche": "Industry/niche",
        "target_audience": "Target audience",
        "goals": "Goals",
        "tone": "Tone of voice",
        "services": "Services/products",
        "location": "Location",
        "contact_email": "Contact email",
        "contact_phone": "Contact phone",
        "website_url": "Existing website",
    }
    lines = ["Business profile:"]
    for key, label in labels.items():
        v = profile.get(key)
        if v:
            lines.append(f"  {label}: {v}")
    for key, v in profile.items():
        if key not in labels and v:
            lines.append(f"  {key}: {v}")
    return "\n".join(lines)


# ── Step 1: Plan the site ─────────────────────────────────────────────────────

PLAN_SYSTEM = """You are a web strategy expert. Given a business profile, produce a JSON site plan.

Return ONLY valid JSON — no prose, no markdown fences. Schema:
{
  "site_name": "string",
  "tagline": "string",
  "brand_colors": {"primary": "#hex", "accent": "#hex", "bg": "#hex", "text": "#hex", "muted": "#hex"},
  "google_fonts": "Font+Name:wght@400;600;700|SecondFont:wght@700",
  "pages": [
    {
      "slug": "index",
      "title": "Home",
      "sections": ["hero", "services", "stats", "testimonials", "cta"]
    }
  ],
  "dynamic_types": ["testimonial", "team_member", "portfolio_item"],
  "nav_links": [{"label": "Home", "href": "index.html"}, ...]
}

Rules:
- Always include index (home) page.
- Include about, services, contact pages for most businesses. Adjust for the business type.
- "sections" describes what content blocks each page has — used to guide page generation.
- "dynamic_types" lists which section types to pre-populate with AI content.
- brand_colors must be specific hex values that fit the industry tone (not generic blue).
- google_fonts: use the Google Fonts URL param format.
"""


def plan_site(profile: dict) -> dict:
    text = _profile_text(profile)
    raw = _call(PLAN_SYSTEM, text, max_tokens=2000)
    return _parse_json(raw)


# ── Step 2: Generate shared CSS ───────────────────────────────────────────────

CSS_SYSTEM = """You are an expert CSS architect. Generate a complete, production-quality shared stylesheet for a multi-page website.

Output ONLY raw CSS — no HTML, no JavaScript, no markdown, no comments except where essential.

Requirements:
- CSS custom properties (--color-primary, --color-accent, --color-bg, --color-text, --color-muted, --radius, --shadow, --max-width: 1160px)
- Google Fonts: the plan specifies which fonts. Link is handled in HTML; use font-family here.
- Full CSS reset (box-sizing, margin/padding 0, img max-width)
- Typography scale: --fs-hero: clamp(48px,6vw,80px), --fs-h2: clamp(28px,4vw,44px), --fs-h3: 22px, --fs-body: 17px, --fs-sm: 14px
- Layout utilities: .container (max-width, centered, padding 0 20px), .section (padding 80px 0), .grid-2, .grid-3, .grid-4 (CSS Grid, gap 32px, collapse to 1 col on mobile)
- Nav: sticky top-0, white bg with box-shadow on .scrolled class, flex between, z-index 100. .nav-logo, .nav-links (flex gap), .nav-links a (no underline, hover color transition). Mobile: hamburger button (#hamburger), .nav-links.open (flex-direction column)
- Hero section: min-height 100vh, CSS gradient background (use plan colors), flex center, text white. .hero-headline (--fs-hero, font-weight 800, line-height 1.1), .hero-sub (--fs-h3, opacity 0.85, margin 24px 0), .hero-cta (inline button)
- Buttons: .btn (padding 14px 32px, border-radius --radius, font-weight 600, cursor pointer, transition 0.2s), .btn-primary (bg --color-primary, text white), .btn-outline (border 2px solid --color-primary, bg transparent)
- Cards: .card (bg white, border-radius --radius, box-shadow --shadow, padding 32px, transition transform 0.2s). .card:hover (transform translateY(-4px))
- Services grid: .services-grid extends .grid-3. Each card has .service-icon (font-size 40px, margin-bottom 16px), .service-title (--fs-h3, font-weight 700), .service-desc (color --color-muted)
- Stats row: .stats-grid extends .grid-4. .stat-number (--fs-h2, font-weight 800, color --color-primary), .stat-label (--fs-sm, color --color-muted)
- Testimonials: .testimonials-grid extends .grid-3. .testimonial-body (font-style italic, margin-bottom 20px), .testimonial-author (font-weight 600), .testimonial-role (color --color-muted, --fs-sm)
- Team: .team-grid extends .grid-4. .team-avatar (width 80px, height 80px, border-radius 50%, bg gradient, font-size 32px, display flex center — emoji avatar), .team-name (font-weight 700), .team-role (color --color-muted)
- Footer: dark bg (--color-text), text white/muted, padding 60px 0 30px. .footer-grid (grid-3), .footer-bottom (border-top, padding-top 20px, flex between, --fs-sm, color muted)
- Scroll reveal: [data-reveal]{opacity:0;transform:translateY(28px);transition:opacity .7s ease,transform .7s ease} [data-reveal].visible{opacity:1;transform:none}
- Dynamic section loading skeleton: .dynamic-section .skeleton (bg #e2e8f0, border-radius 4px, animation shimmer 1.5s infinite). @keyframes shimmer
- Form styles: .form-group (margin-bottom 20px), label (display block, font-weight 600, margin-bottom 6px), input/textarea (width 100%, padding 12px 16px, border 1.5px solid #e2e8f0, border-radius --radius, font-size --fs-body, focus outline --color-primary)
- Timeline: .timeline (position relative), .timeline::before (vertical line), .timeline-item (padding-left 40px, margin-bottom 40px, position relative), .timeline-dot (absolute left, circle, bg --color-primary)
- FAQ accordion: .faq-item, .faq-question (button, full width, flex between, font-weight 600, cursor pointer), .faq-answer (max-height 0 hidden, transition max-height 0.3s)
- Responsive: @media (max-width: 768px) — .grid-2/.grid-3/.grid-4 → 1 col; nav hamburger shows; hero min-height 80vh; section padding 60px 0
- @media (max-width: 480px) — .grid-2 → 1 col; font sizes scale down
"""


def generate_shared_css(plan: dict) -> str:
    prompt = (
        f"Brand colors: {json.dumps(plan['brand_colors'])}\n"
        f"Google Fonts family names: {plan['google_fonts'].split('|')[0].split(':')[0].replace('+', ' ')}"
        f" and {plan['google_fonts'].split('|')[1].split(':')[0].replace('+', ' ') if '|' in plan['google_fonts'] else ''}\n"
        f"Site name: {plan['site_name']}"
    )
    return _call(CSS_SYSTEM, prompt, max_tokens=6000)


# ── Step 3: Generate shared JS ────────────────────────────────────────────────

JS_SYSTEM = """You are an expert JavaScript developer. Generate a complete shared scripts.js file for a multi-page website.

Output ONLY raw JavaScript — no HTML, no CSS, no markdown.

The file receives two globals injected before this script runs:
  SC_WEBSITE_ID  — UUID of this website
  SC_API         — base URL of the SilentChair API (e.g. "https://api.silentchair.app")

Requirements — implement ALL of these:

1. Mobile nav toggle: #hamburger button click toggles .open on .nav-links. Close on outside click.

2. Sticky nav shadow: add .scrolled to <nav> when window.scrollY > 10.

3. Scroll reveal: IntersectionObserver on all [data-reveal] elements — add .visible when intersecting (threshold 0.12). Run on DOMContentLoaded.

4. Smooth scroll: all anchor links with href starting "#" use scrollIntoView({behavior:'smooth'}).

5. Stat counters: on [data-count] elements, animate from 0 to the data-count value over 1.5s (easeOutQuad) when they scroll into view. Format with commas if >= 1000.

6. Parallax hero: if .hero exists, on scroll set hero.style.backgroundPositionY = scrollY * 0.35 + 'px'.

7. FAQ accordion: .faq-question click toggles .faq-answer max-height between 0 and scrollHeight. Add aria-expanded.

8. Dynamic section rendering — implement these functions and call them automatically:
   async function loadDynamicSections() {
     for each [data-dynamic] element on the page:
       const type = el.dataset.dynamic
       fetch sections from SC_API + '/public/website/' + SC_WEBSITE_ID + '/sections?type=' + type
       render using the appropriate render function
       replace skeleton with rendered HTML
   }

   function renderTestimonials(sections) — returns HTML string of testimonial cards
   function renderTeam(sections) — returns HTML string of team member cards
   function renderPortfolio(sections) — returns HTML string of portfolio cards
   function renderBlogPosts(sections) — returns HTML string of blog post cards

   Each render function must produce rich, styled HTML using the shared CSS classes.
   If fetch fails or returns empty, hide the section gracefully (display:none).

9. Active nav link: mark the nav link matching the current page (location.pathname) with class .active.

10. Image lazy load: add loading="lazy" to all <img> tags on DOMContentLoaded.

Call loadDynamicSections() on DOMContentLoaded.
"""


def generate_shared_js(plan: dict, website_id: str, api_base_url: str) -> str:
    prompt = (
        f"SC_WEBSITE_ID = '{website_id}'\n"
        f"SC_API = '{api_base_url}'\n"
        f"Pages: {json.dumps([p['slug'] for p in plan['pages']])}\n"
        f"Dynamic types used: {json.dumps(plan.get('dynamic_types', []))}"
    )
    # Inject the constants at the top of the generated JS
    js_body = _call(JS_SYSTEM, prompt, max_tokens=4000)
    header = (
        f"const SC_WEBSITE_ID = '{website_id}';\n"
        f"const SC_API = '{api_base_url}';\n\n"
    )
    return header + js_body


# ── Step 4: Generate individual page HTML ─────────────────────────────────────

PAGE_SYSTEM_TEMPLATE = """You are a world-class web developer and designer. Generate a complete, production-quality HTML page for a real business website.

{business_context}

{site_context}

SHARED ASSETS (already generated — link to them, do NOT inline their content):
  <link rel="stylesheet" href="styles.css">
  <script src="scripts.js" defer></script>

  The shared JS already handles: nav hamburger, scroll reveal, parallax, stat counters, FAQ accordion, dynamic section loading. Do NOT re-implement these in page-specific JS.

THIS PAGE: {page_title} ({page_slug}.html)
Required sections: {sections}

━━━ REQUIRED STRUCTURE ━━━

Every page MUST have:
- <head> with: charset, viewport meta, title, meta description, Google Fonts link, stylesheet link
- <nav> with: .nav-logo (business name), .nav-links (links to all pages), #hamburger button (three spans)
- <main> with the page sections listed above
- <footer> with: business name, tagline, nav links, contact info from profile
- <script src="scripts.js" defer></script> just before </body>

━━━ SECTIONS GUIDE ━━━

hero: Full-viewport gradient background (from CSS custom properties, NO <img>). Large headline specific to this business. Subtitle. CTA button. Add data-reveal.

services: .services-grid of .card elements. Each card: emoji icon (relevant to the service), title, description. NO external images. Add data-reveal to each card.

stats: .stats-grid with 4 stat blocks. Use [data-count="NUMBER"] for counter animation. Real numbers relevant to the business (years in business, clients, projects, satisfaction %). Add data-reveal.

testimonials: <div data-dynamic="testimonial" class="dynamic-section"> with a loading skeleton inside. The shared JS fetches and renders real testimonials from the API. Add a section heading outside the dynamic div.

team: <div data-dynamic="team_member" class="dynamic-section"> with loading skeleton. Section heading outside.

portfolio: <div data-dynamic="portfolio_item" class="dynamic-section"> with loading skeleton. Section heading outside.

mission: Two-column layout. Left: bold mission statement in large text. Right: paragraph about the business story/values. Add data-reveal to both columns.

timeline: .timeline with 4-5 milestones relevant to the business (founding, growth, achievements). Use years from the business profile if available; invent plausible ones if not. Add data-reveal to each item.

values: .grid-3 of .card elements with value name + description. Use emoji icons. Add data-reveal.

process: Numbered steps (1, 2, 3, 4) describing how this business works with clients. Use CSS counters or explicit numbers in styled circles. Add data-reveal.

service_list: More detailed than the home services section — include pricing hints, deliverables, or time estimates where appropriate. Add data-reveal.

pricing_cta: A centered CTA section with a bold headline, brief copy, and a "Get Started" button linking to contact.html.

form: A contact form with fields: name, email, phone (optional), message. Styled with .form-group. Action="#" (no backend needed for V1). Add a submit button.

map_placeholder: A decorative map-like element using CSS (gradient background with an overlay) and the business location text. NO actual map embed.

faq: 5-6 FAQ items using .faq-item/.faq-question/.faq-answer. Real questions relevant to the business. The shared JS handles accordion behaviour.

intro: A full-width section with a large headline and 2-3 paragraphs introducing the business/services page. Add data-reveal.

cta: A full-width section with gradient background, bold headline, subtext, and button linking to contact.html. Add data-reveal.

━━━ QUALITY RULES ━━━
- Write REAL, specific copy using the business profile — business name, services, audience, tone. No Lorem ipsum. No "[Business Name]" placeholders.
- ALL nav links use correct relative hrefs: index.html, about.html, services.html, contact.html (only link pages that exist in this site).
- data-reveal on every major section/card for scroll animations.
- DO NOT include <style> blocks — all styling is in styles.css.
- Output the COMPLETE HTML file — never truncate, no "..." or "[continues]".
- After the HTML, write ONE sentence summarising what you built (for the chat history).
"""


def generate_page_html(page: dict, plan: dict, profile: dict) -> str:
    business_context = _profile_text(profile)
    nav_links_str = ", ".join(f"{p['title']} ({p['slug']}.html)" for p in plan["pages"])
    site_context = (
        f"Site name: {plan['site_name']}\n"
        f"Tagline: {plan.get('tagline', '')}\n"
        f"All pages: {nav_links_str}\n"
        f"Brand tone: derived from business profile above\n"
        f"Google Fonts: {plan['google_fonts']}"
    )
    system = PAGE_SYSTEM_TEMPLATE.format(
        business_context=business_context,
        site_context=site_context,
        page_title=page["title"],
        page_slug=page["slug"],
        sections=", ".join(page["sections"]),
    )
    raw = _call(system, f"Build the {page['title']} page now.", max_tokens=16000)
    # Strip any trailing summary sentence (after the last </html>)
    if "</html>" in raw:
        raw = raw[:raw.rfind("</html>") + 7]
    return raw


# ── Step 5: Generate initial dynamic content ──────────────────────────────────

CONTENT_SYSTEM = """You are a copywriter. Generate initial dynamic content for a website.

Return ONLY a JSON array — no prose, no markdown fences. Each item:
{
  "type": "testimonial" | "team_member" | "portfolio_item" | "blog_post",
  "title": "string",
  "subtitle": "string",
  "body": "string",
  "metadata": {}
}

For testimonial: title=client name, subtitle=role+company, body=quote. metadata={rating:5}
For team_member: title=name, subtitle=role, body=2-sentence bio. metadata={linkedin_url:""}
For portfolio_item: title=project name, subtitle=client industry, body=2-sentence description of results. metadata={tags:["tag1"], result_metric:"30% increase in sales"}
For blog_post: title=article title, subtitle=category, body=2-3 sentence excerpt. metadata={slug:"url-friendly-slug", estimated_read_min:3}

Generate quantities appropriate to the business type. Aim for: 3 testimonials, 4 team members, 3 portfolio items per requested type.
All content must be realistic and specific to the business described.
"""


def generate_initial_content(plan: dict, profile: dict, website_id: str) -> list[dict]:
    dynamic_types = plan.get("dynamic_types", [])
    if not dynamic_types:
        return []

    prompt = _profile_text(profile) + f"\n\nGenerate content for types: {', '.join(dynamic_types)}"
    raw = _call(CONTENT_SYSTEM, prompt, max_tokens=4000)
    try:
        sections = _parse_json(raw)
        if not isinstance(sections, list):
            return []
    except Exception:
        return []

    sb = get_supabase()
    rows = []
    for i, item in enumerate(sections):
        rows.append({
            "website_id": website_id,
            "type": item.get("type", ""),
            "title": item.get("title"),
            "subtitle": item.get("subtitle"),
            "body": item.get("body"),
            "image_url": item.get("image_url"),
            "metadata": item.get("metadata", {}),
            "display_order": i,
        })

    if rows:
        sb.table("website_sections").insert(rows).execute()

    return rows


# ── Orchestrator ──────────────────────────────────────────────────────────────

def auto_build_website(website_id: str) -> dict:
    """
    Full multi-page site generation. Called once on website creation.
    Returns {files, page_list, reply}.
    """
    sb = get_supabase()
    _, profile = _load_business(website_id)

    # 1. Plan
    plan = plan_site(profile)

    # 2. Shared CSS
    css = generate_shared_css(plan)

    # 3. Shared JS
    js = generate_shared_js(plan, website_id, settings.public_api_url)

    # 4. Pages
    files: list[dict] = [
        {"path": "styles.css", "content": css},
        {"path": "scripts.js", "content": js},
    ]
    for page in plan["pages"]:
        html = generate_page_html(page, plan, profile)
        filename = f"{page['slug']}.html"
        files.append({"path": filename, "content": html})

    # 5. Dynamic content
    generate_initial_content(plan, profile, website_id)

    # Build page list for frontend
    page_list = [{"slug": p["slug"], "title": p["title"]} for p in plan["pages"]]

    # Persist files and a summary chat entry
    site_name = plan.get("site_name", profile.get("name", "your site"))
    page_names = ", ".join(p["title"] for p in plan["pages"])
    reply = (
        f"I've built **{site_name}** — a {len(plan['pages'])}-page professional website "
        f"({page_names}). It features a gradient hero, services grid, stats, "
        f"animated scroll reveals, and sections that load live content (testimonials, team, portfolio) "
        f"from the SilentChair API. Use the chat to refine any page or section."
    )
    sb.table("websites").update({
        "files": files,
        "chat_history": [{"role": "assistant", "content": reply}],
        "updated_at": "now()",
    }).eq("id", website_id).execute()

    return {"files": files, "page_list": page_list, "reply": reply}


# ── Single-turn chat for refinements ─────────────────────────────────────────

REFINE_SYSTEM = """You are an expert web developer helping a client refine their multi-page website.

{business_context}

Current website files:
{files_context}

When making changes, use this exact format to output updated files:

__WEBSITE_FILES__
---filename.html---
[complete file content]
---styles.css---
[complete file content]
__END_FILES__

Rules:
- Only include files you're changing — unchanged files are preserved automatically.
- Output the COMPLETE content of each changed file — never truncate.
- styles.css and scripts.js are shared across all pages; changing them affects all pages.
- After the file block, write 1–2 sentences describing what you changed.
- If no file changes are needed, reply without the file block.
"""


class WebsiteState(TypedDict):
    messages: list[dict]
    current_files: list[dict]
    business_profile: dict
    reply: str
    updated_files: list[dict]


def _parse_files(text: str) -> list[dict]:
    if "__WEBSITE_FILES__" not in text:
        return []
    try:
        inner = text.split("__WEBSITE_FILES__", 1)[1].split("__END_FILES__", 1)[0]
    except IndexError:
        return []
    files = []
    parts = re.split(r"---([^-\n]+)---\n?", inner)
    it = iter(parts[1:])
    for filename, content in zip(it, it):
        filename = filename.strip()
        content = content.rstrip("\n")
        if filename:
            files.append({"path": filename, "content": content})
    return files


def _merge_files(current: list[dict], new: list[dict]) -> list[dict]:
    merged = {f["path"]: f["content"] for f in current}
    for f in new:
        merged[f["path"]] = f["content"]
    return [{"path": p, "content": c} for p, c in merged.items()]


def _files_context(files: list[dict]) -> str:
    if not files:
        return "No files exist yet."
    lines = [f"  - {f['path']} ({len(f['content'])} chars)" for f in files]
    return "\n".join(lines)


def builder_node(state: WebsiteState) -> WebsiteState:
    profile = state.get("business_profile") or {}
    files_ctx = _files_context(state["current_files"])
    system = REFINE_SYSTEM.format(
        business_context=_profile_text(profile),
        files_context=files_ctx,
    )

    lc_messages = [SystemMessage(content=system)]
    for msg in state["messages"]:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))

    response = _llm(16000).invoke(lc_messages)
    raw = response.content

    new_files = _parse_files(raw)
    reply = re.sub(r"__WEBSITE_FILES__.*?__END_FILES__", "", raw, flags=re.DOTALL).strip()
    if not reply:
        reply = "Done! The files have been updated."

    updated = _merge_files(state["current_files"], new_files)
    return {**state, "reply": reply, "updated_files": updated}


def _build_graph() -> StateGraph:
    g = StateGraph(WebsiteState)
    g.add_node("builder", builder_node)
    g.set_entry_point("builder")
    g.add_edge("builder", END)
    return g.compile()


_graph = _build_graph()


def run_website_turn(website_id: str, message: str, current_files: list[dict]) -> dict:
    """Single chat turn for refining the site after it's been built."""
    sb = get_supabase()
    row = sb.table("websites").select("chat_history, business_id").eq("id", website_id).single().execute()
    history: list[dict] = row.data.get("chat_history") or []
    business_id: str = row.data.get("business_id", "")

    business_profile: dict = {}
    if business_id:
        biz = sb.table("businesses").select("profile, name").eq("id", business_id).single().execute()
        if biz.data:
            business_profile = biz.data.get("profile") or {}
            if not business_profile.get("name") and biz.data.get("name"):
                business_profile["name"] = biz.data["name"]

    history.append({"role": "user", "content": message})

    result = _graph.invoke({
        "messages": history,
        "current_files": current_files,
        "business_profile": business_profile,
        "reply": "",
        "updated_files": [],
    })
    reply: str = result["reply"]
    updated_files: list[dict] = result["updated_files"]

    history.append({"role": "assistant", "content": reply})
    sb.table("websites").update({
        "chat_history": history,
        "files": updated_files,
        "updated_at": "now()",
    }).eq("id", website_id).execute()

    return {"reply": reply, "files": updated_files}
