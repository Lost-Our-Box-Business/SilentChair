"use client";

import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import { ApprovalDetail } from "./ApprovalDetail";
import { getApprovalContent, type Task } from "@/lib/tasks-api";
import type { ActivityDetail } from "@/lib/activity-api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task;
  onApprove?: (id: string) => Promise<void>;
  onReject?: (id: string, reason: string) => Promise<void>;
}

export function ApprovalReviewSheet({ open, onOpenChange, task, onApprove, onReject }: Props) {
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<ActivityDetail | null>(null);
  const [actionType, setActionType] = useState<string>("");

  const [declining, setDeclining] = useState(false);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [approving, setApproving] = useState(false);
  const [done, setDone] = useState<"approved" | "declined" | null>(null);

  useEffect(() => {
    if (!open) {
      setDetail(null);
      setDeclining(false);
      setReason("");
      setDone(null);
      return;
    }
    setLoading(true);
    getApprovalContent(task.id)
      .then((res) => {
        setActionType(res.action_type ?? task.title);
        setDetail(res.payload as ActivityDetail);
      })
      .catch(() => setDetail({}))
      .finally(() => setLoading(false));
  }, [open, task.id, task.title]);

  async function handleApprove() {
    if (!onApprove || approving) return;
    setApproving(true);
    try {
      await onApprove(task.id);
      setDone("approved");
      setTimeout(() => onOpenChange(false), 1200);
    } finally {
      setApproving(false);
    }
  }

  async function handleDecline() {
    if (!onReject || submitting || !reason.trim()) return;
    setSubmitting(true);
    try {
      await onReject(task.id, reason.trim());
      setDone("declined");
      setTimeout(() => onOpenChange(false), 1200);
    } finally {
      setSubmitting(false);
    }
  }

  const hasContent =
    detail &&
    ((detail.outreach_emails?.length ?? 0) > 0 ||
      (detail.edited_articles?.length ?? 0) > 0 ||
      (detail.qualified_leads?.length ?? 0) > 0);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl flex flex-col gap-0 p-0">
        <SheetHeader className="px-6 py-4 border-b shrink-0">
          <div className="flex items-center gap-2 flex-wrap">
            <Eye className="h-4 w-4 text-amber-500 shrink-0" />
            <SheetTitle className="text-base leading-snug">{actionType || task.title}</SheetTitle>
            {task.department && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                {task.department.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading work…
            </div>
          ) : done === "approved" ? (
            <div className="flex items-center gap-2 text-green-600 text-sm">
              <CheckCircle2 className="h-4 w-4" /> Approved — the agent will proceed.
            </div>
          ) : done === "declined" ? (
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <XCircle className="h-4 w-4" /> Declined — the agent will retry with your notes.
            </div>
          ) : hasContent ? (
            <ApprovalDetail detail={detail!} />
          ) : (
            <p className="text-sm text-muted-foreground">
              The agent completed this task but produced no reviewable content.
              Approve to confirm, or decline with notes to have it try again.
            </p>
          )}
        </div>

        {!done && !loading && (
          <SheetFooter className="px-6 py-4 border-t shrink-0 flex flex-col gap-3">
            {declining ? (
              <>
                <Textarea
                  placeholder="Describe what should be different (e.g. 'make subject lines more specific', 'focus on SaaS companies only')…"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  className="text-sm resize-none"
                  autoFocus
                />
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    className="flex-1"
                    onClick={handleDecline}
                    disabled={!reason.trim() || submitting}
                  >
                    {submitting && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                    Submit Decline
                  </Button>
                  <Button variant="ghost" onClick={() => { setDeclining(false); setReason(""); }}>
                    Cancel
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex gap-2">
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                  onClick={handleApprove}
                  disabled={approving}
                >
                  {approving && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                  Approve
                </Button>
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setDeclining(true)}
                >
                  Decline
                </Button>
              </div>
            )}
          </SheetFooter>
        )}
      </SheetContent>
    </Sheet>
  );
}
