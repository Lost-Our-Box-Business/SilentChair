"""
Content Agency Pipeline — LangGraph StateGraph that runs the full content creation workflow.

Flow: budget_coordinator → research → editorial_plan → write → edit → [autonomy gate] → publish → social → done
"""
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.tools import serper, wordpress, buffer


# ── State ────────────────────────────────────────────────────────────────────

class Article(TypedDict):
    title: str
    content: str
    meta_description: str
    slug: str


class SocialPost(TypedDict):
    platform: str
    text: str
    article_title: str


class PipelineState(TypedDict):
    business_id: str
    business_profile: dict
    tool_keys: dict
    autonomy: str
    active_dept_types: list[str]

    research_topics: list[str]
    content_plan: list[dict]
    drafted_articles: list[Article]
    edited_articles: list[Article]
    published_urls: list[str]
    social_posts: list[SocialPost]

    budget_state: dict

    approval_required: bool
    approval_action: str
    log: list[str]
    error: str | None


# ── LLM factory ──────────────────────────────────────────────────────────────

def _llm(model: str = "claude-sonnet-4-6", temperature: float = 0.7) -> ChatAnthropic:
    return ChatAnthropic(
        model=model,
        anthropic_api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=4096,
    )


def _cheap_llm() -> ChatAnthropic:
    return _llm("claude-haiku-4-5-20251001", temperature=0.5)


def _json_call(
    llm: ChatAnthropic, system: str, user: str,
    business_id: str = "", dept_type: str = "",
) -> dict | list:
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    if business_id:
        from app.services.cost_tracker import log_llm_usage
        log_llm_usage(response, business_id, dept_type, llm.model)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Budget coordinator node ───────────────────────────────────────────────────

def budget_coordinator_node(state: PipelineState) -> dict:
    """CEO agent: enforce budgets, prioritize departments, log the plan."""
    from app.services.cost_tracker import get_budget_state
    budget = get_budget_state(state["business_id"])
    log = list(state["log"])
    active = list(state["active_dept_types"])

    daily_remaining = budget["daily_remaining"]
    dept_remaining = budget["dept_remaining"]

    # Hard stop: overall daily budget exhausted
    if daily_remaining is not None and daily_remaining <= 0:
        log.append(
            f"CEO: daily budget ${budget['daily_budget']:.2f} exhausted "
            f"(spent ${budget['today_spend']:.4f} today) — skipping run"
        )
        return {"active_dept_types": [], "log": log, "budget_state": budget}

    # Pause departments that have exceeded their per-dept allocation
    if dept_remaining:
        paused = [d for d in active if d in dept_remaining and dept_remaining[d] <= 0.001]
        active = [d for d in active if d not in paused]
        for d in paused:
            log.append(f"CEO: pausing {d} — department allocation exhausted")

    # When under 30% of daily budget, let CEO agent reprioritize
    daily_budget = budget.get("daily_budget")
    if daily_budget and daily_remaining is not None and active and daily_remaining < float(daily_budget) * 0.3:
        try:
            result = _json_call(
                _cheap_llm(),
                """You are the CEO of an AI content agency with a tight remaining budget.
Decide which departments to run and in what order.
Return JSON: {"priority_order": ["dept1", ...], "skip": [], "reasoning": "one sentence"}""",
                f"""Daily budget: ${float(daily_budget):.2f}, remaining: ${daily_remaining:.4f}
Active departments: {', '.join(active)}
Per-dept remaining: {json.dumps({k: round(v, 4) for k, v in dept_remaining.items() if k in active})}
Prioritize highest content ROI.""",
            )
            if isinstance(result, dict):
                order = result.get("priority_order", active)
                skip = result.get("skip", [])
                active = [d for d in order if d in active and d not in skip]
                note = result.get("reasoning", "")
                log.append(f"CEO prioritization: {note}")
        except Exception:
            pass

    spend_msg = f"${budget['today_spend']:.4f} spent today"
    if daily_remaining is not None:
        spend_msg += f", ${daily_remaining:.4f} remaining of ${float(daily_budget):.2f}"
    log.append(f"CEO: budget check — {spend_msg}")

    return {"active_dept_types": active, "log": log, "budget_state": budget}


# ── Nodes ─────────────────────────────────────────────────────────────────────

def research_node(state: PipelineState) -> dict:
    profile = state["business_profile"]
    niche = profile.get("niche", "")
    audience = profile.get("target_audience", "")
    log = list(state["log"])
    bid = state["business_id"]

    serper_key = state["tool_keys"].get("serper") or settings.serper_api_key

    if serper_key:
        try:
            topics = serper.search_topics(niche, audience, api_key=serper_key)
            log.append(f"Research: found {len(topics)} trending topics via search")
        except Exception as e:
            log.append(f"Research: search failed ({e}), using AI suggestions instead")
            topics = _fallback_topics(niche, audience, bid)
    else:
        topics = _fallback_topics(niche, audience, bid)
        log.append("Research: generated topic suggestions via AI (no Serper key configured)")

    return {"research_topics": topics, "log": log}


def _fallback_topics(niche: str, audience: str, business_id: str = "") -> list[str]:
    llm = _cheap_llm()
    result = _json_call(
        llm,
        "Return a JSON array of 6 compelling content topic ideas as strings. No other text.",
        f"Generate 6 content topic ideas for a {niche} business targeting {audience}.",
        business_id=business_id,
        dept_type="editorial",
    )
    return result if isinstance(result, list) else []


def editorial_plan_node(state: PipelineState) -> dict:
    profile = state["business_profile"]
    topics = state["research_topics"]
    log = list(state["log"])
    bid = state["business_id"]

    llm = _cheap_llm()
    plan = _json_call(
        llm,
        """You are a Content Director. Given a list of topics, select the 3 best and return a JSON array.
Each item must have: title (str), angle (str — specific editorial angle), keywords (list of 3 strings).
Return ONLY the JSON array.""",
        f"""Business: {profile.get('name')} | Niche: {profile.get('niche')} | Audience: {profile.get('target_audience')}
Tone: {profile.get('tone_of_voice', 'professional')}
Topics to choose from: {json.dumps(topics)}""",
        business_id=bid,
        dept_type="editorial",
    )

    content_plan = plan if isinstance(plan, list) else []
    log.append(f"Editorial: planned {len(content_plan)} articles for this run")
    return {"content_plan": content_plan, "log": log}


def write_node(state: PipelineState) -> dict:
    profile = state["business_profile"]
    plan = state["content_plan"]
    log = list(state["log"])
    bid = state["business_id"]

    llm = _llm(temperature=0.75)
    drafted: list[Article] = []

    for item in plan:
        result = _json_call(
            llm,
            f"""You are an expert content writer for a {profile.get('niche')} brand.
Write a complete, high-quality article in a {profile.get('tone_of_voice', 'professional')} tone for {profile.get('target_audience')}.

Return JSON with:
- title (str)
- content (str — full HTML article, 600-900 words, use <h2> and <p> tags)
- meta_description (str — 155 chars max, compelling)
- slug (str — URL-friendly kebab-case)""",
            f"Title: {item.get('title')}\nAngle: {item.get('angle')}\nKeywords: {', '.join(item.get('keywords', []))}",
            business_id=bid,
            dept_type="editorial",
        )
        if isinstance(result, dict):
            drafted.append({
                "title": result.get("title", item.get("title", "")),
                "content": result.get("content", ""),
                "meta_description": result.get("meta_description", ""),
                "slug": result.get("slug", item.get("title", "").lower().replace(" ", "-")[:50]),
            })

    log.append(f"Writing: drafted {len(drafted)} articles")
    return {"drafted_articles": drafted, "log": log}


def edit_node(state: PipelineState) -> dict:
    drafted = state["drafted_articles"]
    profile = state["business_profile"]
    log = list(state["log"])
    bid = state["business_id"]

    llm = _llm(temperature=0.3)
    edited: list[Article] = []

    for article in drafted:
        result = _json_call(
            llm,
            f"""You are a Copy Editor for a {profile.get('niche')} brand.
Review and improve the article: fix grammar, improve flow, tighten copy, ensure the tone is {profile.get('tone_of_voice', 'professional')}.
Return the same JSON schema: title, content (HTML), meta_description, slug.""",
            f"Article to edit:\n{json.dumps(article)}",
            business_id=bid,
            dept_type="editorial",
        )
        if isinstance(result, dict):
            edited.append({
                "title": result.get("title", article["title"]),
                "content": result.get("content", article["content"]),
                "meta_description": result.get("meta_description", article["meta_description"]),
                "slug": result.get("slug", article["slug"]),
            })
        else:
            edited.append(article)

    log.append(f"Editing: polished {len(edited)} articles")
    return {"edited_articles": edited, "log": log}


def autonomy_gate_node(state: PipelineState) -> dict:
    autonomy = state["autonomy"]
    log = list(state["log"])
    if autonomy in ("major_decisions", "step_by_step"):
        n = len(state["edited_articles"])
        log.append(f"Gate: awaiting approval to publish {n} article(s)")
        return {"approval_required": True, "approval_action": f"Publish {n} edited article(s)", "log": log}
    log.append("Gate: full_auto mode — proceeding to publish")
    return {"approval_required": False, "log": log}


def publish_node(state: PipelineState) -> dict:
    articles = state["edited_articles"]
    tool_keys = state["tool_keys"]
    log = list(state["log"])
    published: list[str] = []

    wp_key = tool_keys.get("wordpress")

    for article in articles:
        if wp_key:
            try:
                cfg = wordpress.parse_wp_config(wp_key)
                result = wordpress.publish_post(
                    site_url=cfg["site_url"],
                    username=cfg["username"],
                    app_password=cfg["app_password"],
                    title=article["title"],
                    content=article["content"],
                )
                url = result.get("url", "")
                published.append(url)
                log.append(f"Published: '{article['title']}' → {url}")
            except Exception as e:
                log.append(f"Publish failed for '{article['title']}': {e}")
        else:
            fake_url = f"https://yourblog.com/{article['slug']}"
            published.append(fake_url)
            log.append(f"Simulated publish: '{article['title']}' (no WordPress configured)")

    return {"published_urls": published, "log": log}


def social_node(state: PipelineState) -> dict:
    articles = state["edited_articles"]
    published_urls = state["published_urls"]
    profile = state["business_profile"]
    tool_keys = state["tool_keys"]
    log = list(state["log"])
    bid = state["business_id"]

    if "social_media" not in state.get("active_dept_types", []):
        return {"social_posts": [], "log": log}

    llm = _cheap_llm()
    social_posts: list[SocialPost] = []
    buffer_key = tool_keys.get("buffer")

    for i, article in enumerate(articles):
        url = published_urls[i] if i < len(published_urls) else ""
        result = _json_call(
            llm,
            f"""You are a Social Media Manager for a {profile.get('niche')} brand (tone: {profile.get('tone_of_voice', 'engaging')}).
Write a LinkedIn post and a short X/Twitter post promoting this article.
Return JSON array with two objects, each: platform (str), text (str — include the URL naturally).""",
            f"Article: {article['title']}\nURL: {url}\nMeta: {article['meta_description']}",
            business_id=bid,
            dept_type="social_media",
        )
        if isinstance(result, list):
            for post in result:
                social_posts.append({
                    "platform": post.get("platform", ""),
                    "text": post.get("text", ""),
                    "article_title": article["title"],
                })

        if buffer_key and social_posts:
            try:
                buffer.schedule_to_all_profiles(buffer_key, social_posts[-1]["text"])
                log.append(f"Social: queued posts for '{article['title']}' via Buffer")
            except Exception as e:
                log.append(f"Social: Buffer scheduling failed ({e}) — posts drafted but not queued")

    if not buffer_key:
        log.append(f"Social: composed {len(social_posts)} posts (no Buffer key — not scheduled)")

    return {"social_posts": social_posts, "log": log}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_budget(state: PipelineState) -> str:
    return "research" if state.get("active_dept_types") else END


def route_after_gate(state: PipelineState) -> str:
    return END if state.get("approval_required") else "publish"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_content_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("budget_coordinator", budget_coordinator_node)
    graph.add_node("research", research_node)
    graph.add_node("editorial_plan", editorial_plan_node)
    graph.add_node("write", write_node)
    graph.add_node("edit", edit_node)
    graph.add_node("autonomy_gate", autonomy_gate_node)
    graph.add_node("publish", publish_node)
    graph.add_node("social", social_node)

    graph.set_entry_point("budget_coordinator")
    graph.add_conditional_edges("budget_coordinator", route_after_budget, {"research": "research", END: END})
    graph.add_edge("research", "editorial_plan")
    graph.add_edge("editorial_plan", "write")
    graph.add_edge("write", "edit")
    graph.add_edge("edit", "autonomy_gate")
    graph.add_conditional_edges("autonomy_gate", route_after_gate, {"publish": "publish", END: END})
    graph.add_edge("publish", "social")
    graph.add_edge("social", END)

    return graph.compile()


def run_content_pipeline(
    business_id: str,
    business_profile: dict,
    tool_keys: dict,
    autonomy: str,
    active_dept_types: list[str],
) -> PipelineState:
    graph = build_content_pipeline()
    initial: PipelineState = {
        "business_id": business_id,
        "business_profile": business_profile,
        "tool_keys": tool_keys,
        "autonomy": autonomy,
        "active_dept_types": active_dept_types,
        "research_topics": [],
        "content_plan": [],
        "drafted_articles": [],
        "edited_articles": [],
        "published_urls": [],
        "social_posts": [],
        "budget_state": {},
        "approval_required": False,
        "approval_action": "",
        "log": [],
        "error": None,
    }
    return graph.invoke(initial)
