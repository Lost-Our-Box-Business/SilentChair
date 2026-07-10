"""Activity logging, notification dispatch, and pipeline resume for agent actions."""
import uuid
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.db.client import get_supabase


# ── Core logging ──────────────────────────────────────────────────────────────

def log_action(
    business_id: str,
    agent_id: str | None,
    action_type: str,
    summary: str,
    requires_approval: bool = False,
    detail: dict | None = None,
) -> str:
    db = get_supabase()
    row_id = str(uuid.uuid4())
    db.table("activity_log").insert({
        "id": row_id,
        "business_id": business_id,
        "agent_id": agent_id,
        "action_type": action_type,
        "summary": summary,
        "requires_approval": requires_approval,
        "detail": detail or {},
    }).execute()
    return row_id


def _detail_for_log_entry(summary: str, result: dict) -> dict:
    """Attach relevant structured data to a pipeline log entry based on its content."""
    s = summary.lower()
    if "lead finding" in s or "find leads" in s or "extracted" in s:
        return {"leads": result.get("leads", [])}
    if "qualif" in s:
        return {
            "leads": result.get("leads", []),
            "qualified_leads": result.get("qualified_leads", []),
        }
    if "market research" in s:
        return {"market_research": result.get("market_research", {})}
    if "outreach drafting" in s or ("draft" in s and "outreach" in s):
        return {"outreach_emails": result.get("outreach_emails", [])}
    return {}


def log_pipeline_run(business_id: str, pipeline_result: dict) -> str | None:
    """Log all pipeline entries and return the activity_log_id of the approval entry (if any)."""
    for entry in pipeline_result.get("log", []):
        log_action(
            business_id=business_id,
            agent_id=None,
            action_type="pipeline_log",
            summary=entry,
            detail=_detail_for_log_entry(entry, pipeline_result),
        )

    if pipeline_result.get("approval_required"):
        detail: dict = {}
        if pipeline_result.get("edited_articles"):
            detail["edited_articles"] = pipeline_result["edited_articles"]
        if pipeline_result.get("outreach_emails"):
            detail["outreach_emails"] = pipeline_result["outreach_emails"]
        if pipeline_result.get("qualified_leads"):
            detail["qualified_leads"] = pipeline_result["qualified_leads"]
        if pipeline_result.get("market_research"):
            detail["market_research"] = pipeline_result["market_research"]

        return log_action(
            business_id=business_id,
            agent_id=None,
            action_type="approval_required",
            summary=pipeline_result.get("approval_action", "Approval needed"),
            requires_approval=True,
            detail=detail,
        )

    return None


def get_activity_feed(business_id: str, limit: int = 50) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("activity_log")
        .select("*")
        .eq("business_id", business_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def approve_action(activity_id: str) -> dict:
    db = get_supabase()
    result = (
        db.table("activity_log")
        .update({"approved_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", activity_id)
        .execute()
    )
    return result.data[0] if result.data else {}


# ── Business context loader (shared by router and tasks router) ───────────────

def load_business_context(business_id: str) -> dict:
    """Load full business execution context from DB. Raises ValueError if not found."""
    db = get_supabase()
    biz_result = db.table("businesses").select("*").eq("id", business_id).execute()
    if not biz_result.data:
        raise ValueError(f"Business not found: {business_id}")
    biz = biz_result.data[0]

    tools_result = (
        db.table("agent_tools")
        .select("tool_name,key_source,encrypted_key")
        .eq("business_id", business_id)
        .execute()
    )
    tool_keys: dict = {}
    for row in tools_result.data:
        if row["key_source"] == "user" and row.get("encrypted_key"):
            tool_keys[row["tool_name"]] = row["encrypted_key"]
        else:
            tool_keys[row["tool_name"]] = None

    dept_result = (
        db.table("departments")
        .select("dept_type")
        .eq("business_id", business_id)
        .eq("is_active", True)
        .execute()
    )
    active_dept_types = [r["dept_type"] for r in dept_result.data]

    return {
        "business_profile": biz.get("profile", {}),
        "autonomy": biz.get("autonomy", "major_decisions"),
        "archetype": biz.get("archetype", "content_agency"),
        "tool_keys": tool_keys,
        "active_dept_types": active_dept_types,
    }


# ── Pipeline resume (shared by activity router and tasks router) ──────────────

def do_pipeline_resume(activity_id: str, row: dict) -> None:
    """Resume the halted pipeline after an activity is approved."""
    business_id = row["business_id"]
    detail = row.get("detail", {})

    edited_articles = detail.get("edited_articles", [])
    outreach_emails = detail.get("outreach_emails", [])

    if not edited_articles and not outreach_emails:
        return

    ctx = load_business_context(business_id)

    if edited_articles:
        from app.agents.content_pipeline import PipelineState, build_content_pipeline
        graph = build_content_pipeline()
        partial_state: PipelineState = {
            "business_id": business_id,
            "business_profile": ctx["business_profile"],
            "tool_keys": ctx["tool_keys"],
            "autonomy": "full_auto",
            "active_dept_types": ctx["active_dept_types"],
            "research_topics": [],
            "content_plan": [],
            "drafted_articles": [],
            "edited_articles": edited_articles,
            "published_urls": [],
            "social_posts": [],
            "approval_required": False,
            "approval_action": "",
            "log": ["Resuming after manual approval"],
            "error": None,
        }
        result = graph.invoke(partial_state, {"starting_node": "publish"})
        log_pipeline_run(business_id, result)
        notify(business_id, f"Published {len(result.get('published_urls', []))} article(s) after approval.")

    elif outreach_emails:
        archetype = ctx["archetype"]
        if archetype == "lead_generation":
            from app.agents.lead_gen_pipeline import LeadGenState, build_lead_gen_pipeline
            graph = build_lead_gen_pipeline()
            partial: LeadGenState = {
                "business_id": business_id,
                "business_profile": ctx["business_profile"],
                "tool_keys": ctx["tool_keys"],
                "autonomy": "full_auto",
                "active_dept_types": ctx["active_dept_types"],
                "market_research": detail.get("market_research", {}),
                "leads": [],
                "qualified_leads": detail.get("qualified_leads", []),
                "outreach_emails": outreach_emails,
                "sent_results": [],
                "approval_required": False,
                "approval_action": "",
                "log": ["Resuming after approval"],
                "error": None,
            }
            result = graph.invoke(partial, {"starting_node": "send_outreach"})
        else:
            from app.agents.client_acquisition_pipeline import ClientAcquisitionState, build_client_acquisition_pipeline
            graph = build_client_acquisition_pipeline()
            partial: ClientAcquisitionState = {
                "business_id": business_id,
                "business_profile": ctx["business_profile"],
                "tool_keys": ctx["tool_keys"],
                "autonomy": "full_auto",
                "active_dept_types": ctx["active_dept_types"],
                "market_research": detail.get("market_research", {}),
                "leads": [],
                "qualified_leads": detail.get("qualified_leads", []),
                "outreach_emails": outreach_emails,
                "sent_results": [],
                "proposals": [],
                "contracts": [],
                "invoices": [],
                "approval_required": False,
                "approval_action": "",
                "log": ["Resuming after approval"],
                "error": None,
            }
            result = graph.invoke(partial, {"starting_node": "send_outreach"})

        log_pipeline_run(business_id, result)
        sent = len(result.get("sent_results", []))
        notify(business_id, f"Sent {sent} outreach email(s) after approval.")


# ── Notification dispatch ─────────────────────────────────────────────────────

def _send_webhook(url: str, payload: dict) -> None:
    try:
        httpx.post(url, json=payload, timeout=10)
    except Exception:
        pass


def _send_email(to: str, subject: str, body: str) -> None:
    if not settings.resend_api_key:
        return
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": "SilentChair <noreply@silentchair.ai>",
                "to": [to],
                "subject": subject,
                "html": f"<p>{body}</p>",
            },
            timeout=10,
        )
    except Exception:
        pass


def notify(business_id: str, summary: str, requires_approval: bool = False) -> None:
    db = get_supabase()
    result = db.table("businesses").select("comm_channel,comm_config").eq("id", business_id).execute()
    if not result.data:
        return
    biz = result.data[0]
    channel = biz.get("comm_channel", "email")
    config = biz.get("comm_config") or {}

    action_tag = " [ACTION REQUIRED]" if requires_approval else ""
    title = f"SilentChair Update{action_tag}"

    if channel == "email":
        email = config.get("email", "")
        if email:
            _send_email(email, title, summary)
    elif channel in ("slack", "discord"):
        webhook_url = config.get("webhook_url", "")
        if webhook_url:
            _send_webhook(webhook_url, {"text": f"*{title}*\n{summary}"})
