"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loader2, Send, MessageSquare, FileText, CheckCircle2, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { TaskBoard } from "@/components/tasks/TaskBoard";
import {
  getDepartment, chatWithManager, getDeptApprovalQueue,
  approveDeptQueueItem, rejectDeptQueueItem,
  type DepartmentDetail, type ApprovalQueueItem,
} from "@/lib/agents-api";
import {
  getTasks, approveTask, rejectTask, deleteTask,
  type Task,
} from "@/lib/tasks-api";
import { createClient } from "@/lib/supabase/client";

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
  return `${Math.ceil(diff / 3600000)}h`;
}

export default function DepartmentPage() {
  const { businessId, deptType } = useParams<{ businessId: string; deptType: string }>();
  const router = useRouter();
  const t = useTranslations("deptPage");

  const [dept, setDept] = useState<DepartmentDetail | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [queue, setQueue] = useState<ApprovalQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [chatHistory, setChatHistory] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [rejectId, setRejectId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => {
      setUserId(data.user?.id ?? null);
    });
  }, []);

  const load = useCallback(async () => {
    try {
      const [deptData, taskData, queueData] = await Promise.all([
        getDepartment(businessId, deptType),
        getTasks(businessId),
        getDeptApprovalQueue(businessId, deptType),
      ]);
      setDept(deptData);
      setChatHistory(deptData.manager_chat_history ?? []);
      setTasks(taskData.filter((t) => t.department?.toLowerCase().replace(/\s+/g, "_") === deptType ||
        t.department?.toLowerCase() === deptType.replace(/_/g, " ")));
      setQueue(queueData);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [businessId, deptType]);

  useEffect(() => { load(); }, [load]);

  // Poll every 10 seconds so the task board updates without manual refresh
  useEffect(() => {
    const id = setInterval(() => {
      getTasks(businessId).then((data) => {
        setTasks(data.filter((t) => t.department?.toLowerCase().replace(/\s+/g, "_") === deptType ||
          t.department?.toLowerCase() === deptType.replace(/_/g, " ")));
      }).catch(() => {});
      getDeptApprovalQueue(businessId, deptType).then(setQueue).catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, [businessId, deptType]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  async function handleChat() {
    if (!chatInput.trim() || chatBusy) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatBusy(true);
    setChatHistory((prev) => [...prev, { role: "user", content: msg }]);
    try {
      const reply = await chatWithManager(businessId, deptType, msg);
      setChatHistory((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setChatHistory((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong." }]);
    } finally {
      setChatBusy(false);
    }
  }

  async function handleApproveQueue(id: string) {
    if (!userId) return;
    setApprovingId(id);
    try {
      await approveDeptQueueItem(businessId, deptType, id, userId);
      await load();
    } finally {
      setApprovingId(null);
    }
  }

  async function handleRejectQueue() {
    if (!rejectId || !userId) return;
    setRejectingId(rejectId);
    try {
      await rejectDeptQueueItem(businessId, deptType, rejectId, userId, rejectReason);
      setRejectId(null);
      setRejectReason("");
      await load();
    } finally {
      setRejectingId(null);
    }
  }

  async function handleApproveTask(taskId: string) {
    await approveTask(taskId);
    await load();
  }

  async function handleRejectTask(taskId: string, reason: string) {
    await rejectTask(taskId, reason);
    await load();
  }

  async function handleDeleteTask(taskId: string) {
    await deleteTask(taskId);
    await load();
  }

  function handleTaskUpdated(updated: Task) {
    setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.push(`/dashboard/business/${businessId}/agents`)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors mb-2 inline-block"
        >
          {t("backToAgents")}
        </button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {dept?.label_color && (
              <span
                className="h-3 w-3 rounded-full shrink-0"
                style={{ backgroundColor: dept.label_color }}
              />
            )}
            <h1 className="text-xl font-semibold">{dept?.name ?? deptType}</h1>
          </div>
          <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
            <span>{t("lastRun")}: {timeAgo(dept?.last_run_at ?? null)}</span>
            <span>{t("nextEval")}: {timeUntil(dept?.manager_next_eval_at ?? null)}</span>
            <span>{t("todayCost")}: ${dept?.today_cost_usd?.toFixed(4) ?? "0.0000"}</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Narrative */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              {t("narrative")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dept?.status_narrative ? (
              <p className="text-sm text-muted-foreground leading-relaxed">{dept.status_narrative}</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">{t("narrativeEmpty")}</p>
            )}
          </CardContent>
        </Card>

        {/* Manager Chat */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3 shrink-0">
            <CardTitle className="text-sm flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              {t("chatTitle")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col flex-1 gap-3 min-h-0">
            <div className="flex-1 overflow-y-auto space-y-2 max-h-64 pr-1">
              {chatHistory.length === 0 && (
                <p className="text-xs text-muted-foreground italic text-center py-4">—</p>
              )}
              {chatHistory.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {chatBusy && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg px-3 py-2">
                    <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Input
                className="h-8 text-xs"
                placeholder={t("chatPlaceholder")}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleChat(); }}
                disabled={chatBusy}
              />
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0 shrink-0"
                onClick={handleChat}
                disabled={!chatInput.trim() || chatBusy}
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approvals */}
      {queue.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold">{t("pendingApprovals")}</h2>
          {queue.map((item) => (
            <Card key={item.id}>
              <CardContent className="py-3 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-xs font-medium">{item.action_type.replace(/_/g, " ")}</p>
                  <p className="text-[10px] text-muted-foreground">{new Date(item.created_at).toLocaleString()}</p>
                </div>
                {rejectId === item.id ? (
                  <div className="flex items-center gap-2 shrink-0">
                    <Input
                      className="h-7 text-xs w-40"
                      placeholder={t("rejectReason")}
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") handleRejectQueue(); if (e.key === "Escape") setRejectId(null); }}
                      autoFocus
                    />
                    <Button
                      size="sm"
                      variant="destructive"
                      className="h-7 text-xs px-2"
                      onClick={handleRejectQueue}
                      disabled={rejectingId === item.id}
                    >
                      {rejectingId === item.id ? <Loader2 className="h-3 w-3 animate-spin" /> : t("reject")}
                    </Button>
                    <button onClick={() => setRejectId(null)} className="text-muted-foreground hover:text-foreground">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      size="sm"
                      className="h-7 text-xs px-3"
                      onClick={() => handleApproveQueue(item.id)}
                      disabled={approvingId === item.id}
                    >
                      {approvingId === item.id ? (
                        <><Loader2 className="h-3 w-3 mr-1 animate-spin" />{t("approving")}</>
                      ) : (
                        <><CheckCircle2 className="h-3 w-3 mr-1" />{t("approve")}</>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs px-3"
                      onClick={() => setRejectId(item.id)}
                    >
                      {t("reject")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Task Board */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold">{t("taskBoard")}</h2>
        <TaskBoard
          tasks={tasks}
          onApprove={handleApproveTask}
          onReject={handleRejectTask}
          onDelete={handleDeleteTask}
          onUpdated={handleTaskUpdated}
          onRan={load}
        />
      </div>
    </div>
  );
}
