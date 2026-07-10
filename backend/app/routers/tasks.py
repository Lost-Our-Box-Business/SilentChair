"""Task Board API — CRUD + approve + run for the tasks table."""
import traceback
from fastapi import APIRouter, HTTPException, Response
from app.db.client import get_supabase
from app.models.tasks import CreateTaskRequest, UpdateTaskStatusRequest, RejectTaskRequest, UpdateTaskRequest, UpdateApprovalContentRequest
from app.services.activity import approve_action, do_pipeline_resume
from app.services import tasks_sync, pipeline_runner

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/global/{user_id}")
def get_global_tasks(user_id: str, business_id: str | None = None):
    """All tasks across every business owned by this user."""
    db = get_supabase()
    # Collect business ids for this user
    biz_result = db.table("businesses").select("id").eq("user_id", user_id).execute()
    biz_ids = [r["id"] for r in biz_result.data]
    if not biz_ids:
        return []

    if business_id and business_id in biz_ids:
        biz_ids = [business_id]

    all_tasks = []
    for bid in biz_ids:
        result = (
            db.table("tasks")
            .select("*, businesses(name)")
            .eq("business_id", bid)
            .order("created_at", desc=True)
            .limit(200)
            .execute()
        )
        all_tasks.extend(result.data)

    all_tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return all_tasks


@router.get("/{business_id}")
def get_tasks(business_id: str, status: str | None = None, department: str | None = None):
    db = get_supabase()
    q = db.table("tasks").select("*").eq("business_id", business_id)
    if status:
        q = q.eq("status", status)
    if department:
        q = q.eq("department", department)
    result = q.order("created_at", desc=True).limit(200).execute()
    return result.data


@router.post("/{business_id}")
def create_task(business_id: str, req: CreateTaskRequest):
    db = get_supabase()
    result = db.table("tasks").insert({
        "business_id": business_id,
        "title": req.title,
        "description": req.description,
        "department": req.department,
        "status": "planned",
        "created_by": "user",
        "assigned_to": req.assigned_to,
        "label_color": "#6b7280",
    }).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create task")
    return result.data[0]


@router.patch("/{task_id}")
def update_task(task_id: str, req: UpdateTaskRequest):
    db = get_supabase()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = db.table("tasks").update(updates).eq("id", task_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Task not found")
    return result.data[0]


@router.patch("/{task_id}/status")
def update_task_status(task_id: str, req: UpdateTaskStatusRequest):
    db = get_supabase()
    result = db.table("tasks").update({"status": req.status}).eq("id", task_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Task not found")
    return result.data[0]


@router.post("/{task_id}/run")
def run_task(task_id: str, locale: str | None = None):
    """Trigger the pipeline immediately for a specific planned agent task."""
    db = get_supabase()
    task_result = db.table("tasks").select("*").eq("id", task_id).execute()
    if not task_result.data:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_result.data[0]
    if task.get("assigned_to") != "agent":
        raise HTTPException(status_code=400, detail="Task is not assigned to an agent")
    if task.get("status") != "planned":
        raise HTTPException(status_code=400, detail="Task is not in planned state")

    try:
        return pipeline_runner.execute(
            task["business_id"],
            task_ids=[task_id],
            create_summary_task=False,
            locale=locale,
        )
    except pipeline_runner.BudgetExhaustedError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")


@router.get("/{task_id}/approval-content")
def get_approval_content(task_id: str):
    """Return the pending approval payload for a task so the review UI can display it."""
    db = get_supabase()
    task_result = db.table("tasks").select("*").eq("id", task_id).execute()
    if not task_result.data:
        raise HTTPException(status_code=404, detail="Task not found")
    task = task_result.data[0]

    # New dept-agent path: queue_id stored in output_meta
    output_meta = task.get("output_meta") or {}
    queue_id = output_meta.get("queue_id")
    if queue_id:
        item = db.table("approval_queue").select("*").eq("id", queue_id).single().execute().data
        if item:
            return {"action_type": item.get("action_type"), "payload": item.get("payload") or {}}

    # Old pipeline path: activity_log
    log_id = task.get("activity_log_id")
    if log_id:
        log = db.table("activity_log").select("detail,action_type").eq("id", log_id).single().execute().data
        if log:
            return {"action_type": log.get("action_type"), "payload": log.get("detail") or {}}

    return {"action_type": task.get("title"), "payload": {}}


@router.patch("/{task_id}/approval-content")
def update_approval_content(task_id: str, req: UpdateApprovalContentRequest):
    """Replace the approval payload before approving (edit-and-approve flow)."""
    db = get_supabase()
    task_result = db.table("tasks").select("output_meta").eq("id", task_id).execute()
    if not task_result.data:
        raise HTTPException(status_code=404, detail="Task not found")

    output_meta = task_result.data[0].get("output_meta") or {}
    queue_id = output_meta.get("queue_id")
    if not queue_id:
        raise HTTPException(status_code=400, detail="Task has no editable approval queue item")

    from app.services import approval_queue as aq
    aq.update_payload(queue_id, req.payload)
    return {"updated": True}


@router.post("/{task_id}/approve")
def approve_task(task_id: str):
    """Approve a blocked task. Resumes the linked pipeline if one exists."""
    db = get_supabase()
    task_result = db.table("tasks").select("*").eq("id", task_id).execute()
    if not task_result.data:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_result.data[0]
    if task.get("status") != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Task is not awaiting approval")

    # New dept-agent path: execute via approval_queue
    output_meta = task.get("output_meta") or {}
    queue_id = output_meta.get("queue_id")
    if queue_id:
        from app.services import approval_queue as aq
        try:
            aq.approve(queue_id, user_id="system")
        except Exception:
            traceback.print_exc()
    else:
        # Old pipeline path: resume via activity_log
        activity_log_id = task.get("activity_log_id")
        if activity_log_id:
            row_result = db.table("activity_log").select("*").eq("id", activity_log_id).execute()
            if row_result.data:
                row = row_result.data[0]
                if not row.get("approved_at"):
                    try:
                        approve_action(activity_log_id)
                        do_pipeline_resume(activity_log_id, row)
                    except Exception:
                        traceback.print_exc()

    result = db.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()
    return result.data[0] if result.data else task


@router.post("/{task_id}/reject")
def reject_task(task_id: str, req: RejectTaskRequest):
    """Reject a blocked task. Returns it to planned with rejection notes so the agent can retry."""
    db = get_supabase()
    task_result = db.table("tasks").select("*").eq("id", task_id).execute()
    if not task_result.data:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_result.data[0]
    if task.get("status") != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Task is not awaiting approval")

    rejection_note = f"[Rejected: {req.reason}]" if req.reason else "[Rejected by user]"
    existing_desc = task.get("description") or ""
    new_desc = f"{rejection_note}\n\n{existing_desc}".strip() if existing_desc else rejection_note

    result = db.table("tasks").update({
        "status": "planned",
        "description": new_desc,
        "output": None,
    }).eq("id", task_id).execute()

    # Immediately re-run the agent with the rejection notes in the task description
    dept_type = task.get("department")
    business_id = task.get("business_id")
    if dept_type and business_id:
        import threading
        from app.services.department_runner import run_task as _run_task
        threading.Thread(
            target=_run_task,
            args=[business_id, dept_type, task_id],
            daemon=True,
        ).start()

    return result.data[0] if result.data else task


@router.delete("/{task_id}")
def delete_task(task_id: str):
    db = get_supabase()
    db.table("tasks").delete().eq("id", task_id).execute()
    return Response(status_code=204)
