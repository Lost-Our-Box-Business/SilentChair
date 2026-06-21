// Task Board API client
// Phase 2 implementation

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  created_at: string;
  completed_at?: string;
}

export async function getTasks(
  businessId: string,
  filters?: { status?: TaskStatus; department?: string }
): Promise<Task[]> {
  throw new Error("Not implemented — Phase 2");
}

export async function createTask(
  businessId: string,
  title: string,
  department?: string
): Promise<Task> {
  throw new Error("Not implemented — Phase 2");
}

export async function approveTask(taskId: string): Promise<Task> {
  throw new Error("Not implemented — Phase 2");
}

export async function getGlobalTasks(userId: string): Promise<Task[]> {
  throw new Error("Not implemented — Phase 2");
}
