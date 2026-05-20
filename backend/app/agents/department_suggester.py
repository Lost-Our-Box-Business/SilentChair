"""
Department Suggester — maps a business profile to an archetype, then returns
tailored department suggestions for that archetype.

Archetypes: content_agency | lead_generation | client_acquisition
"""
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.departments import DepartmentSuggestion, ToolRequirement, StaffRole


# ── Department catalogs ───────────────────────────────────────────────────────

CONTENT_AGENCY_DEPARTMENTS: list[DepartmentSuggestion] = [
    DepartmentSuggestion(
        dept_type="editorial",
        name="Editorial",
        description="Plans the content calendar, commissions pieces, and manages the overall editorial voice.",
        is_required=True,
        manager_title="Content Director",
        manager_description="An expert editor who understands your brand voice, audience, and content strategy.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Writing, editing, and content generation.", platform_available=True),
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Topic research and competitor content analysis.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Content Writer", agent_type="content_writer", description="Writes long-form articles and guides based on the content calendar."),
            StaffRole(role="Copy Editor", agent_type="copy_editor", description="Proofreads and polishes all content before publication."),
            StaffRole(role="Content Scheduler", agent_type="content_scheduler", description="Manages the editorial calendar and queues content for publication."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="seo",
        name="SEO",
        description="Drives organic traffic through keyword strategy, on-page optimization, and performance tracking.",
        is_required=True,
        manager_title="SEO Strategist",
        manager_description="A data-driven SEO expert who identifies high-value keywords and tracks ranking performance.",
        tools=[
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Keyword research and SERP analysis.", platform_available=True),
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Content optimization and meta description writing.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Keyword Researcher", agent_type="keyword_researcher", description="Identifies keyword opportunities and tracks ranking positions."),
            StaffRole(role="On-Page Optimizer", agent_type="on_page_optimizer", description="Optimizes titles, meta descriptions, headers, and internal links."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="social_media",
        name="Social Media",
        description="Grows and engages your audience across social platforms by repurposing content and posting consistently.",
        is_required=False,
        manager_title="Social Media Manager",
        manager_description="A social-native strategist who adapts content for each platform and builds a following.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Caption writing and social copy.", platform_available=True),
            ToolRequirement(tool_name="buffer", display_name="Buffer", description="Social media scheduling and publishing.", platform_available=True),
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Trending topic research.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Post Composer", agent_type="post_composer", description="Writes and formats posts for each social platform."),
            StaffRole(role="Community Manager", agent_type="community_manager", description="Monitors and responds to comments and mentions."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="distribution",
        name="Distribution",
        description="Gets your content in front of the right audience via newsletters, syndication, and publishing platforms.",
        is_required=False,
        manager_title="Distribution Manager",
        manager_description="A growth-focused operator who maximizes content reach through newsletters and syndication.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Newsletter writing and content adaptation.", platform_available=True),
            ToolRequirement(tool_name="wordpress", display_name="WordPress REST API", description="Publishing blog posts to WordPress sites.", platform_available=False),
        ],
        suggested_staff=[
            StaffRole(role="Newsletter Writer", agent_type="newsletter_writer", description="Writes and sends the weekly/monthly newsletter."),
            StaffRole(role="Blog Publisher", agent_type="blog_publisher", description="Publishes formatted articles to your blog platform."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="analytics",
        name="Analytics",
        description="Tracks what's working, what isn't, and surfaces insights to improve content strategy.",
        is_required=False,
        manager_title="Analytics Director",
        manager_description="A metrics-obsessed analyst who turns data into actionable content strategy insights.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Insight summarization and report writing.", platform_available=True),
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Competitor benchmarking.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Performance Tracker", agent_type="performance_tracker", description="Monitors traffic, engagement, and conversion metrics."),
            StaffRole(role="Report Generator", agent_type="report_generator", description="Produces weekly and monthly performance reports."),
        ],
    ),
]


LEAD_GEN_DEPARTMENTS: list[DepartmentSuggestion] = [
    DepartmentSuggestion(
        dept_type="market_research",
        name="Market Research",
        description="Defines your ideal client profile, maps target markets, and identifies high-value segments.",
        is_required=True,
        manager_title="Market Research Lead",
        manager_description="An analyst who continuously refines your ICP and identifies untapped market segments.",
        tools=[
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Market intelligence and competitor research.", platform_available=True),
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="ICP analysis and market synthesis.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="ICP Analyst", agent_type="icp_analyst", description="Defines and refines the ideal client profile based on market data."),
            StaffRole(role="Competitor Researcher", agent_type="competitor_researcher", description="Tracks what competitors are doing to win clients."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="lead_research",
        name="Lead Research",
        description="Finds and compiles lists of prospects that match the ICP, sourcing contact information.",
        is_required=True,
        manager_title="Lead Research Manager",
        manager_description="A specialist in finding decision-makers at the right companies and building qualified prospect lists.",
        tools=[
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Company and contact discovery.", platform_available=True),
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Lead qualification and list building.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Prospect Hunter", agent_type="prospect_hunter", description="Finds companies and contacts matching the ICP."),
            StaffRole(role="Data Enricher", agent_type="data_enricher", description="Fills in missing contact details and company information."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="lead_qualification",
        name="Lead Qualification",
        description="Scores and filters leads against ICP criteria to ensure the sales team focuses on the best opportunities.",
        is_required=True,
        manager_title="Qualification Specialist",
        manager_description="An expert at separating high-value prospects from noise using structured scoring frameworks.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="AI-powered lead scoring and qualification.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Lead Scorer", agent_type="lead_scorer", description="Applies qualification criteria and scores each incoming lead."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="outreach",
        name="Outreach",
        description="Writes and sends personalized cold emails to qualified prospects, managing sequences and follow-ups.",
        is_required=True,
        manager_title="Outreach Manager",
        manager_description="A cold email specialist who writes compelling sequences that get replies without being spammy.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Email copywriting and personalization.", platform_available=True),
            ToolRequirement(tool_name="resend", display_name="Resend (Email)", description="Sending outreach emails.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Email Copywriter", agent_type="email_copywriter", description="Writes personalized outreach emails for each lead."),
            StaffRole(role="Follow-up Specialist", agent_type="followup_specialist", description="Manages follow-up sequences for non-responders."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="analytics",
        name="Analytics",
        description="Tracks open rates, reply rates, and conversion metrics to optimize the lead generation funnel.",
        is_required=False,
        manager_title="Analytics Manager",
        manager_description="A data analyst who uses funnel metrics to improve lead quality and outreach performance.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Report generation and insight analysis.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Funnel Analyst", agent_type="funnel_analyst", description="Tracks lead-to-meeting conversion rates and identifies drop-off points."),
        ],
    ),
]


CLIENT_ACQUISITION_DEPARTMENTS: list[DepartmentSuggestion] = [
    DepartmentSuggestion(
        dept_type="market_research",
        name="Market Research",
        description="Identifies target markets, ideal client profiles, and high-value segments for acquisition.",
        is_required=True,
        manager_title="Market Research Director",
        manager_description="Defines who your ideal clients are and where to find them at scale.",
        tools=[
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Market and competitor intelligence.", platform_available=True),
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="ICP definition and market analysis.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="ICP Analyst", agent_type="icp_analyst", description="Builds and refines the ideal client profile."),
            StaffRole(role="Market Mapper", agent_type="market_mapper", description="Maps addressable market segments and prioritizes targets."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="lead_generation",
        name="Lead Generation",
        description="Finds, qualifies, and enriches prospect lists from your target markets.",
        is_required=True,
        manager_title="Lead Generation Manager",
        manager_description="Fills the top of the funnel with qualified prospects ready for outreach.",
        tools=[
            ToolRequirement(tool_name="serper", display_name="Serper (Google Search)", description="Prospect discovery.", platform_available=True),
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Lead scoring and qualification.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Prospect Researcher", agent_type="prospect_researcher", description="Finds companies and contacts matching the ICP."),
            StaffRole(role="Lead Qualifier", agent_type="lead_qualifier", description="Scores leads and prioritizes outreach targets."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="sales_outreach",
        name="Sales Outreach",
        description="Manages personalized cold outreach sequences and follow-ups to book discovery calls.",
        is_required=True,
        manager_title="Sales Outreach Manager",
        manager_description="A sales specialist who turns cold prospects into booked calls through strategic messaging.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Personalized email and message writing.", platform_available=True),
            ToolRequirement(tool_name="resend", display_name="Resend (Email)", description="Outreach email delivery.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="SDR Agent", agent_type="sdr_agent", description="Sends initial outreach and manages multi-touch sequences."),
            StaffRole(role="Follow-up Manager", agent_type="followup_manager", description="Handles follow-up emails for prospects who haven't responded."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="proposals_contracts",
        name="Proposals & Contracts",
        description="Creates tailored proposals and service agreements for interested prospects.",
        is_required=True,
        manager_title="Proposals Director",
        manager_description="Converts interest into signed agreements with persuasive proposals and airtight contracts.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Proposal writing, contract drafting, document generation.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Proposal Writer", agent_type="proposal_writer", description="Creates tailored proposals for each qualified prospect."),
            StaffRole(role="Contract Specialist", agent_type="contract_specialist", description="Drafts service agreements based on approved proposals."),
        ],
    ),
    DepartmentSuggestion(
        dept_type="billing",
        name="Billing",
        description="Generates invoices for won deals and tracks payment status.",
        is_required=False,
        manager_title="Billing Manager",
        manager_description="Ensures every won deal is invoiced promptly and accurately.",
        tools=[
            ToolRequirement(tool_name="anthropic", display_name="Claude AI", description="Invoice generation and document formatting.", platform_available=True),
        ],
        suggested_staff=[
            StaffRole(role="Invoice Generator", agent_type="invoice_generator", description="Creates professional invoices from signed contracts."),
        ],
    ),
]

ARCHETYPE_DEPARTMENTS: dict[str, list[DepartmentSuggestion]] = {
    "content_agency": CONTENT_AGENCY_DEPARTMENTS,
    "lead_generation": LEAD_GEN_DEPARTMENTS,
    "client_acquisition": CLIENT_ACQUISITION_DEPARTMENTS,
}


# ── Archetype detection ───────────────────────────────────────────────────────

def detect_archetype(business_profile: dict) -> str:
    """Use a fast LLM call to classify the business into one of three archetypes."""
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0.0,
        max_tokens=20,
    )
    response = llm.invoke([
        SystemMessage(content="""Classify this business into exactly one archetype. Return ONLY the archetype string, nothing else.
Archetypes:
- content_agency: creates and publishes content (blogs, articles, social media, newsletters)
- lead_generation: finds and contacts potential customers on behalf of a business
- client_acquisition: full sales cycle from research through proposals, contracts, and invoicing"""),
        HumanMessage(content=f"Business profile: {json.dumps(business_profile)}"),
    ])
    raw = response.content.strip().lower()
    for archetype in ("content_agency", "lead_generation", "client_acquisition"):
        if archetype in raw:
            return archetype
    return "content_agency"


# ── Description tailoring ─────────────────────────────────────────────────────

TAILORING_SYSTEM_PROMPT = """You are helping customize department descriptions for a specific business.
Given a business profile and a list of departments, return a JSON array where each item has:
- "dept_type": the original dept_type (unchanged)
- "description": a 1-sentence description tailored to this specific business
- "manager_description": a 1-2 sentence description of the manager tailored to this business
Keep descriptions concise and specific. Return ONLY valid JSON, no other text."""


def _tailor_descriptions(business_profile: dict, departments: list[DepartmentSuggestion]) -> list[DepartmentSuggestion]:
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=1024,
    )
    dept_list = [{"dept_type": d.dept_type, "name": d.name} for d in departments]
    prompt = f"Business profile: {json.dumps(business_profile)}\n\nDepartments: {json.dumps(dept_list)}"
    try:
        response = llm.invoke([
            SystemMessage(content=TAILORING_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        tailored = json.loads(raw.strip())
        tailored_map = {t["dept_type"]: t for t in tailored}
        return [
            dept.model_copy(update={
                "description": tailored_map[dept.dept_type].get("description", dept.description),
                "manager_description": tailored_map[dept.dept_type].get("manager_description", dept.manager_description),
            }) if dept.dept_type in tailored_map else dept
            for dept in departments
        ]
    except Exception:
        return departments


# ── Public entry point ────────────────────────────────────────────────────────

def suggest_departments(business_profile: dict) -> tuple[str, list[DepartmentSuggestion]]:
    """
    Detect the archetype and return (archetype, tailored departments).
    The caller is responsible for persisting the archetype on the business row.
    """
    archetype = detect_archetype(business_profile)
    departments = ARCHETYPE_DEPARTMENTS.get(archetype, CONTENT_AGENCY_DEPARTMENTS)
    tailored = _tailor_descriptions(business_profile, departments)
    return archetype, tailored
