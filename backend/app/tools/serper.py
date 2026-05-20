"""Serper — Google Search API wrapper used by research agents."""
import httpx
from app.config import settings


def search(query: str, num_results: int = 5, api_key: str | None = None) -> list[dict]:
    key = api_key or settings.serper_api_key
    response = httpx.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
        })
    return results


def search_topics(niche: str, audience: str, api_key: str | None = None) -> list[str]:
    """Search for trending content topics for the given niche."""
    queries = [
        f"trending topics {niche} {audience} 2026",
        f"best {niche} content ideas this week",
    ]
    seen: set[str] = set()
    topics: list[str] = []
    for q in queries:
        for r in search(q, num_results=5, api_key=api_key):
            title = r["title"].strip()
            if title and title not in seen:
                seen.add(title)
                topics.append(title)
    return topics[:8]
