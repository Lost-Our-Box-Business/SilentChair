// Stripe billing API client — checkout sessions, portal, and top-up
// Phase 5 implementation

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type SubscriptionTier = "starter" | "growth" | "scale";

export async function createSubscriptionCheckout(
  tier: SubscriptionTier,
  successUrl: string,
  cancelUrl: string
): Promise<{ checkout_url: string }> {
  throw new Error("Not implemented — Phase 5");
}

export async function createTopUpCheckout(
  amountUsd: number,
  successUrl: string,
  cancelUrl: string
): Promise<{ checkout_url: string }> {
  throw new Error("Not implemented — Phase 5");
}

export async function openBillingPortal(returnUrl: string): Promise<{ portal_url: string }> {
  throw new Error("Not implemented — Phase 5");
}
