"use client";

import { useEffect, useState } from "react";
import { Loader2, Mail, User, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { getActivityEntry, type ActivityDetail } from "@/lib/activity-api";

interface Props {
  activityLogId: string;
}

function EmailPreview({ email }: { email: NonNullable<ActivityDetail["outreach_emails"]>[number] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-border rounded-md overflow-hidden text-xs">
      <button
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        className="w-full flex items-start gap-2 p-2 text-left hover:bg-muted/50 transition-colors"
      >
        {open ? <ChevronDown className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" /> : <ChevronRight className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" />}
        <div className="min-w-0">
          <p className="font-medium truncate">{email.subject}</p>
          <p className="text-muted-foreground truncate">To: {email.to_name} &lt;{email.to_email}&gt;</p>
        </div>
      </button>
      {open && (
        <div
          className="px-3 pb-3 pt-1 border-t border-border bg-muted/20 prose prose-xs max-w-none text-xs"
          dangerouslySetInnerHTML={{ __html: email.body_html }}
          onClick={(e) => e.stopPropagation()}
        />
      )}
    </div>
  );
}

function ArticlePreview({ article }: { article: NonNullable<ActivityDetail["edited_articles"]>[number] }) {
  const [open, setOpen] = useState(false);
  const wordCount = article.content.split(/\s+/).length;
  return (
    <div className="border border-border rounded-md overflow-hidden text-xs">
      <button
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        className="w-full flex items-start gap-2 p-2 text-left hover:bg-muted/50 transition-colors"
      >
        {open ? <ChevronDown className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" /> : <ChevronRight className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" />}
        <div className="min-w-0">
          <p className="font-medium truncate">{article.title}</p>
          <p className="text-muted-foreground">{wordCount.toLocaleString()} words · /{article.slug}</p>
        </div>
      </button>
      {open && (
        <div
          className="px-3 pb-3 pt-1 border-t border-border bg-muted/20 prose prose-xs max-w-none text-xs"
          dangerouslySetInnerHTML={{ __html: article.content.substring(0, 2000) + (article.content.length > 2000 ? "…" : "") }}
          onClick={(e) => e.stopPropagation()}
        />
      )}
    </div>
  );
}

function LeadRow({ lead }: { lead: Record<string, unknown> }) {
  return (
    <div className="flex items-center gap-2 py-1 border-b border-border last:border-0 text-xs">
      <User className="h-3 w-3 text-muted-foreground shrink-0" />
      <div className="min-w-0">
        <span className="font-medium">{String(lead.name ?? "")}</span>
        {lead.company && <span className="text-muted-foreground"> · {String(lead.company)}</span>}
        {lead.email && <span className="text-muted-foreground block truncate">{String(lead.email)}</span>}
        {lead.qualification_reason && (
          <span className="text-muted-foreground block">{String(lead.qualification_reason)}</span>
        )}
      </div>
      {lead.score !== undefined && (
        <span className="ml-auto shrink-0 text-[10px] font-mono bg-muted rounded px-1">{String(lead.score)}/10</span>
      )}
    </div>
  );
}

export function ApprovalDetail({ activityLogId }: Props) {
  const [detail, setDetail] = useState<ActivityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getActivityEntry(activityLogId)
      .then((entry) => setDetail(entry.detail))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [activityLogId]);

  if (loading) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground py-1">
        <Loader2 className="h-3 w-3 animate-spin" /> Loading work…
      </div>
    );
  }

  if (error || !detail) {
    return <p className="text-xs text-muted-foreground italic">Could not load work details.</p>;
  }

  const emails = detail.outreach_emails ?? [];
  const articles = detail.edited_articles ?? [];
  const leads = detail.qualified_leads ?? [];

  if (!emails.length && !articles.length && !leads.length) {
    return <p className="text-xs text-muted-foreground italic">No detailed preview available.</p>;
  }

  return (
    <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
      {emails.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1">
            <Mail className="h-3 w-3" /> {emails.length} email{emails.length !== 1 ? "s" : ""} to send
          </p>
          {emails.map((e, i) => <EmailPreview key={i} email={e} />)}
        </div>
      )}
      {articles.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1">
            <FileText className="h-3 w-3" /> {articles.length} article{articles.length !== 1 ? "s" : ""} to publish
          </p>
          {articles.map((a, i) => <ArticlePreview key={i} article={a} />)}
        </div>
      )}
      {leads.length > 0 && (
        <div className="space-y-0 border border-border rounded-md overflow-hidden">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1 px-2 py-1.5 bg-muted/30">
            <User className="h-3 w-3" /> {leads.length} qualified lead{leads.length !== 1 ? "s" : ""}
          </p>
          <div className="px-2 divide-y divide-border">
            {leads.map((l, i) => <LeadRow key={i} lead={l} />)}
          </div>
        </div>
      )}
    </div>
  );
}
