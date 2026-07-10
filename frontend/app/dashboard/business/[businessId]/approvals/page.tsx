"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Loader2, CheckSquare, Clock, AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ApprovalReviewSheet } from "@/components/tasks/ApprovalReviewSheet";
import { getTasks, approveTask, rejectTask, type Task } from "@/lib/tasks-api";

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function PendingCard({ task, onDone }: { task: Task; onDone: () => void }) {
  const [reviewOpen, setReviewOpen] = useState(false);

  async function handleApprove(id: string) {
    await approveTask(id);
    onDone();
  }

  async function handleReject(id: string, reason: string) {
    await rejectTask(id, reason);
    onDone();
  }

  const deptLabel = task.department?.replace(/_/g, " ") ?? "";

  return (
    <>
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="py-3 px-4 flex items-center gap-4">
          <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium leading-snug truncate">{task.title}</p>
            <div className="flex items-center gap-2 mt-0.5">
              {deptLabel && (
                <Badge variant="outline" className="text-[10px] px-1 py-0">
                  {deptLabel}
                </Badge>
              )}
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {timeAgo(task.created_at)}
              </span>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 text-xs border-amber-500/40 hover:bg-amber-500/10"
            onClick={() => setReviewOpen(true)}
          >
            Review
          </Button>
        </CardContent>
      </Card>
      <ApprovalReviewSheet
        open={reviewOpen}
        onOpenChange={setReviewOpen}
        task={task}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </>
  );
}

export default function ApprovalsPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await getTasks(businessId, { status: "awaiting_approval" });
      setTasks(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => { load(); }, [load]);

  // Poll every 15 seconds
  useEffect(() => {
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <CheckSquare className="h-5 w-5 text-muted-foreground" />
            Pending Approvals
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Actions your agents are waiting on you to review before proceeding.
          </p>
        </div>
        {tasks.length > 0 && (
          <span className="text-sm font-medium bg-amber-500/10 text-amber-600 border border-amber-500/20 rounded-full px-2.5 py-0.5">
            {tasks.length} pending
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 py-12 justify-center text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Loading…</span>
        </div>
      ) : tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <CheckSquare className="h-10 w-10 text-green-500/60 mb-3" />
          <p className="text-sm font-medium">All caught up</p>
          <p className="text-xs text-muted-foreground mt-1">No actions are awaiting your review.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <PendingCard key={task.id} task={task} onDone={load} />
          ))}
        </div>
      )}
    </div>
  );
}
