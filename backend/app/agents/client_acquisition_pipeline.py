"""
Client Acquisition Pipeline — LangGraph StateGraph for the client_acquisition archetype.

Flow: budget_coordinator → research_market → find_leads → qualify_leads → draft_outreach →
      [gate] → send_outreach → draft_proposals → generate_contracts →
      generate_invoices → done

Proposals, contracts, and invoices are saved to Supabase (not sent automatically).
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

class ClientAcquisitionState(TypedDict):
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
    proposals: list[dict]
    contracts: list[dict]
    invoices: list[dict]

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
        max_tokens=8192,
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

def budget_coordinator_node(state: ClientAcquisitionState) -> dict:
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
                """You are the CEO of a client acquisition agency with limited budget remaining today.
Prioritize which departments to run to maximize deal value.
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

def research_market_node(state: ClientAcquisitionState) -> dict:
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
                f"{niche} B2B clients ideal customer profile {audience}",
                num_results=5,
                api_key=serper_key,
            )
            raw_research = json.dumps(results)
            log.append("Market research: gathered data via search")
        except Exception as e:
            log.append(f"Market research: search failed ({e}), using AI analysis")

    market_research = _json_call(
        _cheap_llm(),
        """You are a B2B market research analyst. Return a JSON object with:
- icp (str): Ideal Client Profile description
- target_industries (list of 3-5 strings): industries to target
- pain_points (list of 3-5 strings): client pain points
- decision_makers (list of 2-3 strings): job titles to contact
- company_size (str): ideal company size
- avg_deal_size (str): estimated deal value range
Return ONLY valid JSON.""",
        f"""Business: {profile.get('name')} | Niche: {niche}
Target audience: {audience}
Goals: {profile.get('goals', '')}
{"Search context: " + raw_research if raw_research else ""}""",
        business_id=bid,
        dept_type="market_research",
    )
    if not isinstance(market_research, dict):
        market_research = {"icp": audience, "target_industries": [], "pain_points": [], "decision_makers": [], "company_size": "any", "avg_deal_size": "TBD"}

    log.append(f"Market research: ICP defined — {market_research.get('icp', '')[:80]}")
    return {"market_research": market_research, "log": log}


def find_leads_node(state: ClientAcquisitionState) -> dict:
    profile = state["business_profile"]
    market = state["market_research"]
    log = list(state["log"])
    bid = state["business_id"]

    serper_key = state["tool_keys"].get("serper") or settings.serper_api_key
    raw_results = ""

    if serper_key:
        try:
            industries = " OR ".join(market.get("target_industries", [profile.get("niche", "")])[:2])
            query = f'{industries} companies hiring or budget for {profile.get("niche", "services")}'
            results = serper.search(query, num_results=8, api_key=serper_key)
            raw_results = json.dumps(results)
            log.append("Lead finding: searched for target companies")
        except Exception as e:
            log.append(f"Lead finding: search failed ({e}), generating AI leads")

    leads_raw = _json_call(
        _cheap_llm(),
        """Return a JSON array of 5 realistic B2B leads.
Each lead: name, company, email (estimated), title, industry, source, notes (fit reason).
Return ONLY valid JSON array.""",
        f"""ICP: {market.get('icp', '')}
Industries: {', '.join(market.get('target_industries', []))}
Decision makers: {', '.join(market.get('decision_makers', []))}
Company size: {market.get('company_size', '')}
{"Search results: " + raw_results if raw_results else ""}""",
        business_id=bid,
        dept_type="lead_generation",
    )
    leads = leads_raw if isinstance(leads_raw, list) else []
    log.append(f"Lead finding: identified {len(leads)} potential leads")
    return {"leads": leads, "log": log}


def qualify_leads_node(state: ClientAcquisitionState) -> dict:
    leads = state["leads"]
    market = state["market_research"]
    profile = state["business_profile"]
    log = list(state["log"])
    bid = state["business_id"]

    if not leads:
        return {"qualified_leads": [], "log": log}

    scored = _json_call(
        _cheap_llm(),
        """Score each lead 1-10 against the ICP. Return JSON array with original data plus:
- score (int 1-10)
- qualification_reason (str): one sentence
- qualified (bool): true if score >= 7
Return ONLY valid JSON array.""",
        f"""ICP: {market.get('icp', '')}
Pain points: {', '.join(market.get('pain_points', []))}
Offering: {profile.get('niche', '')} for {profile.get('target_audience', '')}
Leads: {json.dumps(leads)}""",
        business_id=bid,
        dept_type="lead_generation",
    )
    qualified = [l for l in (scored if isinstance(scored, list) else []) if l.get("qualified")]
    qualified_leads = sorted(qualified, key=lambda x: x.get("score", 0), reverse=True)[:3]

    log.append(f"Qualification: top {len(qualified_leads)} prospects selected for acquisition pipeline")
    return {"qualified_leads": qualified_leads, "log": log}


def draft_outreach_node(state: ClientAcquisitionState) -> dict:
    leads = state["qualified_leads"]
    profile = state["business_profile"]
    market = state["market_research"]
    log = list(state["log"])
    bid = state["business_id"]

    if not leads:
        return {"outreach_emails": [], "log": log}

    emails = []

    for lead in leads:
        result = _json_call(
            _llm(temperature=0.7),
            f"""You are a sales copywriter for a {profile.get('niche')} business.
Write a concise, personalized B2B cold email.
Return JSON: subject (str), body_html (str — 3 paragraphs), preview_text (str).
The email should introduce the business, reference a specific pain point, and propose a discovery call.""",
            f"""Sender: {profile.get('name')} | Niche: {profile.get('niche')}
Lead: {lead.get('name')} at {lead.get('company')} ({lead.get('title')})
Pain point: {market.get('pain_points', [''])[0]}
Why they fit: {lead.get('qualification_reason', '')}
Tone: {profile.get('tone_of_voice', 'professional')}""",
            business_id=bid,
            dept_type="sales_outreach",
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


def autonomy_gate_node(state: ClientAcquisitionState) -> dict:
    autonomy = state["autonomy"]
    log = list(state["log"])
    n = len(state["outreach_emails"])
    if autonomy in ("major_decisions", "step_by_step"):
        log.append(f"Gate: awaiting approval to send {n} outreach email(s)")
        return {"approval_required": True, "approval_action": f"Send {n} outreach email(s) to qualified prospects", "log": log}
    log.append("Gate: full_auto — proceeding to outreach")
    return {"approval_required": False, "log": log}


def send_outreach_node(state: ClientAcquisitionState) -> dict:
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
                notes=lead_data.get("qualification_reason", ""),
                status="contacted",
            )
        except Exception as e:
            log.append(f"CRM: failed to save lead ({e})")
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
        log.append(f"Outreach sent: {item['to_name']} at {lead_data.get('company', '')} — {result.get('status')}")

    return {"sent_results": sent_results, "log": log}


def draft_proposals_node(state: ClientAcquisitionState) -> dict:
    leads = state["qualified_leads"]
    profile = state["business_profile"]
    market = state["market_research"]
    sent = state["sent_results"]
    log = list(state["log"])
    bid = state["business_id"]

    lead_id_map = {r["to_email"]: r.get("lead_id") for r in sent}
    proposals = []

    for lead in leads:
        lead_email = lead.get("email", "")
        lead_id = lead_id_map.get(lead_email)

        result = _json_call(
            _llm(temperature=0.4),
            f"""You are a senior consultant writing a professional proposal for a {profile.get('niche')} engagement.
Return JSON with:
- title (str): proposal title
- content_html (str): complete HTML proposal with sections:
  <h2>Executive Summary</h2>
  <h2>Understanding Your Challenges</h2>
  <h2>Our Approach</h2>
  <h2>Scope of Work</h2>
  <h2>Deliverables</h2>
  <h2>Timeline</h2>
  <h2>Investment</h2>
  <h2>Why {profile.get('name', 'Us')}</h2>
  <h2>Next Steps</h2>
- estimated_value (float): total proposed engagement value in USD
Return ONLY valid JSON.""",
            f"""Client: {lead.get('name')} at {lead.get('company')} ({lead.get('title')})
Industry: {lead.get('industry', '')}
Pain points: {', '.join(market.get('pain_points', []))}
Our offering: {profile.get('niche')} for {profile.get('target_audience', '')}
Business goals: {profile.get('goals', '')}
Estimated deal size: {market.get('avg_deal_size', 'TBD')}""",
            business_id=bid,
            dept_type="proposals_contracts",
        )
        if isinstance(result, dict):
            proposals.append({
                "lead_name": lead.get("name", ""),
                "company": lead.get("company", ""),
                "title": result.get("title", f"Proposal for {lead.get('company', '')}"),
                "content_html": result.get("content_html", ""),
                "estimated_value": result.get("estimated_value", 0.0),
                "lead_id": lead_id,
            })

    log.append(f"Proposals: drafted {len(proposals)} proposals (saved to dashboard — not sent)")
    return {"proposals": proposals, "log": log}


def generate_contracts_node(state: ClientAcquisitionState) -> dict:
    proposals = state["proposals"]
    profile = state["business_profile"]
    business_id = state["business_id"]
    log = list(state["log"])
    bid = state["business_id"]

    contracts = []

    for proposal in proposals:
        result = _json_call(
            _llm(temperature=0.2),
            """You are a legal document specialist. Generate a professional service agreement based on the proposal.
Return JSON with:
- title (str): contract title
- content_html (str): full HTML contract with sections:
  <h2>Parties</h2>
  <h2>Services</h2>
  <h2>Term and Termination</h2>
  <h2>Payment Terms</h2>
  <h2>Intellectual Property</h2>
  <h2>Confidentiality</h2>
  <h2>Limitation of Liability</h2>
  <h2>Governing Law</h2>
  <h2>Signatures</h2> (include placeholder lines)
Return ONLY valid JSON.""",
            f"""Service Provider: {profile.get('name')}
Client: {proposal['lead_name']} at {proposal['company']}
Proposal title: {proposal['title']}
Estimated value: ${proposal.get('estimated_value', 0):,.2f}
Proposal summary:
{proposal['content_html'][:2000]}""",
            business_id=bid,
            dept_type="proposals_contracts",
        )
        if isinstance(result, dict):
            try:
                contract_id = crm_tool.save_contract(
                    business_id=business_id,
                    title=result.get("title", f"Service Agreement — {proposal['company']}"),
                    content=result.get("content_html", ""),
                    lead_id=proposal.get("lead_id"),
                )
            except Exception as e:
                log.append(f"CRM: failed to save contract ({e})")
                contract_id = None

            contracts.append({
                "lead_name": proposal["lead_name"],
                "company": proposal["company"],
                "title": result.get("title", f"Service Agreement — {proposal['company']}"),
                "content_html": result.get("content_html", ""),
                "contract_id": contract_id,
                "lead_id": proposal.get("lead_id"),
                "estimated_value": proposal.get("estimated_value", 0.0),
            })
            if contract_id:
                crm_tool.update_lead_status(proposal["lead_id"], "proposal_sent")

    log.append(f"Contracts: generated {len(contracts)} contracts (saved as draft)")
    return {"contracts": contracts, "log": log}


def generate_invoices_node(state: ClientAcquisitionState) -> dict:
    contracts = state["contracts"]
    profile = state["business_profile"]
    business_id = state["business_id"]
    log = list(state["log"])
    bid = state["business_id"]

    invoices = []

    for contract in contracts:
        amount = contract.get("estimated_value", 0.0)
        result = _json_call(
            _llm(temperature=0.2),
            """Generate a professional invoice. Return JSON with:
- title (str): invoice title
- content_html (str): full HTML invoice with:
  - Invoice number, date, due date
  - Bill To / Bill From sections
  - Line items table with description, qty, rate, amount
  - Subtotal, tax (if applicable), total
  - Payment instructions section
- amount (float): total invoice amount
Return ONLY valid JSON.""",
            f"""Service Provider: {profile.get('name')}
Client: {contract['lead_name']} at {contract['company']}
Contract: {contract['title']}
Engagement value: ${amount:,.2f}
Payment terms: Net 30
Services: {profile.get('niche', 'professional services')}""",
            business_id=bid,
            dept_type="billing",
        )
        if isinstance(result, dict):
            try:
                invoice_id = crm_tool.save_invoice(
                    business_id=business_id,
                    title=result.get("title", f"Invoice — {contract['company']}"),
                    content=result.get("content_html", ""),
                    amount=result.get("amount", amount),
                    lead_id=contract.get("lead_id"),
                    contract_id=contract.get("contract_id"),
                )
            except Exception as e:
                log.append(f"CRM: failed to save invoice ({e})")
                invoice_id = None

            invoices.append({
                "lead_name": contract["lead_name"],
                "company": contract["company"],
                "title": result.get("title", f"Invoice — {contract['company']}"),
                "content_html": result.get("content_html", ""),
                "amount": result.get("amount", amount),
                "invoice_id": invoice_id,
            })

    log.append(f"Invoices: generated {len(invoices)} invoices (saved as draft)")
    return {"invoices": invoices, "log": log}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_budget(state: ClientAcquisitionState) -> str:
    return "research_market" if state.get("active_dept_types") else END


def route_after_gate(state: ClientAcquisitionState) -> str:
    return END if state.get("approval_required") else "send_outreach"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_client_acquisition_pipeline() -> StateGraph:
    graph = StateGraph(ClientAcquisitionState)

    graph.add_node("budget_coordinator", budget_coordinator_node)
    graph.add_node("research_market", research_market_node)
    graph.add_node("find_leads", find_leads_node)
    graph.add_node("qualify_leads", qualify_leads_node)
    graph.add_node("draft_outreach", draft_outreach_node)
    graph.add_node("autonomy_gate", autonomy_gate_node)
    graph.add_node("send_outreach", send_outreach_node)
    graph.add_node("draft_proposals", draft_proposals_node)
    graph.add_node("generate_contracts", generate_contracts_node)
    graph.add_node("generate_invoices", generate_invoices_node)

    graph.set_entry_point("budget_coordinator")
    graph.add_conditional_edges("budget_coordinator", route_after_budget, {"research_market": "research_market", END: END})
    graph.add_edge("research_market", "find_leads")
    graph.add_edge("find_leads", "qualify_leads")
    graph.add_edge("qualify_leads", "draft_outreach")
    graph.add_edge("draft_outreach", "autonomy_gate")
    graph.add_conditional_edges("autonomy_gate", route_after_gate, {"send_outreach": "send_outreach", END: END})
    graph.add_edge("send_outreach", "draft_proposals")
    graph.add_edge("draft_proposals", "generate_contracts")
    graph.add_edge("generate_contracts", "generate_invoices")
    graph.add_edge("generate_invoices", END)

    return graph.compile()


def run_client_acquisition_pipeline(
    business_id: str,
    business_profile: dict,
    tool_keys: dict,
    autonomy: str,
    active_dept_types: list[str],
) -> ClientAcquisitionState:
    graph = build_client_acquisition_pipeline()
    initial: ClientAcquisitionState = {
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
        "proposals": [],
        "contracts": [],
        "invoices": [],
        "budget_state": {},
        "approval_required": False,
        "approval_action": "",
        "log": [],
        "error": None,
    }
    return graph.invoke(initial)
