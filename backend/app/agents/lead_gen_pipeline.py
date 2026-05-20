"""
Lead Generation Pipeline — LangGraph StateGraph for the lead_generation archetype.

Flow: budget_coordinator → research_market → find_leads → qualify_leads → draft_outreach →
      [autonomy gate] → send_outreach → done
"""
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.tools import serper
from app.tools import crm as crm_tool
from app.tools import email_outreach


# ── State ─────────────────────────────────────────────────────────────────────

class LeadGenState(TypedDict):
    business_id: str
    business_profile: dict
    tool_keys: dict
    autonomy: str
    active_dept_types: list[str]

    market_research: dict
    leads: list[dict]
    qualified_leads: list[dict]
    outreach_emails: list[dict]
    sent_results: list[dict]

    budget_state: dict

    approval_required: bool
    approval_action: str
    log: list[str]
    error: str | None


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _llm(temperature: float = 0.5) -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=4096,
    )


def _cheap_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=2048,
    )


def _json_call(
    llm: ChatAnthropic, system: str, user: str,
    business_id: str = "", dept_type: str = "",
) -> dict | list:
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    if business_id:
        from app.services.cost_tracker import log_llm_usage
        log_llm_usage(response, business_id, dept_type, llm.model)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Budget coordinator node ───────────────────────────────────────────────────

def budget_coordinator_node(state: LeadGenState) -> dict:
    """CEO agent: enforce budgets, filter departments, log the plan."""
    from app.services.cost_tracker import get_budget_state
    budget = get_budget_state(state["business_id"])
    log = list(state["log"])
    active = list(state["active_dept_types"])

    daily_remaining = budget["daily_remaining"]
    dept_remaining = budget["dept_remaining"]

    if daily_remaining is not None and daily_remaining <= 0:
        log.append(
            f"CEO: daily budget ${budget['daily_budget']:.2f} exhausted "
            f"(spent ${budget['today_spend']:.4f} today) — skipping run"
        )
        return {"active_dept_types": [], "log": log, "budget_state": budget}

    if dept_remaining:
        paused = [d for d in active if d in dept_remaining and dept_remaining[d] <= 0.001]
        active = [d for d in active if d not in paused]
        for d in paused:
            log.append(f"CEO: pausing {d} — department allocation exhausted")

    daily_budget = budget.get("daily_budget")
    if daily_budget and daily_remaining is not None and active and daily_remaining < float(daily_budget) * 0.3:
        try:
            result = _json_call(
                _cheap_llm(),
                """You are the CEO of a lead generation agency with limited budget remaining today.
Decide which departments to run and in what priority order.
Return JSON: {"priority_order": ["dept1", ...], "skip": [], "reasoning": "one sentence"}""",
                f"""Daily budget: ${float(daily_budget):.2f}, remaining: ${daily_remaining:.4f}
Active departments: {', '.join(active)}
Per-dept remaining: {json.dumps({k: round(v, 4) for k, v in dept_remaining.items() if k in active})}""",
            )
            if isinstance(result, dict):
                order = result.get("priority_order", active)
                skip = result.get("skip", [])
                active = [d for d in order if d in active and d not in skip]
                note = result.get("reasoning", "")
                log.append(f"CEO prioritization: {note}")
        except Exception:
            pass

    spend_msg = f"${budget['today_spend']:.4f} spent today"
    if daily_remaining is not None:
        spend_msg += f", ${daily_remaining:.4f} remaining of ${float(daily_budget):.2f}"
    log.append(f"CEO: budget check — {spend_msg}")

    return {"active_dept_types": active, "log": log, "budget_state": budget}


# ── Nodes ─────────────────────────────────────────────────────────────────────

def research_market_node(state: LeadGenState) -> dict:
    profile = state["business_profile"]
    niche = profile.get("niche", "")
    audience = profile.get("target_audience", "")
    log = list(state["log"])
    bid = state["business_id"]

    serper_key = state["tool_keys"].get("serper") or settings.serper_api_key

    raw_research = ""
    if serper_key:
        try:
            results = serper.search(
                f"{niche} target companies ideal client profile {audience}",
                num_results=5,
                api_key=serper_key,
            )
            raw_research = json.dumps(results)
            log.append(f"Market research: gathered data on {niche} market via search")
        except Exception as e:
            log.append(f"Market research: search failed ({e}), using AI analysis")

    market_research = _json_call(
        _cheap_llm(),
        """You are a B2B market research analyst. Return a JSON object with:
- icp (str): description of the Ideal Client Profile
- target_industries (list of 3-5 strings): specific industries to target
- pain_points (list of 3-5 strings): key pain points of the target audience
- decision_makers (list of 2-3 strings): typical job titles to contact
- company_size (str): ideal company size range (e.g. "10-200 employees")
Return ONLY valid JSON.""",
        f"""Business: {profile.get('name')} | Niche: {niche}
Target audience: {audience}
Goals: {profile.get('goals', '')}
{"Search context: " + raw_research if raw_research else ""}

Define the ideal client profile for this business.""",
        business_id=bid,
        dept_type="market_research",
    )
    if not isinstance(market_research, dict):
        market_research = {"icp": audience, "target_industries": [], "pain_points": [], "decision_makers": [], "company_size": "any"}

    log.append(f"Market research: ICP defined — {market_research.get('icp', '')[:80]}")
    return {"market_research": market_research, "log": log}


def find_leads_node(state: LeadGenState) -> dict:
    profile = state["business_profile"]
    market = state["market_research"]
    log = list(state["log"])
    bid = state["business_id"]

    serper_key = state["tool_keys"].get("serper") or settings.serper_api_key
    raw_results = ""

    if serper_key:
        try:
            industries = " OR ".join(market.get("target_industries", [profile.get("niche", "")])[:2])
            query = f'{industries} companies {market.get("company_size", "")} looking for {profile.get("niche", "")}'
            results = serper.search(query, num_results=8, api_key=serper_key)
            raw_results = json.dumps(results)
            log.append("Lead finding: searched for matching companies via Serper")
        except Exception as e:
            log.append(f"Lead finding: search failed ({e}), generating AI leads")

    leads_raw = _json_call(
        _cheap_llm(),
        """You are a lead research specialist. Return a JSON array of 5-8 leads.
Each lead must have:
- name (str): contact person full name
- company (str): company name
- email (str): estimated email (use common patterns like firstname@company.com or info@company.com — mark as estimated)
- title (str): job title
- industry (str): industry
- source (str): how this lead was identified
- notes (str): 1 sentence on why this is a good fit

Return ONLY valid JSON array.""",
        f"""ICP: {market.get('icp', '')}
Target industries: {', '.join(market.get('target_industries', []))}
Decision makers: {', '.join(market.get('decision_makers', []))}
Company size: {market.get('company_size', '')}
{"Search results: " + raw_results if raw_results else ""}

Generate 5-8 realistic leads matching this ICP.""",
        business_id=bid,
        dept_type="lead_research",
    )

    leads = leads_raw if isinstance(leads_raw, list) else []
    log.append(f"Lead finding: identified {len(leads)} potential leads")
    return {"leads": leads, "log": log}


def qualify_leads_node(state: LeadGenState) -> dict:
    leads = state["leads"]
    market = state["market_research"]
    profile = state["business_profile"]
    log = list(state["log"])
    bid = state["business_id"]

    if not leads:
        log.append("Qualification: no leads to qualify")
        return {"qualified_leads": [], "log": log}

    scored = _json_call(
        _cheap_llm(),
        """You are a sales qualification expert. Score each lead 1-10 against the ICP.
Return a JSON array with the original lead data plus:
- score (int 1-10): qualification score
- qualification_reason (str): 1 sentence explaining the score
- qualified (bool): true if score >= 6

Return ONLY valid JSON array.""",
        f"""ICP: {market.get('icp', '')}
Pain points: {', '.join(market.get('pain_points', []))}
Business offering: {profile.get('niche', '')} for {profile.get('target_audience', '')}
Goals: {profile.get('goals', '')}

Leads to score: {json.dumps(leads)}""",
        business_id=bid,
        dept_type="lead_qualification",
    )

    qualified = [l for l in (scored if isinstance(scored, list) else []) if l.get("qualified", False)]
    qualified_leads = sorted(qualified, key=lambda x: x.get("score", 0), reverse=True)[:5]

    log.append(f"Qualification: {len(qualified_leads)} of {len(leads)} leads qualified (score ≥ 6)")
    return {"qualified_leads": qualified_leads, "log": log}


def draft_outreach_node(state: LeadGenState) -> dict:
    leads = state["qualified_leads"]
    profile = state["business_profile"]
    market = state["market_research"]
    log = list(state["log"])
    bid = state["business_id"]

    if not leads:
        log.append("Outreach drafting: no qualified leads to draft for")
        return {"outreach_emails": [], "log": log}

    emails = []

    for lead in leads:
        result = _json_call(
            _llm(temperature=0.7),
            f"""You are a sales copywriter for a {profile.get('niche')} business.
Write a short, personalized cold outreach email.
Return JSON with:
- subject (str): compelling subject line (under 60 chars)
- body_html (str): email body as HTML, 3-4 short paragraphs, no fluff, ends with clear CTA
- preview_text (str): 1-sentence preview (for email clients)

Keep the email concise, specific, and human. Mention the company and a relevant pain point.""",
            f"""Sender: {profile.get('name')} — {profile.get('niche')} business
Lead: {lead.get('name')} at {lead.get('company')} ({lead.get('title')})
Why they're a fit: {lead.get('qualification_reason', lead.get('notes', ''))}
Key pain point to address: {market.get('pain_points', [''])[0]}
Tone: {profile.get('tone_of_voice', 'professional but approachable')}""",
            business_id=bid,
            dept_type="outreach",
        )
        if isinstance(result, dict):
            emails.append({
                "to_name": lead.get("name", ""),
                "to_email": lead.get("email", ""),
                "subject": result.get("subject", f"Quick question for {lead.get('company', '')}"),
                "body_html": result.get("body_html", ""),
                "preview_text": result.get("preview_text", ""),
                "lead_data": lead,
            })

    log.append(f"Outreach: drafted {len(emails)} personalized emails")
    return {"outreach_emails": emails, "log": log}


def autonomy_gate_node(state: LeadGenState) -> dict:
    autonomy = state["autonomy"]
    log = list(state["log"])
    n = len(state["outreach_emails"])
    if autonomy in ("major_decisions", "step_by_step"):
        log.append(f"Gate: awaiting approval to send {n} outreach email(s)")
        return {"approval_required": True, "approval_action": f"Send {n} cold outreach email(s)", "log": log}
    log.append("Gate: full_auto — proceeding to send outreach")
    return {"approval_required": False, "log": log}


def send_outreach_node(state: LeadGenState) -> dict:
    emails = state["outreach_emails"]
    business_id = state["business_id"]
    profile = state["business_profile"]
    log = list(state["log"])

    sent_results = []

    for item in emails:
        lead_data = item.get("lead_data", {})

        try:
            lead_id = crm_tool.save_lead(
                business_id=business_id,
                name=lead_data.get("name", item["to_name"]),
                company=lead_data.get("company", ""),
                email=item["to_email"],
                source=lead_data.get("source", "pipeline"),
                score=lead_data.get("score", 0),
                notes=lead_data.get("qualification_reason", lead_data.get("notes", "")),
                status="contacted",
            )
        except Exception as e:
            log.append(f"CRM: failed to save lead {item['to_name']} ({e})")
            lead_id = None

        result = email_outreach.send_outreach_email(
            to_email=item["to_email"],
            to_name=item["to_name"],
            subject=item["subject"],
            body_html=item["body_html"],
            from_name=profile.get("name", "SilentChair"),
        )
        result["to_email"] = item["to_email"]
        result["lead_id"] = lead_id
        sent_results.append(result)

        status = result.get("status", "unknown")
        log.append(f"Outreach: email to {item['to_name']} at {lead_data.get('company', '')} — {status}")

    return {"sent_results": sent_results, "log": log}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_budget(state: LeadGenState) -> str:
    return "research_market" if state.get("active_dept_types") else END


def route_after_gate(state: LeadGenState) -> str:
    return END if state.get("approval_required") else "send_outreach"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_lead_gen_pipeline() -> StateGraph:
    graph = StateGraph(LeadGenState)
    graph.add_node("budget_coordinator", budget_coordinator_node)
    graph.add_node("research_market", research_market_node)
    graph.add_node("find_leads", find_leads_node)
    graph.add_node("qualify_leads", qualify_leads_node)
    graph.add_node("draft_outreach", draft_outreach_node)
    graph.add_node("autonomy_gate", autonomy_gate_node)
    graph.add_node("send_outreach", send_outreach_node)

    graph.set_entry_point("budget_coordinator")
    graph.add_conditional_edges("budget_coordinator", route_after_budget, {"research_market": "research_market", END: END})
    graph.add_edge("research_market", "find_leads")
    graph.add_edge("find_leads", "qualify_leads")
    graph.add_edge("qualify_leads", "draft_outreach")
    graph.add_edge("draft_outreach", "autonomy_gate")
    graph.add_conditional_edges("autonomy_gate", route_after_gate, {"send_outreach": "send_outreach", END: END})
    graph.add_edge("send_outreach", END)

    return graph.compile()


def run_lead_gen_pipeline(
    business_id: str,
    business_profile: dict,
    tool_keys: dict,
    autonomy: str,
    active_dept_types: list[str],
) -> LeadGenState:
    graph = build_lead_gen_pipeline()
    initial: LeadGenState = {
        "business_id": business_id,
        "business_profile": business_profile,
        "tool_keys": tool_keys,
        "autonomy": autonomy,
        "active_dept_types": active_dept_types,
        "market_research": {},
        "leads": [],
        "qualified_leads": [],
        "outreach_emails": [],
        "sent_results": [],
        "budget_state": {},
        "approval_required": False,
        "approval_action": "",
        "log": [],
        "error": None,
    }
    return graph.invoke(initial)
