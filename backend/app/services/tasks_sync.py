"""Synchronise pipeline results into the tasks table."""
from app.db.client import get_supabase


_ARCHETYPE_MAP = {
    "content_agency":    ("Marketing",          "#3b82f6"),
    "lead_generation":   ("Lead Generation",    "#10b981"),
    "client_acquisition": ("Client Acquisition", "#f59e0b"),
}


def _pipeline_title(archetype: str, result: dict) -> str:
    """Build a human-readable task title from the pipeline result."""
    if result.get("approval_required"):
        action = result.get("approval_action", "").strip()
        return action if action else "Action pending approval"

    if archetype == "content_agency":
        n = len(result.get("published_urls", []))
        return f"Published {n} article{'s' if n != 1 else ''}"

    if archetype in ("lead_generation", "client_acquisition"):
        n = len(result.get("sent_results", []))
        if n:
            return f"Sent {n} outreach email{'s' if n != 1 else ''}"
        n_leads = len(result.get("qualified_leads", []))
        return f"Qualified {n_leads} lead{'s' if n_leads != 1 else ''}"

    return "Pipeline run complete"


def create_pipeline_task(
    business_id: str,
    archetype: str,
    result: dict,
    activity_log_id: str | None = None,
) -> str:
    """Create a task record from a completed pipeline run. Returns the new task id."""
    department, label_color = _ARCHETYPE_MAP.get(archetype, ("Operations", "#6b7280"))
    status = "awaiting_approval" if result.get("approval_required") else "completed"
    title = _pipeline_title(archetype, result)
    cost_usd = result.get("budget_state", {}).get("total_spend", 0) or 0

    db = get_supabase()
    row = db.table("tasks").insert({
        "business_id": business_id,
        "title": title,
        "status": status,
        "department": department,
        "label_color": label_color,
        "cost_usd": cost_usd,
        "created_by": "agent",
        "activity_log_id": activity_log_id,
    }).execute()

    return row.data[0]["id"] if row.data else ""


def complete_pipeline_task(activity_log_id: str) -> None:
    """Mark the task linked to this activity as completed. Non-critical — never raises."""
    try:
        db = get_supabase()
        db.table("tasks").update({"status": "completed"}).eq(
            "activity_log_id", activity_log_id
        ).eq("status", "awaiting_approval").execute()
    except Exception:
        pass
