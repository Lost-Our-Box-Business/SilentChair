import { API_URL } from "./api";

export type ToolRequirement = {
  tool_name: string;
  display_name: string;
  description: string;
  platform_available: boolean;
};

export type StaffRole = {
  role: string;
  agent_type: string;
  description: string;
  is_suggested: boolean;
};

export type DepartmentSuggestion = {
  dept_type: string;
  name: string;
  description: string;
  is_required: boolean;
  manager_title: string;
  manager_description: string;
  tools: ToolRequirement[];
  suggested_staff: StaffRole[];
};

export type ToolSetupItem = {
  tool_name: string;
  display_name: string;
  dept_type: string;
  dept_name: string;
  key_source: "platform" | "user";
  user_key?: string;
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function suggestDepartments(businessId: string, businessProfile: Record<string, unknown>) {
  return apiFetch<{ business_id: string; departments: DepartmentSuggestion[] }>("/api/departments/suggest", {
    method: "POST",
    body: JSON.stringify({ business_id: businessId, business_profile: businessProfile }),
  });
}

export async function activateDepartments(businessId: string, deptTypes: string[]) {
  return apiFetch<{ activated: number }>("/api/departments/activate", {
    method: "POST",
    body: JSON.stringify({ business_id: businessId, dept_types: deptTypes }),
  });
}

export async function getTools(businessId: string) {
  return apiFetch<Array<{ tool_name: string; key_source: string; is_active: boolean }>>(`/api/departments/tools/${businessId}`);
}

export async function setupTools(businessId: string, tools: ToolSetupItem[]) {
  return apiFetch<{ configured: number }>("/api/departments/tools/setup", {
    method: "POST",
    body: JSON.stringify({ business_id: businessId, tools }),
  });
}

export async function getStaffSuggestions(deptType: string) {
  return apiFetch<StaffRole[]>(`/api/departments/staff-suggestions/${deptType}`);
}

export async function hireStaff(businessId: string, departmentId: string, roles: string[]) {
  return apiFetch<{ hired: string[] }>("/api/departments/staff/hire", {
    method: "POST",
    body: JSON.stringify({ business_id: businessId, department_id: departmentId, roles }),
  });
}

export async function launchBusiness(params: {
  businessId: string;
  autonomy: "full_auto" | "major_decisions" | "step_by_step";
  commChannel: "email" | "slack" | "discord" | "sms";
  commConfig: Record<string, string>;
}) {
  return apiFetch<{ status: string }>("/api/departments/launch", {
    method: "POST",
    body: JSON.stringify({
      business_id: params.businessId,
      autonomy: params.autonomy,
      comm_channel: params.commChannel,
      comm_config: params.commConfig,
    }),
  });
}
