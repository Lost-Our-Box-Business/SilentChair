import { API_URL } from "./api";

export type BudgetState = {
  daily_budget: number | null;
  dept_budgets: Record<string, number>;
  today_spend: number;
  today_by_dept: Record<string, number>;
  daily_remaining: number | null;
  dept_remaining: Record<string, number>;
};

export type DailyUsage = {
  date: string;
  total: number;
  by_dept: Record<string, number>;
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function getBudgetState(businessId: string): Promise<BudgetState> {
  return apiFetch(`/api/usage/${businessId}`);
}

export async function getUsageHistory(businessId: string, days = 30): Promise<DailyUsage[]> {
  return apiFetch(`/api/usage/${businessId}/history?days=${days}`);
}

export async function updateBudget(
  businessId: string,
  params: { daily_budget?: number | null; dept_budgets?: Record<string, number | null> },
): Promise<{ updated: boolean }> {
  return apiFetch(`/api/usage/${businessId}/budget`, {
    method: "PATCH",
    body: JSON.stringify(params),
  });
}
