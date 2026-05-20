"""WordPress REST API — publishes posts to a self-hosted WordPress or WordPress.com site."""
import base64
import httpx


def publish_post(
    site_url: str,
    username: str,
    app_password: str,
    title: str,
    content: str,
    status: str = "publish",
    tags: list[str] | None = None,
) -> dict:
    credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    payload: dict = {"title": title, "content": content, "status": status}
    if tags:
        payload["tags"] = tags

    api_url = site_url.rstrip("/") + "/wp-json/wp/v2/posts"
    response = httpx.post(api_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return {"post_id": data.get("id"), "url": data.get("link"), "status": data.get("status")}


def parse_wp_config(config_str: str) -> dict:
    """Parse a WordPress config string: 'https://mysite.com|username|app_password'"""
    parts = config_str.split("|")
    if len(parts) != 3:
        raise ValueError("WordPress config must be 'site_url|username|app_password'")
    return {"site_url": parts[0], "username": parts[1], "app_password": parts[2]}
