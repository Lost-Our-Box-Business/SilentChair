"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useRouter } from "next/navigation";
import {
  Play, Loader2, CheckCircle2, Clock, AlertCircle, RefreshCw, ExternalLink,
  Users, FileText, Receipt, DollarSign, Settings, Eye, ChevronDown, ChevronUp,
} from "lucide-react";
import {
  getActivityFeed, runPipeline,
  getLeads, getContracts, getInvoices,
  updateLeadStatus, updateContractStatus, updateInvoiceStatus,
  type ActivityEntry, type PipelineRunResult, type Lead, type Contract, type Invoice,
} from "@/lib/activity-api";
import { getTasks, approveTask, rejectTask, type Task } from "@/lib/tasks-api";
import { ApprovalReviewSheet } from "@/components/tasks/ApprovalReviewSheet";
import { useLocale, useTranslations } from "next-intl";
import { getBudgetState, type BudgetState } from "@/lib/usage-api";
import { BusinessOverviewCard } from "@/components/dashboard/BusinessOverviewCard";
import { ActivityDetailPanel } from "@/components/activity/ActivityDetailPanel";

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const LEAD_STATUS_COLORS: Record<Lead["status"], string> = {
  new: "outline", contacted: "secondary", qualified: "default",
  proposal_sent: "secondary", won: "default", lost: "destructive",
} as const;

const CONTRACT_STATUS_COLORS: Record<Contract["status"], string> = {
  draft: "outline", sent: "secondary", signed: "default",
} as const;

const INVOICE_STATUS_COLORS: Record<Invoice["status"], string> = {
  draft: "outline", sent: "secondary", paid: "default",
} as const;

type Tab = "activity" | "leads" | "contracts" | "invoices" | "usage";

// ── Pending task card (dashboard variant) ─────────────────────────────────────

function PendingTaskCard({ task, onDone }: { task: Task; onDone: () => void }) {
  const [reviewOpen, setReviewOpen] = useState(false);

  async function handleApprove(id: string) {
    await approveTask(id);
    onDone();
  }

  async function handleReject(id: string, reason: string) {
    await rejectTask(id, reason);
    onDone();
  }

  return (
    <Card className="border-yellow-500/40 bg-yellow-500/5">
      <CardHeader className="py-3 px-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium">{task.title}</p>
            <p className="text-xs text-muted-foreground">{timeAgo(task.created_at)}</p>
          </div>
          <Button
            size="sm" variant="outline"
            className="shrink-0 text-xs border-yellow-500/50 hover:bg-yellow-500/10"
            onClick={() => setReviewOpen(true)}
          >
            <Eye className="h-3 w-3 mr-1" /> Review
          </Button>
        </div>
      </CardHeader>
      <ApprovalReviewSheet
        open={reviewOpen}
        onOpenChange={setReviewOpen}
        task={task}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </Card>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

function formatCost(n: number): string {
  if (n === 0) return "$0.00";
  if (n < 0.001) return `$${n.toFixed(6)}`;
  if (n < 0.01) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(4)}`;
}

export default function BusinessDetailPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations("businessOps");
  const [tab, setTab] = useState<Tab>("activity");

  const actionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      pipeline_log: t("actionPipelineLog"),
      approval_required: t("actionApprovalRequired"),
      pipeline_complete: t("actionPipelineComplete"),
    };
    return labels[type] ?? type.replace(/_/g, " ");
  };

  const LEAD_STATUS_T: Record<Lead["status"], string> = {
    new: t("leadNew"), contacted: t("leadContacted"), qualified: t("leadQualified"),
    proposal_sent: t("leadProposalSent"), won: t("leadWon"), lost: t("leadLost"),
  };
  const CONTRACT_STATUS_T: Record<Contract["status"], string> = {
    draft: t("contractDraft"), sent: t("contractSent"), signed: t("contractSigned"),
  };
  const INVOICE_STATUS_T: Record<Invoice["status"], string> = {
    draft: t("invoiceDraft"), sent: t("invoiceSent"), paid: t("invoicePaid"),
  };
  const DEPT_LABELS_T: Record<string, string> = {
    editorial: t("deptEditorial"), seo: t("deptSeo"), social_media: t("deptSocialMedia"),
    distribution: t("deptDistribution"), analytics: t("deptAnalytics"),
    market_research: t("deptMarketResearch"), lead_research: t("deptLeadResearch"),
    lead_qualification: t("deptLeadQualification"), outreach: t("deptOutreach"),
    lead_generation: t("deptLeadGeneration"), sales_outreach: t("deptSalesOutreach"),
    proposals_contracts: t("deptProposalsContracts"), billing: t("deptBilling"),
  };

  const [expandedActivityId, setExpandedActivityId] = useState<string | null>(null);
  const [feed, setFeed] = useState<ActivityEntry[]>([]);
  const [pendingTasks, setPendingTasks] = useState<Task[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [budgetState, setBudgetState] = useState<BudgetState | null>(null);
  const [loading, setLoading] = useState(true);

  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<PipelineRunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [feedData, pendingTasksData, leadsData, contractsData, invoicesData, budgetData] = await Promise.all([
        getActivityFeed(businessId),
        getTasks(businessId, { status: "awaiting_approval" }),
        getLeads(businessId),
        getContracts(businessId),
        getInvoices(businessId),
        getBudgetState(businessId).catch(() => null),
      ]);
      setFeed(feedData);
      setPendingTasks(pendingTasksData);
      setLeads(leadsData);
      setContracts(contractsData);
      setInvoices(invoicesData);
      setBudgetState(budgetData);
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => { loadAll(); }, [loadAll]);

  // Refetch when the user returns to this tab after approving from the task board
  useEffect(() => {
    function onVisibilityChange() {
      if (!document.hidden) loadAll();
    }
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [loadAll]);

  async function handleRun() {
    setRunning(true); setRunResult(null); setRunError(null);
    try {
      const result = await runPipeline(businessId, locale);
      setRunResult(result);
      await loadAll();
    } catch (e: unknown) {
      setRunError(e instanceof Error ? e.message : "Pipeline failed.");
    } finally { setRunning(false); }
  }


  const TABS: { id: Tab; label: string; icon: React.ElementType; count?: number }[] = [
    { id: "activity", label: t("tabActivity"), icon: Clock, count: feed.length },
    { id: "leads", label: t("tabLeads"), icon: Users, count: leads.length },
    { id: "contracts", label: t("tabContracts"), icon: FileText, count: contracts.length },
    { id: "invoices", label: t("tabInvoices"), icon: Receipt, count: invoices.length },
    { id: "usage", label: t("tabUsage"), icon: DollarSign },
  ];

  return (
    <div className="space-y-6">
      <BusinessOverviewCard businessId={businessId} />

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">{t("operations")}</h1>
          <p className="text-sm text-muted-foreground">{t("operationsSubtitle")}</p>
        </div>
        <div className="flex items-center gap-2">
          {budgetState && (
            <span className="text-xs text-muted-foreground hidden sm:inline">
              {t("today")}: <span className="font-mono font-medium text-foreground">{formatCost(budgetState.today_spend)}</span>
              {budgetState.daily_budget != null && (
                <span> / {formatCost(budgetState.daily_budget)}</span>
              )}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={loadAll} disabled={loading}>
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            {t("refresh")}
          </Button>
          <Button size="sm" onClick={handleRun} disabled={running}>
            {running ? <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <Play className="h-3.5 w-3.5 mr-1.5" />}
            {running ? t("running") : t("runPipeline")}
          </Button>
        </div>
      </div>

      {/* Run result */}
      {runResult && (
        <Card className={runResult.status === "awaiting_approval" ? "border-yellow-500/50 bg-yellow-500/5" : "border-green-500/50 bg-green-500/5"}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              {runResult.status === "awaiting_approval"
                ? <AlertCircle className="h-4 w-4 text-yellow-500" />
                : <CheckCircle2 className="h-4 w-4 text-green-500" />}
              {runResult.status === "awaiting_approval" ? t("pipelinePaused") : t("pipelineComplete")}
            </CardTitle>
            {runResult.approval_action && <CardDescription className="text-xs">{runResult.approval_action}</CardDescription>}
          </CardHeader>
          <CardContent className="pt-0 space-y-2 text-xs text-muted-foreground">
            {runResult.published_urls && runResult.published_urls.length > 0 && (
              <div>
                {runResult.published_urls.map((url) => (
                  <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-primary hover:underline">
                    {url} <ExternalLink className="h-3 w-3" />
                  </a>
                ))}
              </div>
            )}
            {runResult.qualified_leads && runResult.qualified_leads.length > 0 && (
              <p>{t("qualifiedLeads", { count: runResult.qualified_leads.length })}</p>
            )}
            {runResult.contracts && runResult.contracts.length > 0 && (
              <p>{t("contractsDrafted", { count: runResult.contracts.length })}</p>
            )}
            {runResult.invoices && runResult.invoices.length > 0 && (
              <p>{t("invoicesGenerated", { count: runResult.invoices.length })}</p>
            )}
          </CardContent>
        </Card>
      )}
      {runError && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader className="pb-0">
            <CardTitle className="text-sm flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4" /> {t("pipelineError")}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2"><p className="text-xs text-muted-foreground">{runError}</p></CardContent>
        </Card>
      )}

      {/* Pending approvals (always visible) */}
      {pendingTasks.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-medium flex items-center gap-1.5">
            <AlertCircle className="h-4 w-4 text-yellow-500" /> {t("pendingApprovals", { count: pendingTasks.length })}
          </h2>
          {pendingTasks.map((task) => (
            <PendingTaskCard key={task.id} task={task} onDone={loadAll} />
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="space-y-4">
        <div className="flex gap-1 border-b">
          {TABS.map(({ id, label, icon: Icon, count }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors border-b-2 -mb-px focus-visible:outline-none ${
                tab === id ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
              {count !== undefined && count > 0 && (
                <span className="text-[10px] bg-muted rounded-full px-1.5 py-0.5 ml-0.5">{count}</span>
              )}
            </button>
          ))}
        </div>

        {/* Activity Tab */}
        {tab === "activity" && (
          <div className="space-y-1">
            {loading ? (
              <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /><span className="text-sm">Loading…</span>
              </div>
            ) : feed.length === 0 ? (
              <Card><CardContent className="py-12 text-center"><p className="text-sm text-muted-foreground">{t("noActivity")}</p></CardContent></Card>
            ) : (
              feed.slice(0, 30).map((entry) => {
                const isExpanded = expandedActivityId === entry.id;
                return (
                  <div key={entry.id} className="rounded-lg border overflow-hidden">
                    <button
                      onClick={() => setExpandedActivityId(isExpanded ? null : entry.id)}
                      className="w-full flex items-start gap-3 px-3 py-2.5 text-left hover:bg-muted/30 transition-colors focus-visible:outline-none"
                    >
                      {entry.requires_approval && !entry.approved_at
                        ? <AlertCircle className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" />
                        : entry.approved_at
                        ? <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                        : <Clock className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm leading-snug">{entry.summary}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge variant="outline" className="text-[10px] px-1 py-0">{actionTypeLabel(entry.action_type)}</Badge>
                          <span className="text-xs text-muted-foreground">{timeAgo(entry.created_at)}</span>
                          {entry.approved_at && <span className="text-xs text-green-600">{t("approved")} {timeAgo(entry.approved_at)}</span>}
                        </div>
                      </div>
                      {isExpanded
                        ? <ChevronUp className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
                        : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />}
                    </button>
                    {isExpanded && (
                      <div className="px-3 pb-3">
                        <ActivityDetailPanel
                          detail={entry.detail}
                          actionType={entry.action_type}
                          summary={entry.summary}
                          businessId={businessId}
                        />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Leads Tab */}
        {tab === "leads" && (
          <div className="space-y-2">
            {leads.length === 0 ? (
              <Card><CardContent className="py-12 text-center"><p className="text-sm text-muted-foreground">{t("noLeads")}</p></CardContent></Card>
            ) : (
              leads.map((lead) => (
                <Card key={lead.id}>
                  <CardHeader className="py-3 px-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-0.5">
                        <p className="text-sm font-medium">{lead.name}</p>
                        <p className="text-xs text-muted-foreground">{lead.company}{lead.email ? ` · ${lead.email}` : ""}</p>
                        {lead.notes && <p className="text-xs text-muted-foreground line-clamp-1">{lead.notes}</p>}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {lead.score !== null && (
                          <span className="text-xs font-medium bg-muted rounded px-1.5 py-0.5">{t("score")}: {lead.score}/10</span>
                        )}
                        <Badge variant={(LEAD_STATUS_COLORS[lead.status] as "default" | "secondary" | "destructive" | "outline") ?? "outline"} className="text-[10px]">
                          {LEAD_STATUS_T[lead.status]}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {(["new", "contacted", "qualified", "proposal_sent", "won", "lost"] as Lead["status"][]).map((s) => (
                        <button
                          key={s}
                          disabled={lead.status === s}
                          onClick={async () => {
                            await updateLeadStatus(lead.id, s);
                            setLeads((prev) => prev.map((l) => l.id === lead.id ? { ...l, status: s } : l));
                          }}
                          className={`text-[10px] px-2 py-0.5 rounded border transition-colors focus-visible:outline-none ${lead.status === s ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-primary/50"}`}
                        >
                          {LEAD_STATUS_T[s]}
                        </button>
                      ))}
                    </div>
                  </CardHeader>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Contracts Tab */}
        {tab === "contracts" && (
          <div className="space-y-2">
            {contracts.length === 0 ? (
              <Card><CardContent className="py-12 text-center"><p className="text-sm text-muted-foreground">{t("noContracts")}</p></CardContent></Card>
            ) : (
              contracts.map((contract) => (
                <Card key={contract.id}>
                  <CardHeader className="py-3 px-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-0.5">
                        <p className="text-sm font-medium">{contract.title}</p>
                        <p className="text-xs text-muted-foreground">{t("created")} {timeAgo(contract.created_at)}</p>
                      </div>
                      <Badge variant={(CONTRACT_STATUS_COLORS[contract.status] as "default" | "secondary" | "outline") ?? "outline"} className="text-[10px] shrink-0">
                        {CONTRACT_STATUS_T[contract.status]}
                      </Badge>
                    </div>
                    <div className="flex gap-1 mt-2">
                      {(["draft", "sent", "signed"] as Contract["status"][]).map((s) => (
                        <button
                          key={s}
                          disabled={contract.status === s}
                          onClick={async () => {
                            await updateContractStatus(contract.id, s);
                            setContracts((prev) => prev.map((c) => c.id === contract.id ? { ...c, status: s } : c));
                          }}
                          className={`text-[10px] px-2 py-0.5 rounded border transition-colors focus-visible:outline-none ${contract.status === s ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-primary/50"}`}
                        >
                          {CONTRACT_STATUS_T[s]}
                        </button>
                      ))}
                    </div>
                    <details className="mt-2">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">{t("viewContractHtml")}</summary>
                      <div className="mt-2 rounded border bg-muted/30 p-3 text-xs overflow-auto max-h-64"
                        dangerouslySetInnerHTML={{ __html: contract.content }} />
                    </details>
                  </CardHeader>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Usage Tab */}
        {tab === "usage" && (
          <div className="space-y-4">
            {budgetState ? (
              <>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl border p-4 bg-muted/30 space-y-1">
                    <p className="text-xs text-muted-foreground">{t("todaySpend")}</p>
                    <p className="text-lg font-bold">{formatCost(budgetState.today_spend)}</p>
                    {budgetState.daily_budget != null && (
                      <div className="mt-1">
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full ${(budgetState.today_spend / budgetState.daily_budget) > 0.9 ? "bg-destructive" : (budgetState.today_spend / budgetState.daily_budget) > 0.7 ? "bg-amber-500" : "bg-primary"}`}
                            style={{ width: `${Math.min(100, (budgetState.today_spend / budgetState.daily_budget) * 100)}%` }}
                          />
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          {t("dailyLimitOf", { amount: formatCost(budgetState.daily_budget) })}
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="rounded-xl border p-4 bg-muted/30 space-y-1">
                    <p className="text-xs text-muted-foreground">{t("dailyLimit")}</p>
                    <p className="text-lg font-bold">
                      {budgetState.daily_budget != null ? formatCost(budgetState.daily_budget) : t("unlimited")}
                    </p>
                    {budgetState.daily_remaining != null && (
                      <p className="text-[10px] text-muted-foreground">{t("remaining", { amount: formatCost(budgetState.daily_remaining) })}</p>
                    )}
                  </div>
                  <div className="rounded-xl border p-4 bg-muted/30 flex items-end justify-between">
                    <div>
                      <p className="text-xs text-muted-foreground">{t("budgetSettings")}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{t("setLimits")}</p>
                    </div>
                    <button
                      onClick={() => router.push(`/dashboard/business/${businessId}/budget`)}
                      className="flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      <Settings className="h-3 w-3" /> {t("configure")}
                    </button>
                  </div>
                </div>

                {Object.keys(budgetState.today_by_dept).length > 0 && (
                  <div className="rounded-xl border p-4 space-y-2">
                    <p className="text-xs font-medium">{t("spendByDept")}</p>
                    {Object.entries(budgetState.today_by_dept)
                      .sort(([, a], [, b]) => b - a)
                      .map(([dept, cost]) => (
                        <div key={dept} className="flex items-center gap-3 text-sm">
                          <span className="text-muted-foreground text-xs w-40 shrink-0">{DEPT_LABELS_T[dept] ?? dept}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                            <div
                              className="h-full rounded-full bg-primary/60"
                              style={{
                                width: budgetState.today_spend > 0
                                  ? `${Math.min(100, (cost / budgetState.today_spend) * 100)}%`
                                  : "0%",
                              }}
                            />
                          </div>
                          <span className="font-mono text-xs w-20 text-right shrink-0">{formatCost(cost)}</span>
                          {budgetState.dept_budgets[dept] != null && (
                            <span className="text-[10px] text-muted-foreground w-16 shrink-0">
                              / {formatCost(budgetState.dept_budgets[dept]!)}
                            </span>
                          )}
                        </div>
                      ))}
                  </div>
                )}

                {Object.keys(budgetState.today_by_dept).length === 0 && (
                  <Card>
                    <CardContent className="py-12 text-center">
                      <p className="text-sm text-muted-foreground">{t("noUsage")}</p>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-sm text-muted-foreground">{t("usageUnavailable")}</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Invoices Tab */}
        {tab === "invoices" && (
          <div className="space-y-2">
            {invoices.length === 0 ? (
              <Card><CardContent className="py-12 text-center"><p className="text-sm text-muted-foreground">{t("noInvoices")}</p></CardContent></Card>
            ) : (
              invoices.map((invoice) => (
                <Card key={invoice.id}>
                  <CardHeader className="py-3 px-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-0.5">
                        <p className="text-sm font-medium">{invoice.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {invoice.amount > 0 && <span className="font-medium text-foreground">${invoice.amount.toLocaleString()}</span>}
                          {invoice.amount > 0 && " · "}
                          {t("created")} {timeAgo(invoice.created_at)}
                        </p>
                      </div>
                      <Badge variant={(INVOICE_STATUS_COLORS[invoice.status] as "default" | "secondary" | "outline") ?? "outline"} className="text-[10px] shrink-0">
                        {INVOICE_STATUS_T[invoice.status]}
                      </Badge>
                    </div>
                    <div className="flex gap-1 mt-2">
                      {(["draft", "sent", "paid"] as Invoice["status"][]).map((s) => (
                        <button
                          key={s}
                          disabled={invoice.status === s}
                          onClick={async () => {
                            await updateInvoiceStatus(invoice.id, s);
                            setInvoices((prev) => prev.map((i) => i.id === invoice.id ? { ...i, status: s } : i));
                          }}
                          className={`text-[10px] px-2 py-0.5 rounded border transition-colors focus-visible:outline-none ${invoice.status === s ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-primary/50"}`}
                        >
                          {INVOICE_STATUS_T[s]}
                        </button>
                      ))}
                    </div>
                    <details className="mt-2">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">{t("viewInvoiceHtml")}</summary>
                      <div className="mt-2 rounded border bg-muted/30 p-3 text-xs overflow-auto max-h-64"
                        dangerouslySetInnerHTML={{ __html: invoice.content }} />
                    </details>
                  </CardHeader>
                </Card>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
