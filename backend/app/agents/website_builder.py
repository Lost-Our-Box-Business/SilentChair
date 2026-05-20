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


SYSTEM_PROMPT = """You are an expert web developer building a website for a small business.
The user will describe what they want using natural language and you will produce or modify
the website's files accordingly.

When you need to create or update files, output them using this exact format:

__WEBSITE_FILES__
---index.html---
[full file content here]
---style.css---
[full file content here]
__END_FILES__

Rules:
- Always output the COMPLETE content of every file you create or modify — no truncation.
- Only include files that are new or changed; unchanged files are preserved automatically.
- Use clean, modern, semantic HTML5 with inline or linked CSS.
- Make the site mobile-responsive by default.
- When JavaScript is needed, prefer vanilla JS; keep it minimal.
- After the file block, give a brief plain-English summary of what you did or ask a clarifying
  question if the request is ambiguous.
- If no file changes are needed (e.g. user is asking a question), reply normally without the
  file block.
"""


# ── State ────────────────────────────────────────────────────────────────────

class WebsiteState(TypedDict):
    messages: list[dict]         # [{role, content}]
    current_files: list[dict]    # [{path, content}]
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
    system = f"{SYSTEM_PROMPT}\n\n{files_ctx}"

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
    Loads chat history from DB, appends user message, runs graph,
    persists updated history + files, returns {reply, files}.
    """
    sb = get_supabase()

    # Load existing chat history
    row = sb.table("websites").select("chat_history").eq("id", website_id).single().execute()
    history: list[dict] = row.data.get("chat_history") or []

    # Append user message to history
    history.append({"role": "user", "content": message})

    initial_state: WebsiteState = {
        "messages": history,
        "current_files": current_files,
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
