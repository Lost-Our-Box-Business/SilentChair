import { API_URL } from "./api";
import { createClient } from "@/lib/supabase/client";

const DEPT_LABELS: Record<string, string> = {
  editorial: "Editorial",
  seo: "SEO",
  social_media: "Social Media",
  distribution: "Distribution",
  analytics: "Analytics",
  market_research: "Market Research",
  lead_research: "Lead Research",
  lead_qualification: "Lead Qualification",
  outreach: "Outreach",
  lead_generation: "Lead Generation",
  sales_outreach: "Sales Outreach",
  proposals_contracts: "Proposals & Contracts",
  billing: "Billing",
};

export async function getBusinessDepartments(businessId: string): Promise<string[]> {
  const supabase = createClient();
  const { data } = await supabase
    .from("departments")
    .select("dept_type")
    .eq("business_id", businessId)
    .eq("is_active", true);
  return (data ?? []).map((d: { dept_type: string }) => DEPT_LABELS[d.dept_type] ?? d.dept_type);
}

export type TaskStatus = "planned" | "in_progress" | "awaiting_approval" | "completed" | "failed";

export interface Task {
  id: string;
  business_id: string;
  agent_id?: string;
  title: string;
  description?: string;
  status: TaskStatus;
  output?: string;
  output_meta?: Record<string, unknown>;
  department?: string;
  cost_usd: number;
  label_color?: string;
  created_by: "agent" | "user";
  assigned_to: "agent" | "user";
  approved_by?: string;
  activity_log_id?: string;
  created_at: string;
  completed_at?: string;
  businesses?: { name: string };
}

export async function getTasks(
  businessId: string,
  filters?: { status?: TaskStatus; department?: string }
): Promise<Task[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.department) params.set("department", filters.department);
  const qs = params.toString() ? `?${params}` : "";
  const res = await fetch(`${API_URL}/api/tasks/${businessId}${qs}`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function createTask(
  businessId: string,
  data: { title: string; description?: string; department?: string; assigned_to?: "agent" | "user" }
): Promise<Task> {
  const res = await fetch(`${API_URL}/api/tasks/${businessId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create task");
  return res.json();
}

export async function approveTask(taskId: string): Promise<Task> {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/approve`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to approve task");
  return res.json();
}

export async function updateTask(
  taskId: string,
  data: { title?: string; description?: string; department?: string }
): Promise<Task> {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update task");
  return res.json();
}

export async function rejectTask(taskId: string, reason: string): Promise<Task> {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) throw new Error("Failed to reject task");
  return res.json();
}

export async function deleteTask(taskId: string): Promise<void> {
  await fetch(`${API_URL}/api/tasks/${taskId}`, { method: "DELETE" });
}

export async function runTask(taskId: string, locale?: string): Promise<Record<string, unknown>> {
  const qs = locale ? `?locale=${locale}` : "";
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/run${qs}`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Pipeline error" }));
    throw new Error(err.detail ?? "Pipeline error");
  }
  return res.json();
}

export async function setTaskStatus(taskId: string, status: TaskStatus): Promise<Task> {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Failed to update task status");
  return res.json();
}

export async function getApprovalContent(
  taskId: string
): Promise<{ action_type: string; payload: Record<string, unknown> }> {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/approval-content`);
  if (!res.ok) throw new Error("Failed to fetch approval content");
  return res.json();
}

export async function getGlobalTasks(userId: string, businessId?: string): Promise<Task[]> {
  const params = businessId ? `?business_id=${businessId}` : "";
  const res = await fetch(`${API_URL}/api/tasks/global/${userId}${params}`);
  if (!res.ok) throw new Error("Failed to fetch global tasks");
  return res.json();
}
