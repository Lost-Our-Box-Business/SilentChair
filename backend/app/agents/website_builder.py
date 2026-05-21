"""
Website Builder Agent — single-turn LangGraph node that receives a user message
and the current website files, then produces updated files and a reply.

File changes are communicated using sentinel blocks:

    __WEBSITE_FILES__
    ---index.html---
    <!DOCTYPE html>...
    ---style.css---
    body { ... }
    __END_FILES__

Files not included in a response are preserved unchanged (_merge_files).
"""
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.db.client import get_supabase


SYSTEM_PROMPT_TEMPLATE = """You are an expert web developer and designer creating a professional website for a real business. You produce websites that look like they were built by a top-tier design agency — polished, modern, with excellent typography, visual hierarchy, and compelling copy.

{business_context}

When creating or updating files, use this exact format:

__WEBSITE_FILES__
---index.html---
[complete file content]
---style.css---
[complete file content]
__END_FILES__

━━━ DESIGN STANDARDS ━━━
Typography:
- Load 1–2 Google Fonts via a <link> tag (e.g. Inter, DM Sans, Playfair Display, Plus Jakarta Sans)
- Use a clear type scale: hero 48–72px, h2 32–40px, body 16–18px, small 14px
- Line-height 1.5–1.7 for body, 1.1–1.2 for headings

Layout & spacing:
- CSS Grid and Flexbox only — no Bootstrap, no jQuery
- Section padding: 80–120px top/bottom; max-width 1200px centered with auto margins
- Generous whitespace makes content breathe

Colour:
- Pick a palette of 2–3 colours that fit the business's industry and tone
- Define them as CSS custom properties (--color-primary, --color-accent, etc.)
- Use a near-white or light background; avoid pure #fff/#000

Visual polish:
- Subtle hover transitions (0.2s ease) on all interactive elements
- Box shadows for cards: box-shadow: 0 2px 12px rgba(0,0,0,0.08)
- Rounded corners: border-radius 8–16px on cards/buttons
- Add at least one gradient or decorative background element (hero gradient, accent band, etc.)

Images:
- Use specific, relevant Unsplash photos: https://images.unsplash.com/photo-[id]?w=1200&q=80
- Pick IDs that genuinely match the business's industry

━━━ CONTENT STANDARDS ━━━
- Write REAL copy using the business profile — business name, niche, services, audience, tone
- No "Lorem ipsum", no "[Your Business Name]" placeholders
- Hero: strong, specific headline + 1–2 sentence subtext that speaks to the target audience
- Include a nav bar, hero, 2–3 content sections (services/features/about), and a footer
- Footer: business name, tagline, and any contact info from the profile

━━━ RULES ━━━
- Output the COMPLETE content of every file — never truncate, never use "..." or "[continues]"
- Only include files that changed; unchanged files are preserved automatically
- After the file block, write 1–2 sentences summarising what you built or changed
- If the user asks a question with no file changes needed, reply without the file block
"""


def _build_system_prompt(business_profile: dict) -> str:
    if business_profile:
        lines = ["Business profile for this website:"]
        field_labels = {
            "name": "Business name",
            "niche": "Industry/niche",
            "target_audience": "Target audience",
            "goals": "Goals",
            "tone": "Tone of voice",
            "services": "Services/products",
            "location": "Location",
            "contact_email": "Contact email",
            "contact_phone": "Contact phone",
            "website_url": "Existing website",
        }
        for key, label in field_labels.items():
            value = business_profile.get(key)
            if value:
                lines.append(f"  {label}: {value}")
        # Also dump any other fields not in the known list
        for key, value in business_profile.items():
            if key not in field_labels and value:
                lines.append(f"  {key}: {value}")
        business_context = "\n".join(lines)
    else:
        business_context = "No business profile available — use whatever details the user provides."
    return SYSTEM_PROMPT_TEMPLATE.format(business_context=business_context)


# ── State ────────────────────────────────────────────────────────────────────

class WebsiteState(TypedDict):
    messages: list[dict]         # [{role, content}]
    current_files: list[dict]    # [{path, content}]
    business_profile: dict
    reply: str
    updated_files: list[dict]    # merged result


# ── File helpers ─────────────────────────────────────────────────────────────

def _parse_files(text: str) -> list[dict]:
    """Extract files from the sentinel block in the model's response."""
    if "__WEBSITE_FILES__" not in text:
        return []
    try:
        inner = text.split("__WEBSITE_FILES__", 1)[1].split("__END_FILES__", 1)[0]
    except IndexError:
        return []

    files = []
    parts = re.split(r"---([^-\n]+)---\n?", inner)
    # parts: ["", filename1, content1, filename2, content2, ...]
    it = iter(parts[1:])
    for filename, content in zip(it, it):
        filename = filename.strip()
        content = content.rstrip("\n")
        if filename:
            files.append({"path": filename, "content": content})
    return files


def _merge_files(current: list[dict], new: list[dict]) -> list[dict]:
    """Merge new files into current, preserving files not in new."""
    merged = {f["path"]: f["content"] for f in current}
    for f in new:
        merged[f["path"]] = f["content"]
    return [{"path": p, "content": c} for p, c in merged.items()]


def _files_context(files: list[dict]) -> str:
    """Summarise current files for the system context."""
    if not files:
        return "No files exist yet — this is a fresh project."
    lines = ["Current website files:"]
    for f in files:
        lines.append(f"  - {f['path']} ({len(f['content'])} chars)")
    return "\n".join(lines)


# ── LLM ──────────────────────────────────────────────────────────────────────

def _llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=8192,
    )


# ── Node ─────────────────────────────────────────────────────────────────────

def builder_node(state: WebsiteState) -> WebsiteState:
    llm = _llm()
    files_ctx = _files_context(state["current_files"])
    system = _build_system_prompt(state.get("business_profile") or {}) + f"\n\n{files_ctx}"

    lc_messages = [SystemMessage(content=system)]
    for msg in state["messages"]:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            from langchain_core.messages import AIMessage
            lc_messages.append(AIMessage(content=msg["content"]))

    response = llm.invoke(lc_messages)
    raw = response.content

    new_files = _parse_files(raw)
    # Strip file block from the reply shown to user
    reply = re.sub(
        r"__WEBSITE_FILES__.*?__END_FILES__", "", raw, flags=re.DOTALL
    ).strip()
    if not reply:
        reply = "Done! The files have been updated."

    updated = _merge_files(state["current_files"], new_files)

    return {**state, "reply": reply, "updated_files": updated}


# ── Graph ─────────────────────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    g = StateGraph(WebsiteState)
    g.add_node("builder", builder_node)
    g.set_entry_point("builder")
    g.add_edge("builder", END)
    return g.compile()


_graph = _build_graph()


# ── Public API ────────────────────────────────────────────────────────────────

def run_website_turn(
    website_id: str,
    message: str,
    current_files: list[dict],
) -> dict:
    """
    Run one turn of the website builder conversation.
    Loads chat history and business profile from DB, appends user message,
    runs graph, persists updated history + files, returns {reply, files}.
    """
    sb = get_supabase()

    # Load website + joined business profile in one go
    row = sb.table("websites").select("chat_history, business_id").eq("id", website_id).single().execute()
    history: list[dict] = row.data.get("chat_history") or []
    business_id: str = row.data.get("business_id", "")

    business_profile: dict = {}
    if business_id:
        biz = sb.table("businesses").select("profile, name").eq("id", business_id).single().execute()
        if biz.data:
            business_profile = biz.data.get("profile") or {}
            # Ensure business name is always available
            if not business_profile.get("name") and biz.data.get("name"):
                business_profile["name"] = biz.data["name"]

    # Append user message to history
    history.append({"role": "user", "content": message})

    initial_state: WebsiteState = {
        "messages": history,
        "current_files": current_files,
        "business_profile": business_profile,
        "reply": "",
        "updated_files": [],
    }

    result = _graph.invoke(initial_state)
    reply: str = result["reply"]
    updated_files: list[dict] = result["updated_files"]

    # Append assistant reply to history
    history.append({"role": "assistant", "content": reply})

    # Persist
    sb.table("websites").update({
        "chat_history": history,
        "files": updated_files,
        "updated_at": "now()",
    }).eq("id", website_id).execute()

    return {"reply": reply, "files": updated_files}
