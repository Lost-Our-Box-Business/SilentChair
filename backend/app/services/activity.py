"""Activity logging and notification dispatch for agent actions."""
import uuid
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.db.client import get_supabase


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


def log_pipeline_run(business_id: str, pipeline_result: dict) -> None:
    for entry in pipeline_result.get("log", []):
        log_action(
            business_id=business_id,
            agent_id=None,
            action_type="pipeline_log",
            summary=entry,
        )

    if pipeline_result.get("approval_required"):
        # Store everything needed to resume after approval
        detail: dict = {}
        # content_agency
        if pipeline_result.get("edited_articles"):
            detail["edited_articles"] = pipeline_result["edited_articles"]
        # lead_gen / client_acquisition
        if pipeline_result.get("outreach_emails"):
            detail["outreach_emails"] = pipeline_result["outreach_emails"]
        if pipeline_result.get("qualified_leads"):
            detail["qualified_leads"] = pipeline_result["qualified_leads"]
        if pipeline_result.get("market_research"):
            detail["market_research"] = pipeline_result["market_research"]

        log_action(
            business_id=business_id,
            agent_id=None,
            action_type="approval_required",
            summary=pipeline_result.get("approval_action", "Approval needed"),
            requires_approval=True,
            detail=detail,
        )


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
