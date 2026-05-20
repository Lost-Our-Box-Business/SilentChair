import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { InterviewChat } from "@/components/interview/InterviewChat";
import { randomUUID } from "crypto";

export default async function OnboardingPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login");

  const sessionId = randomUUID();

  return (
    <div className="h-screen flex flex-col bg-background">
      <InterviewChat userId={user.id} sessionId={sessionId} />
    </div>
  );
}
