import { API_URL } from "./api";

export interface BusinessContext {
  summary: string;
  products_services: string[];
  target_customers: string;
  brand_voice: string;
  current_goals: string[];
  competitive_context: string;
  financials: Record<string, unknown>;
  active_campaigns: string[];
  key_decisions: string[];
  last_updated: string | null;
}

export async function getBusinessContext(businessId: string, locale = "en"): Promise<BusinessContext> {
  const url = locale && locale !== "en"
    ? `${API_URL}/api/business/${businessId}/context?locale=${locale}`
    : `${API_URL}/api/business/${businessId}/context`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch business context");
  return res.json();
}

export async function correctBusinessContext(
  businessId: string,
  message: string
): Promise<BusinessContext> {
  const res = await fetch(`${API_URL}/api/business/${businessId}/context/correct`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to update business context");
  return res.json();
}
