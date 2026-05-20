"""Token cost tracking using Claude Opus 4.7 pricing."""
from datetime import date
from app.db.client import get_supabase

# Claude Opus 4.7 pricing per token
_PRICING = {
    "input":        5.00 / 1_000_000,
    "cache_write":  6.25 / 1_000_000,   # 5-min cache write price
    "cache_read":   0.50 / 1_000_000,
    "output":      25.00 / 1_000_000,
}


def calculate_cost(tokens: dict) -> float:
    return (
        tokens.get("input_tokens", 0)        * _PRICING["input"] +
        tokens.get("output_tokens", 0)       * _PRICING["output"] +
        tokens.get("cache_read_tokens", 0)   * _PRICING["cache_read"] +
        tokens.get("cache_write_tokens", 0)  * _PRICING["cache_write"]
    )


def log_llm_usage(response, business_id: str, dept_type: str, model: str = "claude-opus-4-7") -> float:
    """Extract token usage from a LangChain response, persist to usage_events, return cost in USD."""
    try:
        usage = getattr(response, "response_metadata", {}).get("usage", {})
        tokens = {
            "input_tokens":        usage.get("input_tokens", 0),
            "output_tokens":       usage.get("output_tokens", 0),
            "cache_read_tokens":   usage.get("cache_read_input_tokens", 0),
            "cache_write_tokens":  usage.get("cache_creation_input_tokens", 0),
        }
        cost = calculate_cost(tokens)
        get_supabase().table("usage_events").insert({
            "business_id": business_id,
            "dept_type":   dept_type or "unknown",
            "model":       model,
            "event_type":  "llm_call",
            **tokens,
            "cost_usd":    round(cost, 8),
        }).execute()
        return cost
    except Exception:
        return 0.0


def get_today_spend(business_id: str) -> dict:
    """Returns {total: float, by_dept: {dept_type: float}} for today (UTC)."""
    today = date.today().isoformat()
    rows = (
        get_supabase()
        .table("usage_events")
        .select("dept_type,cost_usd")
        .eq("business_id", business_id)
        .gte("created_at", f"{today}T00:00:00Z")
        .execute()
        .data
    )
    by_dept: dict[str, float] = {}
    total = 0.0
    for row in rows:
        dept = row.get("dept_type") or "other"
        cost = float(row["cost_usd"])
        by_dept[dept] = round(by_dept.get(dept, 0.0) + cost, 8)
        total += cost
    return {"total": round(total, 6), "by_dept": by_dept}


def get_budget_state(business_id: str) -> dict:
    """Full budget context: configured limits + today's spend + remaining amounts."""
    biz = (
        get_supabase()
        .table("businesses")
        .select("daily_budget,dept_budgets")
        .eq("id", business_id)
        .single()
        .execute()
        .data or {}
    )
    daily_budget = biz.get("daily_budget")       # None = unlimited
    dept_budgets = biz.get("dept_budgets") or {}

    spend = get_today_spend(business_id)

    dept_remaining: dict[str, float] = {}
    for dept, alloc in dept_budgets.items():
        if alloc is not None:
            dept_remaining[dept] = max(0.0, float(alloc) - spend["by_dept"].get(dept, 0.0))

    daily_remaining = (
        max(0.0, float(daily_budget) - spend["total"])
        if daily_budget is not None else None
    )

    return {
        "daily_budget":    float(daily_budget) if daily_budget is not None else None,
        "dept_budgets":    {k: float(v) for k, v in dept_budgets.items()},
        "today_spend":     spend["total"],
        "today_by_dept":   spend["by_dept"],
        "daily_remaining": daily_remaining,
        "dept_remaining":  dept_remaining,
    }


def daily_budget_ok(business_id: str) -> tuple[bool, dict]:
    """Returns (allowed, budget_state). allowed=False only when a limit is set and exhausted."""
    state = get_budget_state(business_id)
    ok = state["daily_remaining"] is None or state["daily_remaining"] > 0
    return ok, state
