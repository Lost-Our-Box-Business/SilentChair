"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { TaskBoard } from "@/components/tasks/TaskBoard";
import { getGlobalTasks, approveTask, rejectTask, type Task } from "@/lib/tasks-api";
import { createClient } from "@/lib/supabase/client";

export default function GlobalTasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);
  const [bizFilter, setBizFilter] = useState<string>("all");

  const loadTasks = useCallback(async (uid: string) => {
    try {
      const all = await getGlobalTasks(uid);
      setTasks(all);
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) {
        setUserId(data.user.id);
        loadTasks(data.user.id);
      } else {
        setLoading(false);
      }
    });
  }, [loadTasks]);

  async function reload() {
    if (userId) await loadTasks(userId);
  }

  async function handleApprove(taskId: string) {
    await approveTask(taskId);
    await reload();
  }

  async function handleReject(taskId: string, reason: string) {
    await rejectTask(taskId, reason);
    await reload();
  }

  function handleUpdated(updated: Task) {
    setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  }

  const businesses = Array.from(
    new Map(
      tasks
        .filter((t) => t.businesses?.name)
        .map((t) => [t.business_id, t.businesses!.name])
    ).entries()
  );

  const filtered =
    bizFilter === "all" ? tasks : tasks.filter((t) => t.business_id === bizFilter);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Tasks</h1>
          <p className="text-sm text-muted-foreground">All pipeline work across your businesses</p>
        </div>
        {businesses.length > 1 && (
          <select
            value={bizFilter}
            onChange={(e) => setBizFilter(e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="all">All businesses</option>
            {businesses.map(([id, name]) => (
              <option key={id} value={id}>{name}</option>
            ))}
          </select>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <TaskBoard
          tasks={filtered}
          onApprove={handleApprove}
          onReject={handleReject}
          onUpdated={handleUpdated}
          onRan={reload}
          showBusiness={bizFilter === "all" && businesses.length > 1}
        />
      )}
    </div>
  );
}
