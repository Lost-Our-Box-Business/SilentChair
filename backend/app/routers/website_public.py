"""Public (unauthenticated) website content API.

Served under /public prefix. These endpoints are called by published
websites at {slug}.silentchair.app to fetch dynamic content sections.
CORS is handled via allow_origin_regex in CORSMiddleware (main.py) and
explicit headers set on each response below.
"""
from fastapi import APIRouter, HTTPException, Response

from app.db.client import get_supabase

router = APIRouter(tags=["website-public"])


@router.get("/website/{website_id}/sections")
async def get_public_sections(
    response: Response,
    website_id: str,
    type: str | None = None,
):
    """Return published content sections for a website.

    Query params:
      type — filter by section type (testimonial, team_member, portfolio_item, blog_post)
    """
    # Belt-and-suspenders CORS for published-site origins
    response.headers["access-control-allow-origin"] = "*"
    response.headers["cache-control"] = "public, max-age=60"

    sb = get_supabase()
    query = (
        sb.table("website_sections")
        .select("id, type, title, subtitle, body, image_url, metadata, display_order")
        .eq("website_id", website_id)
        .eq("is_published", True)
        .order("display_order")
    )
    if type:
        query = query.eq("type", type)

    result = query.execute()
    return {"sections": result.data or []}
