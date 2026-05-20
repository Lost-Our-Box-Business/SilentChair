from fastapi import APIRouter, HTTPException
from app.models.departments import (
    DepartmentSuggestRequest, DepartmentSuggestResponse,
    ActivateDepartmentsRequest, ToolSetupRequest,
    HireStaffRequest, LaunchConfigRequest,
)
from app.agents.department_suggester import suggest_departments, ARCHETYPE_DEPARTMENTS
from app.db.client import get_supabase

router = APIRouter(prefix="/departments", tags=["departments"])


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
