"""Activity feed, pipeline trigger, and approval endpoints."""
from fastapi import APIRouter, HTTPException

from app.db.client import get_supabase
from app.services.activity import get_activity_feed, approve_action, log_pipeline_run, notify

router = APIRouter(tags=["activity"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_business_context(business_id: str) -> dict:
    db = get_supabase()

    biz_result = db.table("businesses").select("*").eq("id", business_id).execute()
    if not biz_result.data:
        raise HTTPException(status_code=404, detail="Business not found")
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


def _run_pipeline_for_archetype(business_id: str, ctx: dict) -> dict:
    archetype = ctx["archetype"]

    if archetype == "lead_generation":
        from app.agents.lead_gen_pipeline import run_lead_gen_pipeline
        return run_lead_gen_pipeline(
            business_id=business_id,
            business_profile=ctx["business_profile"],
            tool_keys=ctx["tool_keys"],
            autonomy=ctx["autonomy"],
            active_dept_types=ctx["active_dept_types"],
        )
    elif archetype == "client_acquisition":
        from app.agents.client_acquisition_pipeline import run_client_acquisition_pipeline
        return run_client_acquisition_pipeline(
            business_id=business_id,
            business_profile=ctx["business_profile"],
            tool_keys=ctx["tool_keys"],
            autonomy=ctx["autonomy"],
            active_dept_types=ctx["active_dept_types"],
        )
    else:
        from app.agents.content_pipeline import run_content_pipeline
        return run_content_pipeline(
            business_id=business_id,
            business_profile=ctx["business_profile"],
            tool_keys=ctx["tool_keys"],
            autonomy=ctx["autonomy"],
            active_dept_types=ctx["active_dept_types"],
        )


def _pipeline_summary(result: dict, archetype: str) -> dict:
    """Normalize pipeline result into a consistent response shape."""
    base = {
        "status": "awaiting_approval" if result.get("approval_required") else "complete",
        "approval_action": result.get("approval_action"),
        "log": result.get("log", []),
        "budget_state": result.get("budget_state", {}),
    }
    if archetype == "content_agency":
        base["published_urls"] = result.get("published_urls", [])
        base["social_posts"] = result.get("social_posts", [])
    elif archetype == "lead_generation":
        base["qualified_leads"] = result.get("qualified_leads", [])
        base["sent_results"] = result.get("sent_results", [])
    elif archetype == "client_acquisition":
        base["qualified_leads"] = result.get("qualified_leads", [])
        base["sent_results"] = result.get("sent_results", [])
        base["proposals"] = [{"company": p["company"], "title": p["title"]} for p in result.get("proposals", [])]
        base["contracts"] = [{"company": c["company"], "title": c["title"]} for c in result.get("contracts", [])]
        base["invoices"] = [{"company": i["company"], "title": i["title"], "amount": i.get("amount", 0)} for i in result.get("invoices", [])]
    return base


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/activity/{business_id}")
async def get_feed(business_id: str, limit: int = 50):
    return get_activity_feed(business_id, limit=limit)


@router.post("/activity/{activity_id}/approve")
async def approve(activity_id: str):
    db = get_supabase()
    row_result = db.table("activity_log").select("*").eq("id", activity_id).execute()
    if not row_result.data:
        raise HTTPException(status_code=404, detail="Activity not found")

    row = row_result.data[0]
    if not row.get("requires_approval"):
        raise HTTPException(status_code=400, detail="This action does not require approval")
    if row.get("approved_at"):
        raise HTTPException(status_code=400, detail="Already approved")

    updated = approve_action(activity_id)
    business_id = row["business_id"]

    # For content_agency: resume publish from held edited_articles
    detail = row.get("detail", {})
    edited_articles = detail.get("edited_articles", [])
    if edited_articles:
        ctx = _load_business_context(business_id)
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

    # For lead_gen / client_acquisition: resume send_outreach from held emails
    outreach_emails = detail.get("outreach_emails", [])
    if outreach_emails:
        ctx = _load_business_context(business_id)
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

    return updated


@router.post("/pipeline/run/{business_id}")
async def run_pipeline(business_id: str):
    try:
        ctx = _load_business_context(business_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result = _run_pipeline_for_archetype(business_id, ctx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    log_pipeline_run(business_id, result)

    if result.get("approval_required"):
        notify(business_id, result.get("approval_action", "Action requires approval"), requires_approval=True)
    else:
        _notify_completion(business_id, ctx["archetype"], result)

    return _pipeline_summary(result, ctx["archetype"])


def _notify_completion(business_id: str, archetype: str, result: dict) -> None:
    if archetype == "content_agency":
        n = len(result.get("published_urls", []))
        notify(business_id, f"Pipeline complete. Published {n} article(s).")
    elif archetype == "lead_generation":
        n = len(result.get("sent_results", []))
        notify(business_id, f"Lead gen complete. Sent {n} outreach email(s).")
    elif archetype == "client_acquisition":
        sent = len(result.get("sent_results", []))
        contracts = len(result.get("contracts", []))
        notify(business_id, f"Acquisition pipeline complete. {sent} emails sent, {contracts} contract(s) drafted.")
