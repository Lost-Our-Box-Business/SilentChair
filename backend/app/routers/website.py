"""Website builder endpoints."""
import re
from fastapi import APIRouter, HTTPException

from app.db.client import get_supabase
from app.models.website import (
    WebsiteTurnRequest,
    WebsiteTurnResponse,
    WebsiteRecord,
    WebsiteFile,
    ChatMessage,
    CustomDomainRequest,
)
from app.agents.website_builder import run_website_turn
from app.tools.storage import upload_website_files, get_public_url

router = APIRouter(tags=["website"])


def _slugify(name: str) -> str:
    """Convert a business name to a URL-safe subdomain slug."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:50] if slug else "site"


def _unique_subdomain(base: str) -> str:
    sb = get_supabase()
    slug = base
    suffix = 1
    while True:
        existing = sb.table("websites").select("id").eq("subdomain", slug).execute()
        if not existing.data:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


@router.post("/website/turn", response_model=WebsiteTurnResponse)
async def website_turn(req: WebsiteTurnRequest):
    sb = get_supabase()

    # Verify website exists
    row = sb.table("websites").select("id,business_id,subdomain").eq("id", req.website_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Website not found")

    current_files = [f.model_dump() for f in req.current_files]
    result = run_website_turn(req.website_id, req.message, current_files)

    return WebsiteTurnResponse(
        website_id=req.website_id,
        reply=result["reply"],
        files=[WebsiteFile(**f) for f in result["files"]],
    )


@router.get("/website/{website_id}", response_model=WebsiteRecord)
async def get_website(website_id: str):
    sb = get_supabase()
    row = sb.table("websites").select("*").eq("id", website_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Website not found")
    data = row.data[0]
    return WebsiteRecord(
        id=data["id"],
        business_id=data["business_id"],
        subdomain=data["subdomain"],
        custom_domain=data.get("custom_domain"),
        files=[WebsiteFile(**f) for f in (data.get("files") or [])],
        chat_history=[ChatMessage(**m) for m in (data.get("chat_history") or [])],
        published_url=data.get("published_url"),
        status=data["status"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


@router.get("/website/by-business/{business_id}", response_model=WebsiteRecord | None)
async def get_website_by_business(business_id: str):
    sb = get_supabase()
    row = sb.table("websites").select("*").eq("business_id", business_id).limit(1).execute()
    if not row.data:
        return None
    data = row.data[0]
    return WebsiteRecord(
        id=data["id"],
        business_id=data["business_id"],
        subdomain=data["subdomain"],
        custom_domain=data.get("custom_domain"),
        files=[WebsiteFile(**f) for f in (data.get("files") or [])],
        chat_history=[ChatMessage(**m) for m in (data.get("chat_history") or [])],
        published_url=data.get("published_url"),
        status=data["status"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


@router.post("/website/create")
async def create_website(payload: dict):
    """Create a new website record for a business. Payload: {business_id, business_name?}."""
    business_id = payload.get("business_id")
    business_name = payload.get("business_name", "")
    if not business_id:
        raise HTTPException(status_code=422, detail="business_id required")

    sb = get_supabase()

    # Return existing if already created
    existing = sb.table("websites").select("*").eq("business_id", business_id).limit(1).execute()
    if existing.data:
        data = existing.data[0]
        return {"id": data["id"], "subdomain": data["subdomain"]}

    base = _slugify(business_name) if business_name else "site"
    subdomain = _unique_subdomain(base)

    result = sb.table("websites").insert({
        "business_id": business_id,
        "subdomain": subdomain,
    }).execute()
    data = result.data[0]
    return {"id": data["id"], "subdomain": data["subdomain"]}


@router.post("/website/{website_id}/publish")
async def publish_website(website_id: str):
    sb = get_supabase()
    row = sb.table("websites").select("subdomain,files").eq("id", website_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Website not found")
    data = row.data[0]
    files = data.get("files") or []
    subdomain = data["subdomain"]

    if not files:
        raise HTTPException(status_code=400, detail="No files to publish")

    upload_website_files(subdomain, files)
    published_url = f"https://{subdomain}.silentchair.app"

    sb.table("websites").update({
        "published_url": published_url,
        "status": "published",
        "updated_at": "now()",
    }).eq("id", website_id).execute()

    return {"published_url": published_url}


@router.patch("/website/{website_id}/custom_domain")
async def set_custom_domain(website_id: str, req: CustomDomainRequest):
    sb = get_supabase()
    row = sb.table("websites").select("id").eq("id", website_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Website not found")

    sb.table("websites").update({
        "custom_domain": req.custom_domain,
        "updated_at": "now()",
    }).eq("id", website_id).execute()

    return {"custom_domain": req.custom_domain}
