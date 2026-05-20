"""CRM tool — persists leads, contracts, and invoices to Supabase."""
import uuid
from app.db.client import get_supabase


# ── Leads ────────────────────────────────────────────────────────────────────

def save_lead(
    business_id: str,
    name: str,
    company: str = "",
    email: str = "",
    phone: str = "",
    source: str = "",
    score: int = 0,
    notes: str = "",
    status: str = "new",
) -> str:
    """Insert a lead and return its id."""
    db = get_supabase()
    row_id = str(uuid.uuid4())
    db.table("leads").insert({
        "id": row_id,
        "business_id": business_id,
        "name": name,
        "company": company,
        "email": email,
        "phone": phone,
        "source": source,
        "score": score,
        "notes": notes,
        "status": status,
    }).execute()
    return row_id


def update_lead_status(lead_id: str, status: str) -> None:
    db = get_supabase()
    db.table("leads").update({"status": status}).eq("id", lead_id).execute()


def get_leads(business_id: str) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("leads")
        .select("*")
        .eq("business_id", business_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


# ── Contracts ────────────────────────────────────────────────────────────────

def save_contract(
    business_id: str,
    title: str,
    content: str,
    lead_id: str | None = None,
    status: str = "draft",
) -> str:
    db = get_supabase()
    row_id = str(uuid.uuid4())
    db.table("contracts").insert({
        "id": row_id,
        "business_id": business_id,
        "lead_id": lead_id,
        "title": title,
        "content": content,
        "status": status,
    }).execute()
    return row_id


def get_contracts(business_id: str) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("contracts")
        .select("*")
        .eq("business_id", business_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


# ── Invoices ─────────────────────────────────────────────────────────────────

def save_invoice(
    business_id: str,
    title: str,
    content: str,
    amount: float = 0.0,
    lead_id: str | None = None,
    contract_id: str | None = None,
    status: str = "draft",
) -> str:
    db = get_supabase()
    row_id = str(uuid.uuid4())
    db.table("invoices").insert({
        "id": row_id,
        "business_id": business_id,
        "lead_id": lead_id,
        "contract_id": contract_id,
        "title": title,
        "content": content,
        "amount": amount,
        "status": status,
    }).execute()
    return row_id


def get_invoices(business_id: str) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("invoices")
        .select("*")
        .eq("business_id", business_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data
