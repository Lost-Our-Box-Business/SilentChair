import { API_URL } from "./api";

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
  data: { title: string; description?: string; department?: string }
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

export async function getGlobalTasks(userId: string, businessId?: string): Promise<Task[]> {
  const params = businessId ? `?business_id=${businessId}` : "";
  const res = await fetch(`${API_URL}/api/tasks/global/${userId}${params}`);
  if (!res.ok) throw new Error("Failed to fetch global tasks");
  return res.json();
}
