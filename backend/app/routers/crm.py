"""CRM endpoints — leads, contracts, invoices."""
from fastapi import APIRouter, HTTPException
from app.tools.crm import get_leads, get_contracts, get_invoices
from app.db.client import get_supabase

router = APIRouter(prefix="/crm", tags=["crm"])


@router.get("/leads/{business_id}")
async def list_leads(business_id: str):
    return get_leads(business_id)


@router.get("/contracts/{business_id}")
async def list_contracts(business_id: str):
    return get_contracts(business_id)


@router.get("/invoices/{business_id}")
async def list_invoices(business_id: str):
    return get_invoices(business_id)


@router.patch("/leads/{lead_id}/status")
async def update_lead(lead_id: str, status: str):
    valid = {"new", "contacted", "qualified", "proposal_sent", "won", "lost"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid)}")
    db = get_supabase()
    result = db.table("leads").update({"status": status}).eq("id", lead_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result.data[0]


@router.patch("/contracts/{contract_id}/status")
async def update_contract(contract_id: str, status: str):
    valid = {"draft", "sent", "signed"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid)}")
    db = get_supabase()
    result = db.table("contracts").update({"status": status}).eq("id", contract_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Contract not found")
    return result.data[0]


@router.patch("/invoices/{invoice_id}/status")
async def update_invoice(invoice_id: str, status: str):
    valid = {"draft", "sent", "paid"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid)}")
    db = get_supabase()
    result = db.table("invoices").update({"status": status}).eq("id", invoice_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result.data[0]
