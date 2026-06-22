"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Loader2, CheckCircle2, XCircle, ChevronDown, Trash2, Pencil,
  Play, ArrowRight, SquareCheck,
} from "lucide-react";
import { updateTask, runTask, setTaskStatus, type Task, type TaskStatus } from "@/lib/tasks-api";
import { ApprovalDetail } from "./ApprovalDetail";

interface Props {
  task: Task;
  onApprove?: (id: string) => Promise<void>;
  onReject?: (id: string, reason: string) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  onUpdated?: (updated: Task) => void;
  onRan?: () => void;        // called after a successful Run Now so the page can refresh
  availableDepartments?: string[];
  businessName?: string;
}

const STATUS_FLOW: TaskStatus[] = ["planned", "in_progress", "completed"];

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function formatCost(n: number): string {
  if (!n || n === 0) return "";
  if (n < 0.001) return `$${n.toFixed(6)}`;
  if (n < 0.01) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(4)}`;
}

export function TaskCard({
  task,
  onApprove, onReject, onDelete, onUpdated, onRan,
  availableDepartments = [],
  businessName,
}: Props) {
  const [expanded, setExpanded] = useState(task.status === "awaiting_approval");
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [editDesc, setEditDesc] = useState(task.description ?? "");
  const [editDept, setEditDept] = useState(task.department ?? "");
  const [saving, setSaving] = useState(false);

  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const [movingTo, setMovingTo] = useState<TaskStatus | null>(null);

  const [approving, setApproving] = useState(false);
  const [approveDone, setApproveDone] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [rejectDone, setRejectDone] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isBlocked = task.status === "awaiting_approval";
  const isFailed = task.status === "failed";
  const isCompleted = task.status === "completed";
  const isPlanned = task.status === "planned";
  const isInProgress = task.status === "in_progress";
  const actionsBusy = approveDone || rejectDone;

  const isAgentTask = task.assigned_to === "agent";
  const isUserTask = task.assigned_to === "user";
  const canEdit = task.created_by === "user";

  // Status movement for user-assigned tasks
  const currentIdx = STATUS_FLOW.indexOf(task.status as TaskStatus);
  const nextStatus = currentIdx >= 0 && currentIdx < STATUS_FLOW.length - 1 ? STATUS_FLOW[currentIdx + 1] : null;

  const STATUS_LABELS: Record<string, string> = {
    planned: "Planned",
    in_progress: "In Progress",
    completed: "Complete",
  };

  async function handleSave(e: React.MouseEvent) {
    e.stopPropagation();
    if (!editTitle.trim() || saving) return;
    setSaving(true);
    try {
      const updated = await updateTask(task.id, {
        title: editTitle.trim(),
        description: editDesc.trim() || undefined,
        department: editDept || undefined,
      });
      onUpdated?.(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  function handleCancelEdit(e: React.MouseEvent) {
    e.stopPropagation();
    setEditTitle(task.title);
    setEditDesc(task.description ?? "");
    setEditDept(task.department ?? "");
    setEditing(false);
  }

  async function handleRunNow(e: React.MouseEvent) {
    e.stopPropagation();
    if (running) return;
    setRunning(true);
    setRunError(null);
    try {
      await runTask(task.id);
      onRan?.();
    } catch (err) {
      setRunError(err instanceof Error ? err.message : "Pipeline error");
    } finally {
      setRunning(false);
    }
  }

  async function handleMoveStatus(e: React.MouseEvent, status: TaskStatus) {
    e.stopPropagation();
    if (movingTo) return;
    setMovingTo(status);
    try {
      const updated = await setTaskStatus(task.id, status);
      onUpdated?.(updated);
    } finally {
      setMovingTo(null);
    }
  }

  async function handleApprove() {
    if (!onApprove || approving) return;
    setApproving(true);
    try { await onApprove(task.id); setApproveDone(true); }
    finally { setApproving(false); }
  }

  async function handleReject() {
    if (!onReject || rejecting || !rejectReason.trim()) return;
    setRejecting(true);
    try { await onReject(task.id, rejectReason.trim()); setRejectDone(true); setRejectOpen(false); }
    finally { setRejecting(false); }
  }

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!onDelete || deleting) return;
    setDeleting(true);
    try { await onDelete(task.id); }
    finally { setDeleting(false); }
  }

  return (
    <div
      onClick={() => { if (!editing) setExpanded((v) => !v); }}
      className={`rounded-lg border bg-card text-card-foreground shadow-sm text-sm cursor-pointer transition-colors
        ${isBlocked && !actionsBusy ? "border-amber-400 bg-amber-50/60 dark:bg-amber-950/20" : "border-border"}
        ${isFailed ? "border-red-400/60 bg-red-50/60 dark:bg-red-950/20" : ""}
      `}
    >
      <div className="p-3 space-y-2">

        {/* ── Edit mode ────────────────────────────────────────────────── */}
        {editing ? (
          <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
            <Input
              className="h-8 text-sm"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="Task title"
              autoFocus
            />
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground"
              rows={3}
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              placeholder="Description (optional)"
            />
            <select
              value={editDept}
              onChange={(e) => setEditDept(e.target.value)}
              className="w-full h-8 rounded-md border border-input bg-background px-3 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">No department</option>
              {availableDepartments.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            <div className="flex gap-1.5 justify-end">
              <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={handleCancelEdit}>
                Cancel
              </Button>
              <Button size="sm" className="h-7 text-xs" onClick={handleSave} disabled={!editTitle.trim() || saving}>
                {saving && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
                Save
              </Button>
            </div>
          </div>

        ) : (
          <>
            {/* ── Top row ──────────────────────────────────────────────── */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 min-w-0">
                {task.label_color && (
                  <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: task.label_color }} />
                )}
                {task.department && (
                  <span className="text-[10px] text-muted-foreground truncate">{task.department}</span>
                )}
                {task.created_by === "user" && isUserTask && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 shrink-0">Mine</span>
                )}
                {task.created_by === "user" && isAgentTask && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground shrink-0">Agent</span>
                )}
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-[10px] text-muted-foreground tabular-nums">{timeAgo(task.created_at)}</span>
                <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${expanded ? "rotate-180" : ""}`} />
              </div>
            </div>

            {/* Business name (global view) */}
            {businessName && <p className="text-[10px] text-muted-foreground">{businessName}</p>}

            {/* Title */}
            <p className={`font-medium leading-snug ${isFailed ? "text-red-600 dark:text-red-400" : ""}`}>
              {task.title}
            </p>

            {/* ── Run Now (agent-assigned planned tasks only) ───────────── */}
            {isAgentTask && isPlanned && (
              <div onClick={(e) => e.stopPropagation()}>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs w-full"
                  onClick={handleRunNow}
                  disabled={running}
                >
                  {running
                    ? <><Loader2 className="h-3 w-3 mr-1.5 animate-spin" />Running pipeline…</>
                    : <><Play className="h-3 w-3 mr-1.5" />Run now</>
                  }
                </Button>
                {runError && (
                  <p className="text-[10px] text-red-600 mt-1">{runError}</p>
                )}
              </div>
            )}

            {/* ── User-assigned status movement ─────────────────────────── */}
            {isUserTask && (isPlanned || isInProgress) && nextStatus && (
              <div onClick={(e) => e.stopPropagation()}>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs w-full"
                  onClick={(e) => handleMoveStatus(e, nextStatus)}
                  disabled={!!movingTo}
                >
                  {movingTo
                    ? <><Loader2 className="h-3 w-3 mr-1.5 animate-spin" />Moving…</>
                    : nextStatus === "in_progress"
                      ? <><ArrowRight className="h-3 w-3 mr-1.5" />Start working</>
                      : <><SquareCheck className="h-3 w-3 mr-1.5" />Mark complete</>
                  }
                </Button>
              </div>
            )}

            {/* ── Expanded: description + edit/delete ──────────────────── */}
            {expanded && (
              <div className="border-t pt-2 mt-1 space-y-2" onClick={(e) => e.stopPropagation()}>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {task.description || <span className="italic">No description</span>}
                </p>
                <div className="flex items-center gap-3">
                  {canEdit && !isCompleted && !isFailed && (
                    <button
                      onClick={(e) => { e.stopPropagation(); setEditing(true); setExpanded(false); }}
                      className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <Pencil className="h-3 w-3" /> Edit
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={handleDelete}
                      disabled={deleting}
                      className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-red-600 transition-colors"
                    >
                      {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                      Delete
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Cost on completed */}
            {isCompleted && task.cost_usd > 0 && (
              <p className="text-[10px] text-muted-foreground font-mono">{formatCost(task.cost_usd)}</p>
            )}

            {/* Rejection reason */}
            {isFailed && task.output?.startsWith("Rejected:") && (
              <p className="text-[10px] text-muted-foreground italic">{task.output}</p>
            )}

            {/* ── Work preview (Blocked by User) ───────────────────────── */}
            {isBlocked && !actionsBusy && task.activity_log_id && expanded && (
              <div className="border-t pt-2 mt-1">
                <ApprovalDetail activityLogId={task.activity_log_id} />
              </div>
            )}

            {/* ── Approve / Reject (Blocked by User column) ────────────── */}
            {isBlocked && !actionsBusy && (
              <div onClick={(e) => e.stopPropagation()}>
                {rejectOpen ? (
                  <div className="space-y-1.5">
                    <Input
                      className="h-7 text-xs"
                      placeholder="Reason for rejection"
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") handleReject(); if (e.key === "Escape") setRejectOpen(false); }}
                      autoFocus
                    />
                    <div className="flex gap-1.5">
                      <Button size="sm" variant="destructive" className="h-7 text-xs flex-1"
                        onClick={handleReject} disabled={!rejectReason.trim() || rejecting}>
                        {rejecting && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
                        Confirm reject
                      </Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs"
                        onClick={() => { setRejectOpen(false); setRejectReason(""); }}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-1.5">
                    <Button size="sm" variant="outline"
                      className="h-7 text-xs flex-1 border-amber-400 hover:bg-amber-500/10"
                      onClick={handleApprove} disabled={approving}>
                      {approving && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
                      {approving ? "Approving…" : "Approve & send"}
                    </Button>
                    <Button size="sm" variant="ghost"
                      className="h-7 text-xs text-muted-foreground hover:text-red-600 hover:bg-red-500/10"
                      onClick={() => setRejectOpen(true)}>
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            )}

            {approveDone && (
              <p className="text-[11px] text-green-600 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Approved
              </p>
            )}
            {rejectDone && (
              <p className="text-[11px] text-red-600 flex items-center gap-1">
                <XCircle className="h-3 w-3" /> Rejected
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
