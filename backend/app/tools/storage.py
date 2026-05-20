import os
from app.db.client import get_supabase


WEBSITE_BUCKET = "websites"


def upload_website_files(subdomain: str, files: list[dict]) -> None:
    """Upload website files to Supabase Storage under {subdomain}/{path}."""
    sb = get_supabase()
    for f in files:
        path = f["path"].lstrip("/")
        key = f"{subdomain}/{path}"
        content = f["content"].encode("utf-8")
        content_type = _guess_content_type(path)
        try:
            sb.storage.from_(WEBSITE_BUCKET).upload(
                key,
                content,
                file_options={"content-type": content_type, "upsert": "true"},
            )
        except Exception:
            sb.storage.from_(WEBSITE_BUCKET).update(
                key,
                content,
                file_options={"content-type": content_type},
            )


def get_public_url(subdomain: str, path: str) -> str:
    """Return the public URL for a file in the websites bucket."""
    sb = get_supabase()
    key = f"{subdomain}/{path.lstrip('/')}"
    return sb.storage.from_(WEBSITE_BUCKET).get_public_url(key)


def _guess_content_type(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
        "json": "application/json",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
        "woff": "font/woff",
        "woff2": "font/woff2",
    }.get(ext, "text/plain")
