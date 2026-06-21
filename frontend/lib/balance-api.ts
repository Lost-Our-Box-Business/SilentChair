// Dollar balance and spend ledger API client
// Phase 4 implementation

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface UserBalance {
  user_id: string;
  balance_usd: number;
  monthly_grant_usd: number;
  subscription_tier: string;
  stripe_customer_id?: string;
  trial_ends_at?: string;
}

export interface SpendEntry {
  id: string;
  user_id: string;
  business_id?: string;
  task_id?: string;
  amount_usd: number;
  type: "subscription_grant" | "top_up" | "debit" | "refund";
  description?: string;
  balance_after?: number;
  created_at: string;
}

export async function getBalance(): Promise<UserBalance> {
  throw new Error("Not implemented — Phase 4");
}

export async function getLedger(businessId?: string): Promise<SpendEntry[]> {
  throw new Error("Not implemented — Phase 4");
}
