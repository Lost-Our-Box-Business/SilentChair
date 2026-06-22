"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import { Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TaskBoard } from "@/components/tasks/TaskBoard";
import { useTranslations } from "next-intl";
import {
  getTasks, createTask, approveTask, rejectTask, deleteTask,
  getBusinessDepartments, type Task,
} from "@/lib/tasks-api";

const DEPARTMENTS = ["Marketing", "Lead Generation", "Client Acquisition", "Other"];

export default function BusinessTasksPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const t = useTranslations("taskBoardPage");
  const tBoard = useTranslations("taskBoard");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newDept, setNewDept] = useState("");
  const [newAssignee, setNewAssignee] = useState<"agent" | "user">("agent");
  const [creating, setCreating] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  const loadTasks = useCallback(async () => {
    try {
      const [data, depts] = await Promise.all([
        getTasks(businessId),
        getBusinessDepartments(businessId),
      ]);
      setTasks(data);
      setDepartments(depts.length > 0 ? depts : DEPARTMENTS);
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

  async function handleDelete(taskId: string) {
    await deleteTask(taskId);
    await loadTasks();
  }

  function handleUpdated(updated: Task) {
    setTasks((prev) => prev.map((task) => (task.id === updated.id ? updated : task)));
  }

  async function handleCreate() {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await createTask(businessId, {
        title: newTitle.trim(),
        description: newDesc.trim() || undefined,
        department: newDept || undefined,
        assigned_to: newAssignee,
      });
      closeDialog();
      await loadTasks();
    } finally {
      setCreating(false);
    }
  }

  function closeDialog() {
    setDialogOpen(false);
    setNewTitle("");
    setNewDesc("");
    setNewDept("");
    setNewAssignee("agent");
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
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
          onDelete={handleDelete}
          onUpdated={handleUpdated}
          onRan={loadTasks}
          onAddTask={() => setDialogOpen(true)}
          availableDepartments={departments}
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
              <h2 className="text-sm font-semibold">{t("addTaskTitle")}</h2>
              <button onClick={closeDialog} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <Input
                ref={titleRef}
                placeholder={tBoard("taskTitle")}
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Escape") closeDialog(); }}
              />
              <textarea
                placeholder={tBoard("descriptionOptional")}
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
                <option value="">{t("departmentOptional")}</option>
                {departments.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>

              {/* Assignee toggle */}
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">{t("assignTo")}</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setNewAssignee("agent")}
                    className={`flex-1 h-8 rounded-md border text-xs font-medium transition-colors ${
                      newAssignee === "agent"
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-input bg-background text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    {tBoard("agentLabel")}
                  </button>
                  <button
                    type="button"
                    onClick={() => setNewAssignee("user")}
                    className={`flex-1 h-8 rounded-md border text-xs font-medium transition-colors ${
                      newAssignee === "user"
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-input bg-background text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    {t("me")}
                  </button>
                </div>
                <p className="text-[10px] text-muted-foreground">
                  {newAssignee === "agent" ? t("agentHint") : t("meHint")}
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={closeDialog}>
                {tBoard("cancel")}
              </Button>
              <Button size="sm" onClick={handleCreate} disabled={!newTitle.trim() || creating}>
                {creating && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                {t("create")}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
