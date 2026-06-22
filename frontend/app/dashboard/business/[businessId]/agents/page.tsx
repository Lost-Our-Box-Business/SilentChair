"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Play, Pause, RefreshCw, ChevronRight, Cpu } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";
import {
  getAgents, startAgents, pauseAgents, resumeAgents,
  type DepartmentStatus,
} from "@/lib/agents-api";

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function timeUntil(iso: string | null): string {
  if (!iso) return "—";
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return "soon";
  const mins = Math.ceil(diff / 60000);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.ceil(diff / 3600000);
  return `${hrs}h`;
}

function StatusBadge({ dept, t }: { dept: DepartmentStatus; t: (k: string) => string }) {
  if (dept.is_paused) return <Badge variant="outline">{t("statusPaused")}</Badge>;
  if (dept.last_run_status === "in_progress") return <Badge className="bg-blue-500 text-white border-0">{t("statusActive")}</Badge>;
  return <Badge variant="secondary">{t("statusIdle")}</Badge>;
}

export default function AgentsPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations("agentsPage");

  const [depts, setDepts] = useState<DepartmentStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState<"start" | "pause" | "resume" | null>(null);
  const [isPaused, setIsPaused] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getAgents(businessId);
      setDepts(data);
      setIsPaused(data.some((d) => d.is_paused));
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => { load(); }, [load]);

  async function handleStart() {
    setActionBusy("start");
    try { await startAgents(businessId, locale); await load(); } finally { setActionBusy(null); }
  }

  async function handlePause() {
    setActionBusy("pause");
    try { await pauseAgents(businessId); await load(); } finally { setActionBusy(null); }
  }

  async function handleResume() {
    setActionBusy("resume");
    try { await resumeAgents(businessId, locale); await load(); } finally { setActionBusy(null); }
  }

  const anyActive = depts.some((d) => d.last_run_status === "in_progress");

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {!anyActive && !isPaused && (
            <Button size="sm" onClick={handleStart} disabled={!!actionBusy}>
              {actionBusy === "start" ? (
                <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />{t("starting")}</>
              ) : (
                <><Play className="h-3.5 w-3.5 mr-1.5" />{t("start")}</>
              )}
            </Button>
          )}
          {isPaused && (
            <Button size="sm" onClick={handleResume} disabled={!!actionBusy}>
              {actionBusy === "resume" ? (
                <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />{t("resuming")}</>
              ) : (
                <><RefreshCw className="h-3.5 w-3.5 mr-1.5" />{t("resume")}</>
              )}
            </Button>
          )}
          {anyActive && !isPaused && (
            <Button size="sm" variant="outline" onClick={handlePause} disabled={!!actionBusy}>
              {actionBusy === "pause" ? (
                <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />{t("pausing")}</>
              ) : (
                <><Pause className="h-3.5 w-3.5 mr-1.5" />{t("pause")}</>
              )}
            </Button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : depts.length === 0 ? (
        <p className="text-sm text-muted-foreground py-10 text-center">{t("noDepts")}</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {depts.map((dept) => (
            <Card
              key={dept.dept_type}
              className="cursor-pointer hover:border-primary/50 transition-colors group"
              onClick={() => router.push(`/dashboard/business/${businessId}/departments/${dept.dept_type}`)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: dept.label_color || "#6366f1" }}
                    />
                    {dept.name}
                  </CardTitle>
                  <div className="flex items-center gap-1.5">
                    <StatusBadge dept={dept} t={t} />
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {dept.status_narrative ? (
                  <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                    {dept.status_narrative}
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground italic">—</p>
                )}

                <div className="flex items-center justify-between text-[10px] text-muted-foreground border-t pt-2">
                  <span>{t("lastRun")}: {timeAgo(dept.last_run_at)}</span>
                  <span>{t("nextEval")}: {timeUntil(dept.manager_next_eval_at)}</span>
                  <span>{t("todayCost")}: ${dept.today_cost_usd?.toFixed(4) ?? "0.0000"}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
