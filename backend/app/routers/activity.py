"""Activity feed, pipeline trigger, and approval endpoints."""
from fastapi import APIRouter, HTTPException

from app.db.client import get_supabase
from app.services.activity import (
    get_activity_feed, approve_action, load_business_context, do_pipeline_resume,
)
from app.services import tasks_sync, pipeline_runner

router = APIRouter(tags=["activity"])


@router.get("/activity/entry/{activity_id}")
async def get_entry(activity_id: str):
    """Return a single activity_log row including its detail payload."""
    db = get_supabase()
    result = db.table("activity_log").select("*").eq("id", activity_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Activity not found")
    return result.data[0]


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
    do_pipeline_resume(activity_id, row)
    tasks_sync.complete_pipeline_task(activity_id)
    return updated


@router.post("/pipeline/run/{business_id}")
async def run_pipeline(business_id: str):
    try:
        load_business_context(business_id)  # validate business exists
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        return pipeline_runner.execute(business_id)
    except pipeline_runner.BudgetExhaustedError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")
