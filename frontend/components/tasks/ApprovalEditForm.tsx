"use client";

import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { type ActivityDetail, type OutreachEmail } from "@/lib/activity-api";

interface Props {
  payload: ActivityDetail;
  onChange: (payload: ActivityDetail) => void;
}

export function ApprovalEditForm({ payload, onChange }: Props) {
  const emails = payload.outreach_emails ?? [];
  const articles = payload.edited_articles ?? [];
  const leads = (payload.qualified_leads ?? []) as Array<Record<string, unknown> & { _included?: boolean }>;

  function updateEmail(index: number, field: keyof OutreachEmail, value: string) {
    const updated = emails.map((e, i) => i === index ? { ...e, [field]: value } : e);
    onChange({ ...payload, outreach_emails: updated });
  }

  function removeEmail(index: number) {
    onChange({ ...payload, outreach_emails: emails.filter((_, i) => i !== index) });
  }

  function updateArticle(index: number, field: "title" | "slug", value: string) {
    const updated = articles.map((a, i) => i === index ? { ...a, [field]: value } : a);
    onChange({ ...payload, edited_articles: updated });
  }

  function removeArticle(index: number) {
    onChange({ ...payload, edited_articles: articles.filter((_, i) => i !== index) });
  }

  function toggleLead(index: number, included: boolean) {
    const updated = leads.map((l, i) => i === index ? { ...l, _included: included } : l);
    onChange({ ...payload, qualified_leads: updated });
  }

  const hasEmails = emails.length > 0;
  const hasArticles = articles.length > 0;
  const hasLeads = leads.length > 0;

  if (!hasEmails && !hasArticles && !hasLeads) {
    return <p className="text-sm text-muted-foreground italic">Nothing to edit for this approval.</p>;
  }

  return (
    <div className="space-y-5">
      {hasEmails && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Outreach Emails ({emails.length})
          </p>
          <div className="space-y-2">
            {emails.map((email, i) => (
              <div key={i} className="rounded border border-border p-2.5 space-y-1.5 text-xs relative">
                <button
                  onClick={() => removeEmail(i)}
                  className="absolute top-2 right-2 text-muted-foreground hover:text-destructive transition-colors"
                  title="Remove this email"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <p className="text-muted-foreground truncate pr-5">
                  To: <span className="text-foreground font-medium">{email.to_name}</span>
                  {email.to_email && <span> &lt;{email.to_email}&gt;</span>}
                </p>
                <Input
                  value={email.subject}
                  onChange={(e) => updateEmail(i, "subject", e.target.value)}
                  placeholder="Subject line"
                  className="h-7 text-xs"
                />
              </div>
            ))}
          </div>
          {emails.length === 0 && (
            <p className="text-xs text-muted-foreground italic">All emails removed.</p>
          )}
        </div>
      )}

      {hasArticles && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Articles ({articles.length})
          </p>
          <div className="space-y-2">
            {articles.map((article, i) => (
              <div key={i} className="rounded border border-border p-2.5 space-y-1.5 text-xs relative">
                <button
                  onClick={() => removeArticle(i)}
                  className="absolute top-2 right-2 text-muted-foreground hover:text-destructive transition-colors"
                  title="Remove this article"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <Input
                  value={article.title}
                  onChange={(e) => updateArticle(i, "title", e.target.value)}
                  placeholder="Article title"
                  className="h-7 text-xs pr-6"
                />
                <div className="flex items-center gap-1 text-muted-foreground">
                  <span>/</span>
                  <Input
                    value={article.slug}
                    onChange={(e) => updateArticle(i, "slug", e.target.value)}
                    placeholder="slug"
                    className="h-7 text-xs font-mono"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasLeads && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Leads — uncheck to exclude
          </p>
          <div className="space-y-1.5">
            {leads.map((lead, i) => {
              const included = lead._included !== false;
              return (
                <div
                  key={i}
                  className={`flex items-start gap-2.5 rounded border px-2.5 py-2 text-xs transition-opacity ${included ? "border-border" : "border-border opacity-40"}`}
                >
                  <input
                    type="checkbox"
                    checked={included}
                    onChange={(e) => toggleLead(i, e.target.checked)}
                    className="mt-0.5 shrink-0 h-4 w-4 cursor-pointer accent-primary"
                  />
                  <div className="min-w-0">
                    <p className="font-medium truncate">{String(lead.company || lead.name || "")}</p>
                    {!!lead.email && <p className="text-muted-foreground truncate">{String(lead.email)}</p>}
                    {!!lead.qualification_reason && (
                      <p className="text-muted-foreground">{String(lead.qualification_reason)}</p>
                    )}
                  </div>
                  {lead.score !== undefined && (
                    <span className="ml-auto shrink-0 text-[10px] font-mono bg-muted rounded px-1">
                      {String(lead.score)}/10
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
