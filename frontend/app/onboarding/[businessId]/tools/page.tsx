"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { getTools, setupTools, type ToolSetupItem } from "@/lib/hiring-api";
import { createClient } from "@/lib/supabase/client";
import { ArrowRight, Loader2, ShieldCheck, Key } from "lucide-react";

type ToolState = ToolSetupItem & { platform_available: boolean };

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  anthropic: "Anthropic Claude",
  serper: "Serper (Google Search)",
  buffer: "Buffer",
  wordpress: "WordPress",
  beehiiv: "Beehiiv",
  resend: "Resend Email",
};

const PLATFORM_AVAILABLE: Record<string, boolean> = {
  anthropic: true,
  serper: true,
  buffer: true,
  wordpress: false,
  beehiiv: false,
  resend: true,
};

const TOOL_TO_DEPT: Record<string, string> = {
  anthropic: "editorial",
  serper: "seo",
  buffer: "social_media",
  wordpress: "distribution",
  beehiiv: "distribution",
  resend: "outreach",
};

const TOOL_DESCRIPTIONS: Record<string, string> = {
  anthropic: "Powers all AI writing, research, and decision-making across your agents.",
  serper: "Gives agents real-time access to Google Search results for research.",
  buffer: "Schedules and publishes posts to Instagram, X, LinkedIn, and Facebook.",
  wordpress: "Publishes formatted articles directly to your WordPress site.",
  beehiiv: "Sends newsletters to your subscriber list via Beehiiv.",
  resend: "Sends outreach and follow-up emails to leads and prospects.",
};

export default function ToolsPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const [tools, setTools] = useState<ToolState[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const supabase = createClient();
        const [dbTools, deptsResult] = await Promise.all([
          getTools(businessId),
          supabase
            .from("departments")
            .select("dept_type, name")
            .eq("business_id", businessId)
            .eq("is_active", true),
        ]);

        const deptNameMap: Record<string, string> = {};
        for (const d of deptsResult.data ?? []) {
          deptNameMap[d.dept_type] = d.name;
        }

        const seen = new Set<string>();
        const toolList: ToolState[] = [];
        for (const t of dbTools) {
          if (seen.has(t.tool_name)) continue;
          seen.add(t.tool_name);
          const deptType = TOOL_TO_DEPT[t.tool_name] ?? "";
          toolList.push({
            tool_name: t.tool_name,
            display_name: TOOL_DISPLAY_NAMES[t.tool_name] ?? t.tool_name,
            dept_type: deptType,
            dept_name: deptNameMap[deptType] ?? deptType,
            key_source: t.key_source as "platform" | "user",
            platform_available: PLATFORM_AVAILABLE[t.tool_name] ?? false,
          });
        }
        setTools(toolList);
      } catch {
        setError("Failed to load tools.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [businessId]);

  function setKeySource(toolName: string, source: "platform" | "user") {
    setTools((prev) => prev.map((t) => t.tool_name === toolName ? { ...t, key_source: source } : t));
  }

  function setUserKey(toolName: string, key: string) {
    setTools((prev) => prev.map((t) => t.tool_name === toolName ? { ...t, user_key: key } : t));
  }

  async function handleContinue() {
    const missing = tools.filter((t) => t.key_source === "user" && !t.user_key?.trim());
    if (missing.length > 0) {
      setError(`Please enter API keys for: ${missing.map((t) => t.display_name).join(", ")}`);
      return;
    }
    setSaving(true);
    try {
      await setupTools(businessId, tools);
      router.push(`/onboarding/${businessId}/staff`);
    } catch {
      setError("Failed to save tool configuration.");
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-4 w-96" />
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
      </div>
    );
  }

  const platformTools = tools.filter((t) => t.key_source === "platform");
  const userKeyTools = tools.filter((t) => t.key_source === "user");

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Set up your tools</h1>
        <p className="text-muted-foreground">
          Your managers need access to a few tools. For most, SilentChair provides access and
          bills you for usage. For platform-specific tools you may want to use your own accounts.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="space-y-3">
        {tools.map((tool) => (
          <div key={tool.tool_name} className="rounded-xl border p-5 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm">{tool.display_name}</h3>
                  <Badge variant="outline" className="text-[10px]">{tool.dept_name}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {TOOL_DESCRIPTIONS[tool.tool_name] ?? "Required for agent operations."}
                </p>
              </div>
            </div>

            {tool.platform_available ? (
              <div className="flex gap-2">
                <button
                  onClick={() => setKeySource(tool.tool_name, "platform")}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-all ${
                    tool.key_source === "platform"
                      ? "border-primary bg-primary/5 text-foreground"
                      : "border-border text-muted-foreground hover:border-primary/40"
                  }`}
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  SilentChair provides access
                </button>
                <button
                  onClick={() => setKeySource(tool.tool_name, "user")}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-all ${
                    tool.key_source === "user"
                      ? "border-primary bg-primary/5 text-foreground"
                      : "border-border text-muted-foreground hover:border-primary/40"
                  }`}
                >
                  <Key className="h-3.5 w-3.5" />
                  Use my own key
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
                <Key className="h-3.5 w-3.5 shrink-0" />
                Your own account required — SilentChair cannot provide this integration.
              </div>
            )}

            {(tool.key_source === "user" || !tool.platform_available) && (
              <div className="space-y-1.5">
                <Label htmlFor={tool.tool_name} className="text-xs">
                  {tool.display_name} API Key
                </Label>
                <Input
                  id={tool.tool_name}
                  type="password"
                  placeholder="sk-..."
                  value={tool.user_key ?? ""}
                  onChange={(e) => setUserKey(tool.tool_name, e.target.value)}
                  className="font-mono text-xs"
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2">
        <p className="text-xs text-muted-foreground">
          {platformTools.length} via SilentChair · {userKeyTools.length} via your own keys
        </p>
        <Button onClick={handleContinue} disabled={saving}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {saving ? "Saving…" : "Continue to staff"}
          {!saving && <ArrowRight className="ml-2 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
