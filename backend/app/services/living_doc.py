"""Living Business Document — initialize, update, version, and summarize.

Cost note: LLM calls here are not yet tracked in spend_ledger (Phase 4).
They are accounted for in usage_events indirectly via cost_tracker when
departments read business_context as part of their runs.
"""
import json
from datetime import datetime, timezone
from anthropic import Anthropic
from app.config import settings
from app.db.client import get_supabase


EMPTY_CONTEXT: dict = {
    "summary": "",
    "products_services": [],
    "target_customers": "",
    "brand_voice": "",
    "current_goals": [],
    "competitive_context": "",
    "financials": {},
    "active_campaigns": [],
    "key_decisions": [],
    "last_updated": None,
}


def _client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_context(business_id: str, context: dict) -> None:
    db = get_supabase()
    db.table("businesses").update({
        "business_context": context,
        "business_context_updated_at": _now_iso(),
    }).eq("id", business_id).execute()


def _snapshot(business_id: str, context: dict, change_summary: str, triggered_by: str) -> None:
    """Write the current context to history before overwriting it. Non-critical — never raises."""
    try:
        db = get_supabase()
        db.table("business_context_history").insert({
            "business_id": business_id,
            "context_snapshot": context,
            "change_summary": change_summary,
            "triggered_by": triggered_by,
        }).execute()
    except Exception:
        pass


def _haiku(prompt: str, max_tokens: int = 400) -> str:
    response = _client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON from an LLM response."""
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
    return json.loads(raw)


def _build_summary(profile: dict) -> str:
    """Write a 3-5 sentence plain-English summary from a flat interview profile."""
    name = profile.get("name", "This business")
    niche = profile.get("niche", "")
    audience = profile.get("target_audience", "")
    goals = profile.get("goals", [])
    channels = profile.get("publishing_channels", [])
    kpis = profile.get("kpis", [])
    notes = profile.get("additional_notes", "")

    prompt = (
        "Write a 3–5 sentence plain-English summary of this business for display on a dashboard. "
        "Be specific and factual. Use third person. No bullet points or headers.\n\n"
        f"Business name: {name}\n"
        f"Niche/industry: {niche}\n"
        f"Target audience: {audience}\n"
        f"Goals: {', '.join(goals) if goals else 'Not specified'}\n"
        f"Publishing channels: {', '.join(channels) if channels else 'Not specified'}\n"
        f"KPIs: {', '.join(kpis) if kpis else 'Not specified'}\n"
        f"Additional notes: {notes}\n\n"
        "Return ONLY the summary paragraph, nothing else."
    )

    try:
        return _haiku(prompt, 300)
    except Exception:
        goal_str = f": {goals[0]}" if goals else ""
        return f"{name} is a {niche} business targeting {audience}. Key goal{goal_str}."


def initialize_from_profile(business_id: str, profile: dict) -> dict:
    """Convert the interview profile JSON into a structured business_context.

    Called once on interview completion and lazily on first dashboard load
    for existing businesses that pre-date the Living Document system.
    """
    context = {
        **EMPTY_CONTEXT,
        "target_customers": profile.get("target_audience", ""),
        "brand_voice": profile.get("tone_of_voice", ""),
        "current_goals": profile.get("goals", []),
        "summary": _build_summary(profile),
        "last_updated": _now_iso(),
    }
    _write_context(business_id, context)
    _snapshot(business_id, context, "Initialized from interview", "interview")
    return context


def update_context(
    business_id: str,
    updates: dict,
    change_summary: str,
    triggered_by: str = "agent",
) -> dict:
    """Merge updates into business_context and snapshot the previous version to history."""
    current = get_context(business_id)
    _snapshot(business_id, current, change_summary, triggered_by)
    merged = {**current, **updates, "last_updated": _now_iso()}
    _write_context(business_id, merged)
    return merged


LANGUAGE_NAMES: dict = {
    "es": "Spanish", "fr": "French", "pt": "Portuguese",
    "de": "German", "zh": "Chinese",
}


def _translate_summary(summary: str, locale: str) -> str:
    lang = LANGUAGE_NAMES.get(locale)
    if not lang or not summary:
        return summary
    prompt = (
        f"Translate the following business description into {lang}. "
        "Return ONLY the translated text, no explanation.\n\n"
        f"{summary}"
    )
    try:
        return _haiku(prompt, 400)
    except Exception:
        return summary


def get_context(business_id: str, locale: str = "en") -> dict:
    """Return the full business_context JSONB.

    Lazily initializes from businesses.profile if business_context is empty —
    so existing businesses get populated on first dashboard load.
    When locale is not English, the summary is translated on the fly.
    """
    db = get_supabase()
    result = db.table("businesses").select(
        "business_context, profile"
    ).eq("id", business_id).single().execute()

    if not result.data:
        return dict(EMPTY_CONTEXT)

    ctx = result.data.get("business_context") or {}

    if not ctx.get("summary") and result.data.get("profile"):
        ctx = initialize_from_profile(business_id, result.data["profile"])

    ctx = ctx or dict(EMPTY_CONTEXT)

    if locale and locale != "en" and ctx.get("summary"):
        ctx = {**ctx, "summary": _translate_summary(ctx["summary"], locale)}

    return ctx


def propose_correction(business_id: str, user_message: str) -> dict:
    """Interpret a user correction via Haiku and apply it to business_context."""
    current = get_context(business_id)

    prompt = (
        "You are updating a business's Living Business Document.\n\n"
        f"Current context (JSON):\n{json.dumps(current, indent=2)}\n\n"
        f'The business owner says: "{user_message}"\n\n'
        "Return a JSON object containing ONLY the fields that need to change:\n"
        "- For 'summary': rewrite the complete paragraph incorporating the change.\n"
        "- For list fields (current_goals, products_services, etc.): return the complete updated list.\n"
        "- Omit any field that did not change.\n\n"
        "Available fields: summary, products_services, target_customers, brand_voice, "
        "current_goals, competitive_context, active_campaigns, key_decisions\n\n"
        "Return ONLY valid JSON — no markdown, no explanation."
    )

    raw = _haiku(prompt, 800)
    updates = _parse_json_response(raw)
    return update_context(
        business_id,
        updates,
        f"User correction: {user_message[:100]}",
        "user_correction",
    )
