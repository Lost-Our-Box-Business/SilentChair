"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2, DollarSign, TrendingUp, AlertCircle, CheckCircle2 } from "lucide-react";
import { getBudgetState, getUsageHistory, updateBudget, type BudgetState, type DailyUsage } from "@/lib/usage-api";
import { createClient } from "@/lib/supabase/client";

const DEPT_LABELS: Record<string, string> = {
  editorial: "Editorial",
  seo: "SEO",
  social_media: "Social Media",
  distribution: "Distribution",
  analytics: "Analytics",
  market_research: "Market Research",
  lead_research: "Lead Research",
  lead_qualification: "Lead Qualification",
  outreach: "Outreach",
  lead_generation: "Lead Generation",
  sales_outreach: "Sales Outreach",
  proposals_contracts: "Proposals & Contracts",
  billing: "Billing",
};

function formatCost(n: number): string {
  if (n === 0) return "$0.00";
  if (n < 0.001) return `$${n.toFixed(6)}`;
  if (n < 0.01) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(4)}`;
}

function SpendBar({ spend, limit }: { spend: number; limit: number | null }) {
  if (limit === null) return null;
  const pct = Math.min(100, (spend / limit) * 100);
  const color = pct > 90 ? "bg-destructive" : pct > 70 ? "bg-amber-500" : "bg-primary";
  return (
    <div className="mt-1">
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-[10px] text-muted-foreground mt-0.5">
        {formatCost(spend)} of {formatCost(limit)} used ({pct.toFixed(1)}%)
      </p>
    </div>
  );
}

export default function BudgetPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const [budget, setBudget] = useState<BudgetState | null>(null);
  const [history, setHistory] = useState<DailyUsage[]>([]);
  const [activeDepts, setActiveDepts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Editable form state
  const [dailyLimit, setDailyLimit] = useState("");
  const [deptLimits, setDeptLimits] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const supabase = createClient();
      const [budgetData, historyData, deptsResult] = await Promise.all([
        getBudgetState(businessId),
        getUsageHistory(businessId, 7),
        supabase
          .from("departments")
          .select("dept_type")
          .eq("business_id", businessId)
          .eq("is_active", true),
      ]);
      setBudget(budgetData);
      setHistory(historyData);
      setActiveDepts((deptsResult.data ?? []).map((d: { dept_type: string }) => d.dept_type));

      // Populate form
      setDailyLimit(budgetData.daily_budget != null ? String(budgetData.daily_budget) : "");
      const dl: Record<string, string> = {};
      for (const dept of (deptsResult.data ?? []).map((d: { dept_type: string }) => d.dept_type)) {
        dl[dept] = budgetData.dept_budgets[dept] != null ? String(budgetData.dept_budgets[dept]) : "";
      }
      setDeptLimits(dl);
    } catch {
      setError("Failed to load budget data.");
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => { load(); }, [load]);

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const daily_budget = dailyLimit.trim() ? parseFloat(dailyLimit) : null;
      const dept_budgets: Record<string, number | null> = {};
      for (const [dept, val] of Object.entries(deptLimits)) {
        dept_budgets[dept] = val.trim() ? parseFloat(val) : null;
      }
      await updateBudget(businessId, { daily_budget, dept_budgets });
      setSaved(true);
      await load();
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError("Failed to save budget settings.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 max-w-2xl">
        <Skeleton className="h-7 w-48" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  const weekTotal = history.reduce((s, d) => s + d.total, 0);

  return (
    <div className="space-y-8 max-w-2xl">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Budget & Usage</h1>
        <p className="text-sm text-muted-foreground">
          Set daily spending limits and per-department allocations. The CEO agent enforces these before each pipeline run.
        </p>
      </div>

      {error && (
        <p className="flex items-center gap-1.5 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" /> {error}
        </p>
      )}

      {/* Today's snapshot */}
      {budget && (
        <div className="grid gap-3 sm:grid-cols-3">
          <Card className="border-none bg-muted/50">
            <CardContent className="pt-4 pb-3">
              <p className="text-xs text-muted-foreground">Today's spend</p>
              <p className="text-xl font-bold mt-0.5">{formatCost(budget.today_spend)}</p>
              {budget.daily_budget != null && (
                <SpendBar spend={budget.today_spend} limit={budget.daily_budget} />
              )}
            </CardContent>
          </Card>
          <Card className="border-none bg-muted/50">
            <CardContent className="pt-4 pb-3">
              <p className="text-xs text-muted-foreground">Daily limit</p>
              <p className="text-xl font-bold mt-0.5">
                {budget.daily_budget != null ? formatCost(budget.daily_budget) : "Unlimited"}
              </p>
              {budget.daily_remaining != null && (
                <p className="text-[10px] text-muted-foreground mt-1">
                  {formatCost(budget.daily_remaining)} remaining
                </p>
              )}
            </CardContent>
          </Card>
          <Card className="border-none bg-muted/50">
            <CardContent className="pt-4 pb-3">
              <p className="text-xs text-muted-foreground">Last 7 days</p>
              <p className="text-xl font-bold mt-0.5">{formatCost(weekTotal)}</p>
              <p className="text-[10px] text-muted-foreground mt-1">avg {formatCost(weekTotal / 7)}/day</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Usage by dept today */}
      {budget && Object.keys(budget.today_by_dept).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Today's spend by department
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-2">
            {Object.entries(budget.today_by_dept)
              .sort(([, a], [, b]) => b - a)
              .map(([dept, cost]) => (
                <div key={dept} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{DEPT_LABELS[dept] ?? dept}</span>
                  <div className="text-right">
                    <span className="font-mono text-xs">{formatCost(cost)}</span>
                    {budget.dept_budgets[dept] != null && (
                      <span className="text-[10px] text-muted-foreground ml-2">
                        / {formatCost(budget.dept_budgets[dept])}
                      </span>
                    )}
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>
      )}

      {/* Settings form */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-sm flex items-center gap-2">
            <DollarSign className="h-4 w-4" /> Spending limits
          </CardTitle>
          <CardDescription className="text-xs">
            Leave blank for unlimited. Costs are calculated using Claude Opus 4.7 pricing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Daily limit */}
          <div className="space-y-1.5">
            <Label className="text-xs">Daily spending limit (USD)</Label>
            <div className="relative max-w-xs">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
              <Input
                className="pl-7 font-mono text-sm"
                placeholder="e.g. 5.00"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
                type="number"
                min="0"
                step="0.01"
              />
            </div>
            <p className="text-[10px] text-muted-foreground">
              Pipeline runs that would exceed this limit are blocked by the CEO agent.
            </p>
          </div>

          {/* Per-department limits */}
          {activeDepts.length > 0 && (
            <div className="space-y-3">
              <Label className="text-xs">Department allocations (USD/day)</Label>
              <div className="grid gap-2 sm:grid-cols-2">
                {activeDepts.map((dept) => (
                  <div key={dept} className="space-y-1">
                    <Label htmlFor={`dept-${dept}`} className="text-[11px] text-muted-foreground">
                      {DEPT_LABELS[dept] ?? dept}
                      {budget?.today_by_dept[dept] != null && (
                        <span className="ml-1.5 text-foreground">(today: {formatCost(budget.today_by_dept[dept]!)})</span>
                      )}
                    </Label>
                    <div className="relative">
                      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">$</span>
                      <Input
                        id={`dept-${dept}`}
                        className="pl-6 font-mono text-xs h-8"
                        placeholder="unlimited"
                        value={deptLimits[dept] ?? ""}
                        onChange={(e) => setDeptLimits((p) => ({ ...p, [dept]: e.target.value }))}
                        type="number"
                        min="0"
                        step="0.01"
                      />
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground">
                Departments over their allocation are paused by the CEO agent until the next day.
              </p>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <Button onClick={handleSave} disabled={saving} size="sm">
              {saving && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
              {saving ? "Saving…" : "Save limits"}
            </Button>
            {saved && (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <CheckCircle2 className="h-3.5 w-3.5" /> Saved
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 7-day history */}
      {history.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Spending history (last 7 days)</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-1.5">
              {history.slice(-7).map((day) => (
                <div key={day.date} className="flex items-center gap-3 text-xs">
                  <span className="text-muted-foreground w-20 shrink-0">{day.date}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary/60"
                      style={{
                        width: weekTotal > 0 ? `${Math.min(100, (day.total / (weekTotal / 7)) * 50)}%` : "0%",
                      }}
                    />
                  </div>
                  <span className="font-mono text-right w-20 shrink-0">{formatCost(day.total)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
