import { API_URL } from "./api";

export type WebsiteFile = {
  path: string;
  content: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type WebsiteRecord = {
  id: string;
  business_id: string;
  subdomain: string;
  custom_domain: string | null;
  files: WebsiteFile[];
  chat_history: ChatMessage[];
  published_url: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function getWebsiteByBusiness(businessId: string): Promise<WebsiteRecord | null> {
  return apiFetch<WebsiteRecord | null>(`/api/website/by-business/${businessId}`);
}

export async function getWebsite(websiteId: string): Promise<WebsiteRecord> {
  return apiFetch<WebsiteRecord>(`/api/website/${websiteId}`);
}

export async function createWebsite(businessId: string, businessName?: string): Promise<{ id: string; subdomain: string }> {
  return apiFetch(`/api/website/create`, {
    method: "POST",
    body: JSON.stringify({ business_id: businessId, business_name: businessName ?? "" }),
  });
}

export async function sendWebsiteMessage(
  websiteId: string,
  message: string,
  currentFiles: WebsiteFile[],
): Promise<{ website_id: string; reply: string; files: WebsiteFile[] }> {
  return apiFetch(`/api/website/turn`, {
    method: "POST",
    body: JSON.stringify({ website_id: websiteId, message, current_files: currentFiles }),
  });
}

export async function publishWebsite(websiteId: string): Promise<{ published_url: string }> {
  return apiFetch(`/api/website/${websiteId}/publish`, { method: "POST" });
}

export async function setCustomDomain(websiteId: string, customDomain: string): Promise<void> {
  await apiFetch(`/api/website/${websiteId}/custom_domain`, {
    method: "PATCH",
    body: JSON.stringify({ custom_domain: customDomain }),
  });
}
