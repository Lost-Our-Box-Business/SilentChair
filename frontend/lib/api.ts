export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ChatMessage = { role: "user" | "assistant"; content: string };

export async function sendInterviewMessage(params: {
  sessionId: string;
  userId: string;
  message: string;
  history: ChatMessage[];
}) {
  const res = await fetch(`${API_URL}/api/interview/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: params.sessionId,
      user_id: params.userId,
      message: params.message,
      history: params.history,
    }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json() as Promise<{
    session_id: string;
    message: string;
    is_complete: boolean;
    business_profile: Record<string, unknown> | null;
  }>;
}
