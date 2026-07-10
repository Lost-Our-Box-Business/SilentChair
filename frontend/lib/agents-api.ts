import { API_URL } from "./api";

export type ScheduleConfig =
  | { type: "interval"; hours: number }
  | { type: "daily"; hour: number }
  | { type: "weekdays"; hour: number }
  | null;

export interface DepartmentStatus {
  dept_type: string;
  name: string;
  is_active: boolean;
  is_paused: boolean;
  label_color: string;
  last_run_at: string | null;
  last_run_status: string | null;
  manager_next_eval_at: string | null;
  status_narrative: string;
  today_cost_usd: number;
  schedule_config: ScheduleConfig;
}

export interface DepartmentDetail extends DepartmentStatus {
  id: string;
  description: string | null;
  is_required: boolean;
  manager_chat_history: { role: "user" | "assistant"; content: string }[];
}

export interface ApprovalQueueItem {
  id: string;
  business_id: string;
  dept_type: string;
  action_type: string;
  payload: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  resolved_at: string | null;
}

export async function getAgents(businessId: string): Promise<DepartmentStatus[]> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}`);
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function startAgents(businessId: string, locale = "en"): Promise<void> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}/start?locale=${locale}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start agents");
}

export async function pauseAgents(businessId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}/pause`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to pause agents");
}

export async function resumeAgents(businessId: string, locale = "en"): Promise<void> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}/resume?locale=${locale}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to resume agents");
}

export async function getApprovalQueue(businessId: string): Promise<ApprovalQueueItem[]> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}/queue`);
  if (!res.ok) throw new Error("Failed to fetch approval queue");
  return res.json();
}

export async function approveQueueItem(businessId: string, queueId: string, userId: string): Promise<ApprovalQueueItem> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}/queue/${queueId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error("Failed to approve item");
  return res.json();
}

export async function rejectQueueItem(businessId: string, queueId: string, userId: string, reason = ""): Promise<ApprovalQueueItem> {
  const res = await fetch(`${API_URL}/api/agents/${businessId}/queue/${queueId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, reason }),
  });
  if (!res.ok) throw new Error("Failed to reject item");
  return res.json();
}

export async function setDeptSchedule(businessId: string, deptType: string, scheduleConfig: ScheduleConfig): Promise<void> {
  const res = await fetch(`${API_URL}/api/departments/${businessId}/${deptType}/schedule`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schedule_config: scheduleConfig }),
  });
  if (!res.ok) throw new Error(`Failed to save schedule: ${await res.text()}`);
}

export async function getDepartment(businessId: string, deptType: string): Promise<DepartmentDetail> {
  const res = await fetch(`${API_URL}/api/departments/${businessId}/${deptType}`);
  if (!res.ok) throw new Error("Failed to fetch department");
  return res.json();
}

export async function chatWithManager(businessId: string, deptType: string, message: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/departments/${businessId}/${deptType}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to send message");
  const data = await res.json();
  return data.reply as string;
}

export async function getDeptApprovalQueue(businessId: string, deptType: string): Promise<ApprovalQueueItem[]> {
  const res = await fetch(`${API_URL}/api/departments/${businessId}/${deptType}/queue`);
  if (!res.ok) throw new Error("Failed to fetch dept queue");
  return res.json();
}

export async function approveDeptQueueItem(businessId: string, deptType: string, queueId: string, userId: string): Promise<ApprovalQueueItem> {
  const res = await fetch(`${API_URL}/api/departments/${businessId}/${deptType}/queue/${queueId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error("Failed to approve item");
  return res.json();
}

export async function rejectDeptQueueItem(businessId: string, deptType: string, queueId: string, userId: string, reason = ""): Promise<ApprovalQueueItem> {
  const res = await fetch(`${API_URL}/api/departments/${businessId}/${deptType}/queue/${queueId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, reason }),
  });
  if (!res.ok) throw new Error("Failed to reject item");
  return res.json();
}
