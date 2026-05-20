"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Globe, ArrowRight, Clock, Loader2, CheckCircle2 } from "lucide-react";
import {
  createWebsite,
  type WebsiteFile,
} from "@/lib/website-api";
import { WebsiteBuilderChat } from "@/components/website/WebsiteBuilderChat";
import { createClient } from "@/lib/supabase/client";

type Step = "gate" | "building";

export default function OnboardingWebsitePage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const [step, setStep] = useState<Step>("gate");
  const [websiteId, setWebsiteId] = useState<string | null>(null);
  const [files, setFiles] = useState<WebsiteFile[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function goToDashboard() {
    router.push(`/dashboard/business/${businessId}`);
  }

  async function handleBuildWebsite() {
    setCreating(true);
    setError(null);
    try {
      const supabase = createClient();
      const bizResult = await supabase
        .from("businesses")
        .select("name")
        .eq("id", businessId)
        .single();
      const bizName = bizResult.data?.name ?? "";
      const created = await createWebsite(businessId, bizName);
      setWebsiteId(created.id);
      setStep("building");
    } catch {
      setError("Failed to set up your website. Please try again.");
    } finally {
      setCreating(false);
    }
  }

  if (step === "gate") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8 max-w-lg mx-auto text-center px-4">
        <div className="rounded-full bg-muted p-5">
          <Globe className="h-10 w-10 text-muted-foreground" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">Does your business have a website?</h1>
          <p className="text-sm text-muted-foreground">
            Your AI team needs a home base. We can build one for you right now using plain English
            — or you can skip this and add it later.
          </p>
        </div>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <div className="flex flex-col gap-3 w-full">
          <Button
            variant="default"
            size="lg"
            className="w-full"
            onClick={handleBuildWebsite}
            disabled={creating}
          >
            {creating ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Globe className="mr-2 h-4 w-4" />
            )}
            {creating ? "Setting up…" : "No — help me build one"}
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="w-full"
            onClick={goToDashboard}
          >
            <ArrowRight className="mr-2 h-4 w-4" />
            Yes — I already have a website
          </Button>

          <Button
            variant="ghost"
            size="lg"
            className="w-full text-muted-foreground"
            onClick={goToDashboard}
          >
            <Clock className="mr-2 h-4 w-4" />
            Skip for now — I'll do this later
          </Button>
        </div>
      </div>
    );
  }

  // Building step
  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      <div className="mb-4 shrink-0">
        <h1 className="text-lg font-semibold">Build your website</h1>
        <p className="text-sm text-muted-foreground">
          Describe what you want and your AI web developer will build it. You can always refine it later from the dashboard.
        </p>
      </div>

      <div className="flex flex-1 min-h-0 rounded-xl border overflow-hidden">
        {websiteId ? (
          <WebsiteBuilderChat
            websiteId={websiteId}
            initialFiles={[]}
            onFilesUpdate={setFiles}
          />
        ) : null}
      </div>

      <div className="mt-4 flex justify-end shrink-0">
        <Button
          onClick={goToDashboard}
          disabled={files.length === 0}
          className="gap-2"
        >
          {files.length > 0 ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <ArrowRight className="h-4 w-4" />
          )}
          {files.length > 0 ? "Finish & go to dashboard" : "Skip — go to dashboard"}
        </Button>
      </div>
    </div>
  );
}
