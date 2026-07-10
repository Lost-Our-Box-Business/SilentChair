"use client";

import Link from "next/link";
import { type ActivityDetail } from "@/lib/activity-api";

type Props = {
  detail: ActivityDetail;
  actionType: string;
  summary: string;
  businessId: string;
};

function str(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string") return v;
  if (typeof v === "number") return String(v);
  return JSON.stringify(v);
}

function deptFromActionType(actionType: string): string | null {
  if (actionType.startsWith("dept_")) return actionType.slice(5);
  return null;
}

function deptFromSummary(summary: string): string | null {
  const s = summary.toLowerCase();
  if (s.includes("lead") || s.includes("qualif") || s.includes("outreach") || s.includes("market research")) {
    return "lead_generation";
  }
  if (s.includes("editorial") || s.includes("article") || s.includes("blog") || s.includes("content")) {
    return "editorial";
  }
  return null;
}

export function ActivityDetailPanel({ detail, actionType, summary, businessId }: Props) {
  const deptType = deptFromActionType(actionType) ?? deptFromSummary(summary);

  const hasLeads = (detail.leads?.length ?? 0) > 0;
  const hasQualified = (detail.qualified_leads?.length ?? 0) > 0;
  const qualificationRan = detail.qualified_leads !== undefined;
  const hasMarket = !!detail.market_research && Object.keys(detail.market_research).length > 0;
  const hasEmails = (detail.outreach_emails?.length ?? 0) > 0;
  const hasArticles = (detail.edited_articles?.length ?? 0) > 0;
  const hasAny = hasLeads || hasQualified || hasMarket || hasEmails || hasArticles;

  const mr = detail.market_research as Record<string, unknown> | undefined;

  return (
    <div className="mt-2 space-y-3 border-t pt-2">
      {!hasAny && (
        <p className="text-xs text-muted-foreground italic">No additional data recorded for this step.</p>
      )}

      {/* Raw leads extracted before qualification */}
      {hasLeads && !qualificationRan && (
        <div>
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Extracted Companies
          </p>
          <div className="space-y-1">
            {detail.leads!.map((lead, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{str(lead.company || lead.name)}</span>
                {str(lead.source || lead.website) !== "—" && (
                  <span className="text-[10px]">· {str(lead.source || lead.website)}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Qualified leads (passed filter) */}
      {hasQualified && (
        <div>
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Qualified ({detail.qualified_leads!.length})
          </p>
          <div className="space-y-1.5">
            {detail.qualified_leads!.map((lead, i) => (
              <div key={i} className="rounded border border-green-500/20 bg-green-500/5 px-2 py-1.5 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{str(lead.company || lead.name)}</span>
                  {lead.score !== undefined && (
                    <span className="text-[10px] font-mono bg-green-500/10 text-green-700 dark:text-green-400 rounded px-1.5 py-0.5">
                      {str(lead.score)}/10
                    </span>
                  )}
                </div>
                {str(lead.email) !== "—" && <p className="text-muted-foreground mt-0.5">{str(lead.email)}</p>}
                {str(lead.qualification_reason || lead.reason) !== "—" && (
                  <p className="text-muted-foreground mt-0.5">{str(lead.qualification_reason || lead.reason)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Leads that were evaluated but didn't pass */}
      {hasLeads && qualificationRan && (
        <div>
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Evaluated ({detail.leads!.length} found, {detail.qualified_leads!.length} qualified)
          </p>
          <div className="space-y-1.5">
            {detail.leads!.map((lead, i) => {
              const passed = detail.qualified_leads!.some(
                (q) => str(q.company || q.name) === str(lead.company || lead.name)
              );
              return (
                <div
                  key={i}
                  className={`rounded border px-2 py-1.5 text-xs ${
                    passed
                      ? "border-green-500/20 bg-green-500/5"
                      : "border-border text-muted-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`font-medium ${passed ? "" : "text-foreground"}`}>
                      {str(lead.company || lead.name)}
                    </span>
                    <span className={`text-[10px] rounded px-1.5 py-0.5 font-mono ${passed ? "bg-green-500/10 text-green-700 dark:text-green-400" : "bg-muted"}`}>
                      {passed ? "✓ qualified" : "✗ rejected"}
                    </span>
                  </div>
                  {str(lead.qualification_reason || lead.reason || lead.disqualification_reason) !== "—" && (
                    <p className="mt-0.5">{str(lead.qualification_reason || lead.reason || lead.disqualification_reason)}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Market research */}
      {hasMarket && (
        <div>
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">Market Research</p>
          <div className="space-y-1 text-xs">
            {mr?.icp && (
              <p>
                <span className="font-medium text-foreground">ICP: </span>
                <span className="text-muted-foreground">{str(mr.icp)}</span>
              </p>
            )}
            {mr?.company_size && (
              <p>
                <span className="font-medium text-foreground">Company size: </span>
                <span className="text-muted-foreground">{str(mr.company_size)}</span>
              </p>
            )}
            {Array.isArray(mr?.target_industries) && (mr.target_industries as unknown[]).length > 0 && (
              <p>
                <span className="font-medium text-foreground">Industries: </span>
                <span className="text-muted-foreground">{(mr.target_industries as string[]).join(", ")}</span>
              </p>
            )}
            {Array.isArray(mr?.pain_points) && (mr.pain_points as unknown[]).length > 0 && (
              <p>
                <span className="font-medium text-foreground">Pain points: </span>
                <span className="text-muted-foreground">{(mr.pain_points as string[]).join(", ")}</span>
              </p>
            )}
            {Array.isArray(mr?.decision_makers) && (mr.decision_makers as unknown[]).length > 0 && (
              <p>
                <span className="font-medium text-foreground">Decision makers: </span>
                <span className="text-muted-foreground">{(mr.decision_makers as string[]).join(", ")}</span>
              </p>
            )}
            {mr?.summary && <p className="text-muted-foreground">{str(mr.summary)}</p>}
          </div>
        </div>
      )}

      {/* Outreach emails */}
      {hasEmails && (
        <div>
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Drafted Emails ({detail.outreach_emails!.length})
          </p>
          <div className="space-y-1">
            {detail.outreach_emails!.map((email, i) => (
              <div key={i} className="text-xs flex items-baseline gap-1.5 text-muted-foreground">
                <span className="font-medium text-foreground shrink-0">{email.to_name}</span>
                {email.to_email && <span className="shrink-0">· {email.to_email}</span>}
                {email.subject && <span className="text-[10px] truncate">— {email.subject}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Articles */}
      {hasArticles && (
        <div>
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Articles ({detail.edited_articles!.length})
          </p>
          <div className="space-y-1">
            {detail.edited_articles!.map((article, i) => (
              <div key={i} className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{article.title}</span>
                {article.slug && <span className="text-[10px]"> · /{article.slug}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Link to department manager chat */}
      {deptType && (
        <div className="pt-1 border-t">
          <Link
            href={`/dashboard/business/${businessId}/departments/${deptType}`}
            className="text-[10px] text-primary hover:underline"
          >
            Discuss with manager →
          </Link>
        </div>
      )}
    </div>
  );
}
