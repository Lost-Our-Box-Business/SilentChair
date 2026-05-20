"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { launchBusiness } from "@/lib/hiring-api";
import { Loader2, Zap, Bell, Hand, Mail, Hash, MessageCircle } from "lucide-react";

type Autonomy = "full_auto" | "major_decisions" | "step_by_step";
type CommChannel = "email" | "slack" | "discord";

const AUTONOMY_OPTIONS: { value: Autonomy; label: string; description: string; icon: React.ElementType }[] = [
  {
    value: "full_auto",
    label: "Full Auto",
    description: "Agents run independently and log everything. You review the activity feed at your own pace.",
    icon: Zap,
  },
  {
    value: "major_decisions",
    label: "Major Decisions",
    description: "Agents work autonomously but pause to ask before publishing, spending, or contacting anyone externally.",
    icon: Bell,
  },
  {
    value: "step_by_step",
    label: "Step by Step",
    description: "Agents propose each action before taking it. Maximum control, minimum surprises.",
    icon: Hand,
  },
];

const COMM_OPTIONS: { value: CommChannel; label: string; icon: React.ElementType; placeholder: string; field: string }[] = [
  { value: "email", label: "Email", icon: Mail, placeholder: "you@example.com", field: "email" },
  { value: "slack", label: "Slack", icon: Hash, placeholder: "https://hooks.slack.com/services/...", field: "webhook_url" },
  { value: "discord", label: "Discord", icon: MessageCircle, placeholder: "https://discord.com/api/webhooks/...", field: "webhook_url" },
];

export default function LaunchPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const [autonomy, setAutonomy] = useState<Autonomy>("major_decisions");
  const [commChannel, setCommChannel] = useState<CommChannel>("email");
  const [commValue, setCommValue] = useState("");
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedComm = COMM_OPTIONS.find((c) => c.value === commChannel)!;

  async function handleLaunch() {
    if (!commValue.trim()) {
      setError(`Please enter your ${selectedComm.label} ${selectedComm.field === "email" ? "address" : "webhook URL"}.`);
      return;
    }
    setLaunching(true);
    try {
      await launchBusiness({
        businessId,
        autonomy,
        commChannel,
        commConfig: { [selectedComm.field]: commValue.trim() },
      });
      router.push(`/onboarding/${businessId}/website`);
    } catch {
      setError("Failed to launch. Please try again.");
      setLaunching(false);
    }
  }

  return (
    <div className="space-y-10">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Configure and launch</h1>
        <p className="text-muted-foreground">
          Almost there. Set how autonomously your business should run and how your team should reach you.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <section className="space-y-4">
        <h2 className="text-sm font-semibold">Autonomy level</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          {AUTONOMY_OPTIONS.map(({ value, label, description, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setAutonomy(value)}
              className={`text-left rounded-xl border-2 p-4 space-y-2 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                autonomy === value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/40"
              }`}
            >
              <div className="flex items-center gap-2">
                <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${autonomy === value ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className="text-sm font-medium">{label}</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold">Communication channel</h2>
        <p className="text-xs text-muted-foreground">
          How should your team reach you when they need input or have updates?
        </p>
        <div className="flex gap-2">
          {COMM_OPTIONS.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => { setCommChannel(value); setCommValue(""); }}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                commChannel === value
                  ? "border-primary bg-primary/5 text-foreground"
                  : "border-border text-muted-foreground hover:border-primary/40"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
        </div>
        <div className="space-y-1.5 max-w-sm">
          <Label htmlFor="comm-input" className="text-xs capitalize">
            {selectedComm.field === "email" ? "Your email address" : `${selectedComm.label} webhook URL`}
          </Label>
          <Input
            id="comm-input"
            placeholder={selectedComm.placeholder}
            value={commValue}
            onChange={(e) => setCommValue(e.target.value)}
          />
        </div>
      </section>

      <div className="border-t pt-6">
        <Button
          size="lg"
          onClick={handleLaunch}
          disabled={launching}
          className="w-full sm:w-auto"
        >
          {launching && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {launching ? "Launching your business…" : "🚀 Launch my AI workforce"}
        </Button>
        <p className="text-xs text-muted-foreground mt-3">
          You can change these settings at any time from your business dashboard.
        </p>
      </div>
    </div>
  );
}
