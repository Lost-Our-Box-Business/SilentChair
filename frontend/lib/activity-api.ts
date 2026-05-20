import { API_URL } from "./api";

export type OutreachEmail = {
  to_name: string;
  to_email: string;
  subject: string;
  body_html: string;
  preview_text: string;
  lead_data: Record<string, unknown>;
};

export type ActivityDetail = {
  outreach_emails?: OutreachEmail[];
  edited_articles?: Array<{ title: string; content: string; meta_description: string; slug: string }>;
  qualified_leads?: Record<string, unknown>[];
  market_research?: Record<string, unknown>;
};

export type ActivityEntry = {
  id: string;
  business_id: string;
  agent_id: string | null;
  action_type: string;
  summary: string;
  requires_approval: boolean;
  approved_at: string | null;
  detail: ActivityDetail;
  created_at: string;
};

export type PipelineRunResult = {
  status: "complete" | "awaiting_approval";
  approval_action: string | null;
  published_urls: string[];
  social_posts: Array<{ platform: string; text: string; article_title: string }>;
  qualified_leads?: Record<string, unknown>[];
  contracts?: Record<string, unknown>[];
  invoices?: Record<string, unknown>[];
  log: string[];
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function getActivityFeed(businessId: string, limit = 50): Promise<ActivityEntry[]> {
  return apiFetch<ActivityEntry[]>(`/api/activity/${businessId}?limit=${limit}`);
}

export async function approveActivity(activityId: string): Promise<ActivityEntry> {
  return apiFetch<ActivityEntry>(`/api/activity/${activityId}/approve`, { method: "POST" });
}

export async function runPipeline(businessId: string): Promise<PipelineRunResult> {
  return apiFetch<PipelineRunResult>(`/api/pipeline/run/${businessId}`, { method: "POST" });
}

// ── CRM ──────────────────────────────────────────────────────────────────────

export type Lead = {
  id: string;
  business_id: string;
  name: string;
  company: string;
  email: string;
  title?: string;
  source: string;
  status: "new" | "contacted" | "qualified" | "proposal_sent" | "won" | "lost";
  score: number | null;
  notes: string;
  created_at: string;
};

export type Contract = {
  id: string;
  business_id: string;
  lead_id: string | null;
  title: string;
  content: string;
  status: "draft" | "sent" | "signed";
  created_at: string;
};

export type Invoice = {
  id: string;
  business_id: string;
  lead_id: string | null;
  contract_id: string | null;
  title: string;
  content: string;
  amount: number;
  status: "draft" | "sent" | "paid";
  created_at: string;
};

export async function getLeads(businessId: string): Promise<Lead[]> {
  return apiFetch<Lead[]>(`/api/crm/leads/${businessId}`);
}

export async function getContracts(businessId: string): Promise<Contract[]> {
  return apiFetch<Contract[]>(`/api/crm/contracts/${businessId}`);
}

export async function getInvoices(businessId: string): Promise<Invoice[]> {
  return apiFetch<Invoice[]>(`/api/crm/invoices/${businessId}`);
}

export async function updateLeadStatus(leadId: string, status: Lead["status"]): Promise<Lead> {
  return apiFetch<Lead>(`/api/crm/leads/${leadId}/status?status=${status}`, { method: "PATCH" });
}

export async function updateContractStatus(contractId: string, status: Contract["status"]): Promise<Contract> {
  return apiFetch<Contract>(`/api/crm/contracts/${contractId}/status?status=${status}`, { method: "PATCH" });
}

export async function updateInvoiceStatus(invoiceId: string, status: Invoice["status"]): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/crm/invoices/${invoiceId}/status?status=${status}`, { method: "PATCH" });
}
