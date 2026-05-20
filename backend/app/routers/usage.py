from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.client import get_supabase
from app.services.cost_tracker import get_budget_state

router = APIRouter(prefix="/usage", tags=["usage"])


class BudgetUpdate(BaseModel):
    daily_budget: Optional[float] = None
    dept_budgets: Optional[dict[str, Optional[float]]] = None


@router.get("/{business_id}")
async def get_usage(business_id: str):
    try:
        return get_budget_state(business_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{business_id}/history")
async def get_history(business_id: str, days: int = 30):
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = (
        get_supabase()
        .table("usage_events")
        .select("dept_type,cost_usd,created_at")
        .eq("business_id", business_id)
        .gte("created_at", f"{start}T00:00:00Z")
        .order("created_at")
        .execute()
        .data
    )
    by_date: dict[str, dict] = {}
    for row in rows:
        day = row["created_at"][:10]
        dept = row.get("dept_type") or "other"
        cost = float(row["cost_usd"])
        if day not in by_date:
            by_date[day] = {"date": day, "total": 0.0, "by_dept": {}}
        by_date[day]["total"] = round(by_date[day]["total"] + cost, 6)
        by_date[day]["by_dept"][dept] = round(
            by_date[day]["by_dept"].get(dept, 0.0) + cost, 8
        )
    return sorted(by_date.values(), key=lambda x: x["date"])


@router.patch("/{business_id}/budget")
async def update_budget(business_id: str, req: BudgetUpdate):
    update: dict = {}
    fields = req.model_fields_set
    if "daily_budget" in fields:
        update["daily_budget"] = req.daily_budget   # None clears the limit
    if "dept_budgets" in fields:
        update["dept_budgets"] = req.dept_budgets or {}
    if not update:
        return {"updated": False}
    get_supabase().table("businesses").update(update).eq("id", business_id).execute()
    return {"updated": True}
