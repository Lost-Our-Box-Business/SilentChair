"""
Business Analyst agent — conducts a structured interview to produce a business profile.
Uses LangGraph for stateful multi-turn conversation with completion detection.
"""
import json
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.config import settings

SYSTEM_PROMPT = """You are a Business Analyst at SilentChair, an AI workforce platform.
Your job is to conduct a friendly, focused interview to gather everything needed to set up an AI-powered business for the user.

You need to collect all of the following before the interview is complete:
1. Business name (or working title)
2. Business niche / industry
3. Target audience (who are the ideal customers/readers/clients)
4. Top 2-3 goals for the business in the first 6 months
5. Tone of voice (professional, casual, witty, authoritative, etc.)
6. Key performance indicators (what does success look like — traffic, revenue, subscribers, etc.)
7. Preferred publishing/distribution channels (blog, Instagram, newsletter, YouTube, etc.)

Rules:
- Ask 1-2 questions at a time. Never dump all questions at once.
- Be conversational and encouraging.
- When you have enough information for ALL seven items above, end your message with the exact token: [INTERVIEW_COMPLETE]
- Do NOT include [INTERVIEW_COMPLETE] until you genuinely have enough for all seven items.
- Do NOT ask about technical setup, API keys, or agents — that comes later.
- If the user gives vague answers, ask one clarifying follow-up before moving on.
"""

EXTRACTION_PROMPT = """Based on this interview conversation, extract the business profile as JSON.

Return ONLY valid JSON matching this schema exactly:
{
  "name": "business name or working title",
  "niche": "specific niche/industry",
  "target_audience": "description of ideal customer/reader",
  "goals": ["goal 1", "goal 2", "goal 3"],
  "tone_of_voice": "tone description",
  "kpis": ["kpi 1", "kpi 2"],
  "publishing_channels": ["channel 1", "channel 2"],
  "additional_notes": "anything else relevant"
}

Conversation:
{conversation}
"""


class InterviewState(TypedDict):
    messages: Annotated[list, add_messages]
    is_complete: bool
    business_profile: dict | None


def _build_llm(temperature: float = 0.7) -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=1024,
    )


def _build_extraction_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=1024,
    )


def analyst_node(state: InterviewState) -> dict:
    llm = _build_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    content = response.content

    is_complete = "[INTERVIEW_COMPLETE]" in content
    clean_content = content.replace("[INTERVIEW_COMPLETE]", "").strip()

    business_profile = None
    if is_complete:
        business_profile = _extract_profile(state["messages"] + [AIMessage(content=clean_content)])

    return {
        "messages": [AIMessage(content=clean_content)],
        "is_complete": is_complete,
        "business_profile": business_profile,
    }


def _extract_profile(messages: list) -> dict | None:
    llm = _build_extraction_llm()
    conversation_text = "\n".join(
        f"{m.type.upper()}: {m.content}" for m in messages
    )
    prompt = EXTRACTION_PROMPT.format(conversation=conversation_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        return None


def route_after_analyst(state: InterviewState) -> str:
    return END


def build_interview_graph() -> StateGraph:
    graph = StateGraph(InterviewState)
    graph.add_node("analyst", analyst_node)
    graph.set_entry_point("analyst")
    graph.add_conditional_edges("analyst", route_after_analyst)
    return graph.compile()


def run_interview_turn(history: list[dict], user_message: str) -> dict:
    """
    Run one turn of the interview.
    history: list of {"role": "user"|"assistant", "content": str}
    Returns: {"message": str, "is_complete": bool, "business_profile": dict|None}
    """
    graph = build_interview_graph()

    lc_messages = []
    for msg in history:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))
    lc_messages.append(HumanMessage(content=user_message))

    result = graph.invoke({
        "messages": lc_messages,
        "is_complete": False,
        "business_profile": None,
    })

    last_ai = next(
        (m for m in reversed(result["messages"]) if isinstance(m, AIMessage)),
        None,
    )

    return {
        "message": last_ai.content if last_ai else "",
        "is_complete": result["is_complete"],
        "business_profile": result["business_profile"],
    }
