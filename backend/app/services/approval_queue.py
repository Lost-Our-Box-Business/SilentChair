"""ApprovalQueue — dedicated approval flow for agent-generated actions.

Decoupled from activity_log (which is the history feed).
The approval_queue holds actionable items with explicit pending/approved/rejected state.
"""
from datetime import datetime, timezone

from app.db.client import get_supabase


def list_pending(business_id: str, dept_type: str | None = None) -> list[dict]:
    """Return pending approval items for a business, optionally filtered by dept."""
    db = get_supabase()
    q = (
        db.table("approval_queue")
        .select("*")
        .eq("business_id", business_id)
        .eq("status", "pending")
        .order("created_at", desc=False)
    )
    if dept_type:
        q = q.eq("dept_type", dept_type)
    return q.execute().data or []


def approve(queue_id: str, user_id: str) -> dict:
    """
    Approve a pending item. Triggers the pipeline resume logic so the action
    (e.g. send emails, publish articles) is actually executed.
    Returns the resolved queue row.
    """
    db = get_supabase()
    row = db.table("approval_queue").select("*").eq("id", queue_id).single().execute().data
    if not row:
        raise ValueError(f"Approval queue item not found: {queue_id}")
    if row["status"] != "pending":
        raise ValueError(f"Item {queue_id} is already {row['status']}")

    # Resolve the item
    db.table("approval_queue").update({
        "status": "approved",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "resolved_by": user_id,
    }).eq("id", queue_id).execute()

    # Execute the approved action by reusing existing resume logic
    _execute_approved_action(row)

    return {**row, "status": "approved"}


def reject(queue_id: str, user_id: str, reason: str = "") -> dict:
    """Reject a pending item and mark the associated task as failed."""
    db = get_supabase()
    row = db.table("approval_queue").select("*").eq("id", queue_id).single().execute().data
    if not row:
        raise ValueError(f"Approval queue item not found: {queue_id}")

    db.table("approval_queue").update({
        "status": "rejected",
        "reject_reason": reason,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "resolved_by": user_id,
    }).eq("id", queue_id).execute()

    # Find and fail associated task
    payload = row.get("payload") or {}
    _fail_associated_tasks(row["business_id"], row["dept_type"], reason)

    return {**row, "status": "rejected"}


def _execute_approved_action(row: dict) -> None:
    """Delegate to activity.do_pipeline_resume using the queue item's payload."""
    from app.services.activity import do_pipeline_resume, load_business_context, log_pipeline_run, notify

    business_id = row["business_id"]
    payload = row.get("payload") or {}
    action_type = row.get("action_type", "")

    # Build a synthetic activity row that do_pipeline_resume understands
    synthetic_row = {
        "business_id": business_id,
        "detail": {
            "edited_articles": payload.get("edited_articles", []),
            "outreach_emails": payload.get("outreach_emails", []),
            "qualified_leads": payload.get("qualified_leads", []),
            "market_research": payload.get("market_research", {}),
        },
    }
    try:
        do_pipeline_resume(row["id"], synthetic_row)
    except Exception as e:
        notify(business_id, f"Approval execution failed for {action_type}: {e}")


def _fail_associated_tasks(business_id: str, dept_type: str, reason: str) -> None:
    """Mark any awaiting_approval tasks for this dept as failed."""
    db = get_supabase()
    db.table("tasks").update({
        "status": "failed",
        "output": f"Rejected: {reason}",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("business_id", business_id).eq("department", dept_type).eq("status", "awaiting_approval").execute()
