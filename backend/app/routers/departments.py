import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.departments import (
    DepartmentSuggestRequest, DepartmentSuggestResponse,
    ActivateDepartmentsRequest, ToolSetupRequest,
    HireStaffRequest, LaunchConfigRequest,
)
from app.agents.department_suggester import suggest_departments, ARCHETYPE_DEPARTMENTS
from app.db.client import get_supabase

router = APIRouter(prefix="/departments", tags=["departments"])


class ChatRequest(BaseModel):
    message: str


class ApprovalAction(BaseModel):
    user_id: str
    reason: str = ""


# ── Per-department endpoints (manager chat, narrative, approval queue) ─────────

@router.get("/{business_id}/{dept_type}")
def get_department(business_id: str, dept_type: str):
    """Return full department details including narrative, chat history, and today's cost."""
    try:
        from app.services.cost_tracker import get_today_spend
        from app.services.department_runner import AGENT_REGISTRY
        db = get_supabase()
        row = (
            db.table("departments")
            .select("*")
            .eq("business_id", business_id)
            .eq("dept_type", dept_type)
            .single()
            .execute()
            .data
        )
        if not row:
            raise HTTPException(status_code=404, detail="Department not found")
        spend = get_today_spend(business_id)
        by_dept = spend.get("by_dept", {})
        agent_cls = AGENT_REGISTRY.get(dept_type)
        row["today_cost_usd"] = by_dept.get(dept_type, 0.0)
        row["label_color"] = row.get("label_color") or (agent_cls.label_color if agent_cls else "#6b7280")
        return row
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/{dept_type}/chat")
def chat_with_manager(business_id: str, dept_type: str, body: ChatRequest):
    """Send a message to the department manager. Returns the manager's reply."""
    try:
        from app.services import department_manager
        reply = department_manager.chat(business_id, dept_type, body.message)
        return {"reply": reply}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{business_id}/{dept_type}/queue")
def get_dept_approval_queue(business_id: str, dept_type: str):
    """Return pending approval items for a specific department."""
    try:
        from app.services import approval_queue
        return approval_queue.list_pending(business_id, dept_type=dept_type)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/{dept_type}/queue/{queue_id}/approve")
def approve_dept_queue_item(business_id: str, dept_type: str, queue_id: str, body: ApprovalAction):
    """Approve a pending item in this department's approval queue."""
    try:
        from app.services import approval_queue
        return approval_queue.approve(queue_id, body.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/{dept_type}/queue/{queue_id}/reject")
def reject_dept_queue_item(business_id: str, dept_type: str, queue_id: str, body: ApprovalAction):
    """Reject a pending item in this department's approval queue."""
    try:
        from app.services import approval_queue
        return approval_queue.reject(queue_id, body.user_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _full_dept_catalog() -> dict:
    """Merge all archetype department catalogs into one dict keyed by dept_type."""
    catalog = {}
    for depts in ARCHETYPE_DEPARTMENTS.values():
        for d in depts:
            catalog[d.dept_type] = d
    return catalog


@router.post("/suggest", response_model=DepartmentSuggestResponse)
async def suggest(req: DepartmentSuggestRequest):
    try:
        archetype, departments = suggest_departments(req.business_profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db = get_supabase()

    # Persist detected archetype on the business
    db.table("businesses").update({"archetype": archetype}).eq("id", req.business_id).execute()

    rows = [
        {
            "business_id": req.business_id,
            "name": d.name,
            "dept_type": d.dept_type,
            "description": d.description,
            "is_required": d.is_required,
            "is_active": False,
        }
        for d in departments
    ]
    db.table("departments").upsert(rows, on_conflict="business_id,dept_type").execute()

    return DepartmentSuggestResponse(business_id=req.business_id, departments=departments)


@router.get("/business/{business_id}")
async def get_departments(business_id: str):
    db = get_supabase()
    result = db.table("departments").select("*").eq("business_id", business_id).execute()
    return result.data


@router.post("/activate")
async def activate_departments(req: ActivateDepartmentsRequest):
    db = get_supabase()
    db.table("departments").update({"is_active": False}).eq("business_id", req.business_id).execute()
    if req.dept_types:
        db.table("departments").update({"is_active": True}).eq("business_id", req.business_id).in_("dept_type", req.dept_types).execute()

    dept_catalog = _full_dept_catalog()
    result = db.table("departments").select("*").eq("business_id", req.business_id).eq("is_active", True).execute()
    active_depts = result.data

    for dept in active_depts:
        dept_type = dept["dept_type"]
        catalog_entry = dept_catalog.get(dept_type)
        if not catalog_entry:
            continue
        db.table("agents").upsert({
            "business_id": req.business_id,
            "department_id": dept["id"],
            "name": catalog_entry.manager_title,
            "role": "manager",
            "agent_type": f"{dept_type}_manager",
            "model": "claude-sonnet-4-6",
            "is_active": True,
        }, on_conflict="business_id,agent_type").execute()

        tool_rows = [
            {
                "business_id": req.business_id,
                "tool_name": tool.tool_name,
                "key_source": "platform",
                "is_active": False,
            }
            for tool in catalog_entry.tools
        ]
        db.table("agent_tools").upsert(tool_rows, on_conflict="business_id,tool_name").execute()

    return {"activated": len(active_depts)}


@router.post("/tools/setup")
async def setup_tools(req: ToolSetupRequest):
    db = get_supabase()
    for item in req.tools:
        update = {"key_source": item.key_source, "is_active": True}
        if item.key_source == "user" and item.user_key:
            update["encrypted_key"] = item.user_key
        db.table("agent_tools").update(update).eq("business_id", req.business_id).eq("tool_name", item.tool_name).execute()
    return {"configured": len(req.tools)}


@router.get("/tools/{business_id}")
async def get_tools(business_id: str):
    db = get_supabase()
    result = db.table("agent_tools").select("*").eq("business_id", business_id).execute()
    return result.data


@router.post("/staff/hire")
async def hire_staff(req: HireStaffRequest):
    db = get_supabase()
    dept_catalog = _full_dept_catalog()

    dept_result = db.table("departments").select("dept_type").eq("id", req.department_id).single().execute()
    if not dept_result.data:
        raise HTTPException(status_code=404, detail="Department not found")

    dept_type = dept_result.data["dept_type"]
    catalog_entry = dept_catalog.get(dept_type)
    if not catalog_entry:
        raise HTTPException(status_code=400, detail="Unknown department type")

    role_map = {s.role: s for s in catalog_entry.suggested_staff}
    hired = []
    for role_name in req.roles:
        staff = role_map.get(role_name)
        if not staff:
            continue
        db.table("agents").insert({
            "business_id": req.business_id,
            "department_id": req.department_id,
            "name": staff.role,
            "role": "staff",
            "agent_type": staff.agent_type,
            "model": "claude-haiku-4-5-20251001",
            "is_active": True,
        }).execute()
        hired.append(role_name)

    return {"hired": hired}


@router.post("/launch")
async def launch_business(req: LaunchConfigRequest):
    db = get_supabase()
    db.table("businesses").update({
        "autonomy": req.autonomy,
        "comm_channel": req.comm_channel,
        "comm_config": req.comm_config,
        "status": "active",
    }).eq("id", req.business_id).execute()
    return {"status": "active", "business_id": req.business_id}


@router.get("/staff-suggestions/{dept_type}")
async def get_staff_suggestions(dept_type: str):
    catalog = _full_dept_catalog()
    entry = catalog.get(dept_type)
    if not entry:
        raise HTTPException(status_code=404, detail="Department type not found")
    return [s.model_dump() for s in entry.suggested_staff]
