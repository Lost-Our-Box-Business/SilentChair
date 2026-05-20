"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Globe,
  Upload,
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ChevronRight,
} from "lucide-react";
import {
  getWebsiteByBusiness,
  createWebsite,
  publishWebsite,
  setCustomDomain,
  type WebsiteFile,
  type WebsiteRecord,
} from "@/lib/website-api";
import { WebsiteBuilderChat } from "@/components/website/WebsiteBuilderChat";
import { createClient } from "@/lib/supabase/client";

export default function WebsitePage() {
  const { businessId } = useParams<{ businessId: string }>();
  const [website, setWebsite] = useState<WebsiteRecord | null>(null);
  const [files, setFiles] = useState<WebsiteFile[]>([]);
  const [activeFile, setActiveFile] = useState<string>("index.html");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [published, setPublished] = useState(false);
  const [publishedUrl, setPublishedUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [domainInput, setDomainInput] = useState("");
  const [savingDomain, setSavingDomain] = useState(false);
  const [domainSaved, setDomainSaved] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const record = await getWebsiteByBusiness(businessId);
      if (record) {
        setWebsite(record);
        setFiles(record.files);
        setPublishedUrl(record.published_url);
        if (record.custom_domain) setDomainInput(record.custom_domain);
      }
    } catch {
      setError("Failed to load website data.");
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate() {
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
      await load();
    } catch {
      setError("Failed to create website. Please try again.");
    } finally {
      setCreating(false);
    }
  }

  async function handlePublish() {
    if (!website) return;
    setPublishing(true);
    setError(null);
    try {
      const result = await publishWebsite(website.id);
      setPublishedUrl(result.published_url);
      setPublished(true);
      setTimeout(() => setPublished(false), 4000);
    } catch {
      setError("Failed to publish. Please try again.");
    } finally {
      setPublishing(false);
    }
  }

  async function handleSaveDomain() {
    if (!website || !domainInput.trim()) return;
    setSavingDomain(true);
    try {
      await setCustomDomain(website.id, domainInput.trim());
      setDomainSaved(true);
      setTimeout(() => setDomainSaved(false), 3000);
    } catch {
      setError("Failed to save custom domain.");
    } finally {
      setSavingDomain(false);
    }
  }

  const indexHtml = files.find((f) => f.path === "index.html")?.content ?? "";
  const activeContent = files.find((f) => f.path === activeFile)?.content ?? "";

  if (loading) {
    return (
      <div className="h-[calc(100vh-4rem)] space-y-4 p-4">
        <Skeleton className="h-7 w-48" />
        <div className="flex gap-4 h-full">
          <Skeleton className="w-2/5 rounded-xl" />
          <Skeleton className="flex-1 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!website) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)] gap-6 max-w-md mx-auto text-center">
        <div className="rounded-full bg-muted p-4">
          <Globe className="h-8 w-8 text-muted-foreground" />
        </div>
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">No website yet</h2>
          <p className="text-sm text-muted-foreground">
            Build a website for your business using AI. Describe what you want and we'll create it.
          </p>
        </div>
        {error && (
          <p className="flex items-center gap-1.5 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" /> {error}
          </p>
        )}
        <Button onClick={handleCreate} disabled={creating}>
          {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {creating ? "Setting up…" : "Start building"}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b shrink-0 flex-wrap gap-y-2">
        <div className="flex items-center gap-2 mr-auto">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{website.subdomain}.silentchair.app</span>
          {publishedUrl && (
            <a
              href={publishedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary flex items-center gap-1 hover:underline"
            >
              <ExternalLink className="h-3 w-3" /> Live
            </a>
          )}
        </div>

        {error && (
          <span className="flex items-center gap-1 text-xs text-destructive">
            <AlertCircle className="h-3.5 w-3.5" /> {error}
          </span>
        )}

        {published && (
          <span className="flex items-center gap-1 text-xs text-green-600">
            <CheckCircle2 className="h-3.5 w-3.5" /> Published!
          </span>
        )}

        <Button
          size="sm"
          variant="outline"
          onClick={handlePublish}
          disabled={publishing || files.length === 0}
        >
          {publishing ? (
            <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Upload className="mr-2 h-3.5 w-3.5" />
          )}
          {publishing ? "Publishing…" : "Publish"}
        </Button>
      </div>

      {/* Main split pane */}
      <div className="flex flex-1 min-h-0">
        {/* Chat pane — 40% */}
        <div className="w-2/5 border-r flex flex-col min-h-0">
          <WebsiteBuilderChat
            websiteId={website.id}
            initialMessages={website.chat_history}
            initialFiles={files}
            onFilesUpdate={(updated) => {
              setFiles(updated);
              if (!activeFile || !updated.find((f) => f.path === activeFile)) {
                setActiveFile(updated[0]?.path ?? "index.html");
              }
            }}
          />
        </div>

        {/* Preview + files pane — 60% */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* File tabs */}
          {files.length > 1 && (
            <div className="flex gap-1 px-3 pt-2 pb-0 border-b overflow-x-auto shrink-0">
              {files.map((f) => (
                <button
                  key={f.path}
                  onClick={() => setActiveFile(f.path)}
                  className={`px-3 py-1.5 text-xs rounded-t border-b-2 whitespace-nowrap transition-colors ${
                    activeFile === f.path
                      ? "border-primary text-primary font-medium"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {f.path}
                </button>
              ))}
            </div>
          )}

          {files.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
              Preview will appear here once you describe your website
            </div>
          ) : activeFile === "index.html" || files.length === 1 ? (
            <iframe
              srcDoc={activeFile === "index.html" ? indexHtml : activeContent}
              className="flex-1 w-full border-0"
              sandbox="allow-scripts"
              title="Website preview"
            />
          ) : (
            <pre className="flex-1 overflow-auto p-4 text-xs font-mono bg-muted/30 whitespace-pre-wrap">
              {activeContent}
            </pre>
          )}
        </div>
      </div>

      {/* Domain settings footer */}
      <div className="border-t px-4 py-3 shrink-0 flex items-center gap-3 flex-wrap">
        <Label className="text-xs text-muted-foreground shrink-0">Custom domain</Label>
        <Input
          className="h-7 text-xs max-w-xs font-mono"
          placeholder="yourdomain.com"
          value={domainInput}
          onChange={(e) => setDomainInput(e.target.value)}
        />
        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={handleSaveDomain} disabled={savingDomain || !domainInput.trim()}>
          {savingDomain ? <Loader2 className="h-3 w-3 animate-spin" /> : "Save"}
        </Button>
        {domainSaved && (
          <span className="flex items-center gap-1 text-xs text-green-600">
            <CheckCircle2 className="h-3 w-3" /> Saved
          </span>
        )}
        {website.custom_domain && (
          <p className="text-xs text-muted-foreground ml-2">
            Point a CNAME record at <code className="font-mono">{website.subdomain}.silentchair.app</code>
          </p>
        )}
      </div>
    </div>
  );
}
