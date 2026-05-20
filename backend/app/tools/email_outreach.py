"""Email outreach tool — sends cold/warm outreach emails via Resend."""
import httpx
from app.config import settings


def send_outreach_email(
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    from_name: str = "SilentChair",
    reply_to: str | None = None,
) -> dict:
    """Send a single outreach email. Returns {id, status} or raises on failure."""
    if not settings.resend_api_key:
        return {"id": None, "status": "simulated", "reason": "no Resend key configured"}

    payload: dict = {
        "from": f"{from_name} <noreply@silentchair.ai>",
        "to": [f"{to_name} <{to_email}>"],
        "subject": subject,
        "html": body_html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    return {"id": data.get("id"), "status": "sent"}


def send_bulk_outreach(emails: list[dict], from_name: str = "SilentChair") -> list[dict]:
    """
    Send multiple outreach emails.

    Each item in `emails` must have: to_email, to_name, subject, body_html.
    Returns list of {to_email, status, id, error}.
    """
    results = []
    for item in emails:
        try:
            result = send_outreach_email(
                to_email=item["to_email"],
                to_name=item["to_name"],
                subject=item["subject"],
                body_html=item["body_html"],
                from_name=from_name,
                reply_to=item.get("reply_to"),
            )
            results.append({"to_email": item["to_email"], **result})
        except Exception as e:
            results.append({"to_email": item["to_email"], "status": "failed", "error": str(e)})
    return results
