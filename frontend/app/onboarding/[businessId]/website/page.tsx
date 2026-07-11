"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Globe, ArrowRight, Clock, Loader2, CheckCircle2, Sparkles } from "lucide-react";
import {
  createWebsite,
  buildWebsite,
  type WebsiteFile,
} from "@/lib/website-api";
import { WebsiteBuilderChat } from "@/components/website/WebsiteBuilderChat";
import { createClient } from "@/lib/supabase/client";

type Step = "gate" | "building" | "done";

const BUILD_PROGRESS_MESSAGES = [
  "Analysing your business profile…",
  "Planning your site structure…",
  "Generating your design system…",
  "Building the home page…",
  "Building the about page…",
  "Building the services page…",
  "Building the contact page…",
  "Populating dynamic content…",
  "Putting the finishing touches on…",
];

export default function OnboardingWebsitePage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();

  const [step, setStep] = useState<Step>("gate");
  const [websiteId, setWebsiteId] = useState<string | null>(null);
  const [files, setFiles] = useState<WebsiteFile[]>([]);
  const [pageList, setPageList] = useState<{ slug: string; title: string }[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMsg, setProgressMsg] = useState(BUILD_PROGRESS_MESSAGES[0]);
  const progressInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const indexHtml = files.find((f) => f.path === "index.html")?.content ?? "";

  function goToDashboard() {
    router.push(`/dashboard/business/${businessId}`);
  }

  function startProgressCycle() {
    let i = 0;
    setProgressMsg(BUILD_PROGRESS_MESSAGES[0]);
    progressInterval.current = setInterval(() => {
      i = Math.min(i + 1, BUILD_PROGRESS_MESSAGES.length - 1);
      setProgressMsg(BUILD_PROGRESS_MESSAGES[i]);
    }, 7000);
  }

  function stopProgressCycle() {
    if (progressInterval.current) {
      clearInterval(progressInterval.current);
      progressInterval.current = null;
    }
  }

  useEffect(() => () => stopProgressCycle(), []);

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
      startProgressCycle();

      const result = await buildWebsite(created.id);
      stopProgressCycle();
      setFiles(result.files);
      setPageList(result.page_list);
      setStep("done");
    } catch {
      stopProgressCycle();
      setError("Something went wrong building your website. Please try again.");
      setStep("gate");
    } finally {
      setCreating(false);
    }
  }

  // ── Gate step ──────────────────────────────────────────────────────────────
  if (step === "gate") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8 max-w-lg mx-auto text-center px-4">
        <div className="rounded-full bg-muted p-5">
          <Globe className="h-10 w-10 text-muted-foreground" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">Does your business have a website?</h1>
          <p className="text-sm text-muted-foreground">
            Your AI team needs a home base. We can build a professional multi-page site right now
            — or you can skip and add it later.
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
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            {creating ? "Setting up…" : "No — build one for me"}
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

  // ── Building step ──────────────────────────────────────────────────────────
  if (step === "building") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 max-w-lg mx-auto text-center px-4">
        <div className="rounded-full bg-primary/10 p-6">
          <Sparkles className="h-12 w-12 text-primary animate-pulse" />
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-semibold">Building your website</h1>
          <p className="text-sm text-muted-foreground">
            Your AI developer is generating a full multi-page site. This takes about a minute.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
          <span>{progressMsg}</span>
        </div>
      </div>
    );
  }

  // ── Done step — split-pane preview ─────────────────────────────────────────
  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      {/* Success banner */}
      <div className="mb-3 shrink-0 flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-green-50 border border-green-200">
        <div className="flex items-center gap-2 text-sm text-green-800 font-medium">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Your {pageList.length}-page website is ready
          {pageList.length > 0 && (
            <span className="font-normal text-green-700">
              ({pageList.map((p) => p.title).join(", ")})
            </span>
          )}
        </div>
        <Button size="sm" onClick={goToDashboard} className="gap-1.5 shrink-0">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Finish & go to dashboard
        </Button>
      </div>

      {/* Split pane */}
      <div className="flex flex-1 min-h-0 rounded-xl border overflow-hidden">
        {/* Chat — 40% */}
        <div className="w-2/5 border-r flex flex-col min-h-0">
          <div className="px-3 py-2 border-b shrink-0">
            <p className="text-xs text-muted-foreground">Refine your site by chatting below</p>
          </div>
          {websiteId ? (
            <WebsiteBuilderChat
              websiteId={websiteId}
              initialFiles={files}
              onFilesUpdate={setFiles}
            />
          ) : null}
        </div>

        {/* Preview — 60% */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="px-3 py-2 border-b shrink-0 flex items-center gap-2">
            <Globe className="h-3.5 w-3.5 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">Live preview — home page</p>
          </div>
          {indexHtml ? (
            <iframe
              srcDoc={indexHtml}
              className="flex-1 w-full border-0"
              sandbox="allow-scripts"
              title="Website preview"
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">
              Preview loading…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
