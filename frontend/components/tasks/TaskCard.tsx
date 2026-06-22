"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import type { Task } from "@/lib/tasks-api";

interface Props {
  task: Task;
  onApprove?: (id: string) => Promise<void>;
  onReject?: (id: string, reason: string) => Promise<void>;
  businessName?: string;
}

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

export function TaskCard({ task, onApprove, onReject, businessName }: Props) {
  const [approving, setApproving] = useState(false);
  const [approveDone, setApproveDone] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [rejectDone, setRejectDone] = useState(false);

  const isBlocked = task.status === "awaiting_approval";
  const isFailed = task.status === "failed";
  const isCompleted = task.status === "completed";

  async function handleApprove() {
    if (!onApprove || approving) return;
    setApproving(true);
    try {
      await onApprove(task.id);
      setApproveDone(true);
    } finally {
      setApproving(false);
    }
  }

  async function handleReject() {
    if (!onReject || rejecting || !rejectReason.trim()) return;
    setRejecting(true);
    try {
      await onReject(task.id, rejectReason.trim());
      setRejectDone(true);
      setRejectOpen(false);
    } finally {
      setRejecting(false);
    }
  }

  const actionsBusy = approveDone || rejectDone;

  return (
    <Card
      className={`text-sm transition-colors ${
        isBlocked && !actionsBusy ? "border-amber-500/60 bg-amber-500/5" : ""
      } ${isFailed ? "border-red-500/40 bg-red-500/5" : ""}`}
    >
      <CardContent className="p-3 space-y-2">
        {/* Top row: dept label + time */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 min-w-0">
            {task.label_color && (
              <span
                className="h-2 w-2 rounded-full shrink-0"
                style={{ backgroundColor: task.label_color }}
              />
            )}
            {task.department && (
              <span className="text-[10px] text-muted-foreground truncate">
                {task.department}
              </span>
            )}
            {task.created_by === "user" && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground shrink-0">
                Manual
              </span>
            )}
          </div>
          <span className="text-[10px] text-muted-foreground shrink-0 tabular-nums">
            {timeAgo(task.created_at)}
          </span>
        </div>

        {/* Business name (global view) */}
        {businessName && (
          <p className="text-[10px] text-muted-foreground">{businessName}</p>
        )}

        {/* Title */}
        <p className={`font-medium leading-snug ${isFailed ? "text-red-600 dark:text-red-400" : ""}`}>
          {task.title}
        </p>

        {/* Rejection reason */}
        {isFailed && task.output?.startsWith("Rejected:") && (
          <p className="text-[10px] text-muted-foreground italic">{task.output}</p>
        )}

        {/* Cost on completed tasks */}
        {isCompleted && task.cost_usd > 0 && (
          <p className="text-[10px] text-muted-foreground font-mono">
            {formatCost(task.cost_usd)}
          </p>
        )}

        {/* Approve / Reject actions on blocked tasks */}
        {isBlocked && !actionsBusy && (
          <>
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
                  <Button
                    size="sm"
                    variant="destructive"
                    className="h-7 text-xs flex-1"
                    onClick={handleReject}
                    disabled={!rejectReason.trim() || rejecting}
                  >
                    {rejecting && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
                    Confirm reject
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs"
                    onClick={() => { setRejectOpen(false); setRejectReason(""); }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex gap-1.5">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs flex-1 border-amber-500/60 hover:bg-amber-500/10"
                  onClick={handleApprove}
                  disabled={approving}
                >
                  {approving && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
                  {approving ? "Approving…" : "Approve & send"}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 text-xs text-muted-foreground hover:text-red-600 hover:bg-red-500/10"
                  onClick={() => setRejectOpen(true)}
                >
                  Reject
                </Button>
              </div>
            )}
          </>
        )}

        {/* Feedback after action */}
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
      </CardContent>
    </Card>
  );
}
