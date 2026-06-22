"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import { Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TaskBoard } from "@/components/tasks/TaskBoard";
import { getTasks, createTask, approveTask, rejectTask, type Task } from "@/lib/tasks-api";

const DEPARTMENTS = ["Marketing", "Lead Generation", "Client Acquisition", "Other"];

export default function BusinessTasksPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newDept, setNewDept] = useState("");
  const [creating, setCreating] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  const loadTasks = useCallback(async () => {
    try {
      const data = await getTasks(businessId);
      setTasks(data);
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  useEffect(() => {
    if (dialogOpen) setTimeout(() => titleRef.current?.focus(), 50);
  }, [dialogOpen]);

  async function handleApprove(taskId: string) {
    await approveTask(taskId);
    await loadTasks();
  }

  async function handleReject(taskId: string, reason: string) {
    await rejectTask(taskId, reason);
    await loadTasks();
  }

  async function handleCreate() {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await createTask(businessId, {
        title: newTitle.trim(),
        description: newDesc.trim() || undefined,
        department: newDept || undefined,
      });
      setDialogOpen(false);
      setNewTitle("");
      setNewDesc("");
      setNewDept("");
      await loadTasks();
    } finally {
      setCreating(false);
    }
  }

  function closeDialog() {
    setDialogOpen(false);
    setNewTitle("");
    setNewDept("");
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Task Board</h1>
        <p className="text-sm text-muted-foreground">
          Pipeline runs, approvals, and manual tasks for this business
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <TaskBoard
          tasks={tasks}
          onApprove={handleApprove}
          onReject={handleReject}
          onAddTask={() => setDialogOpen(true)}
        />
      )}

      {/* Add Task modal */}
      {dialogOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={(e) => { if (e.target === e.currentTarget) closeDialog(); }}
        >
          <div className="bg-background border rounded-lg shadow-lg w-full max-w-sm mx-4 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Add Task</h2>
              <button onClick={closeDialog} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <Input
                ref={titleRef}
                placeholder="Task title"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Escape") closeDialog(); }}
              />
              <textarea
                placeholder="Description (optional)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground"
              />
              <select
                value={newDept}
                onChange={(e) => setNewDept(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">Department (optional)</option>
                {DEPARTMENTS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={closeDialog}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleCreate} disabled={!newTitle.trim() || creating}>
                {creating && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                Create
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
