"use client";

import { useState, useMemo } from "react";
import { Plus } from "lucide-react";
import { useTranslations } from "next-intl";
import { TaskCard } from "./TaskCard";
import { DepartmentFilter } from "./DepartmentFilter";
import type { Task, TaskStatus } from "@/lib/tasks-api";

interface Props {
  tasks: Task[];
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string, reason: string) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  onUpdated?: (updated: Task) => void;
  onRan?: () => void;
  onAddTask?: () => void;
  availableDepartments?: string[];
  showBusiness?: boolean;
}

export function TaskBoard({ tasks, onApprove, onReject, onDelete, onUpdated, onRan, onAddTask, availableDepartments, showBusiness = false }: Props) {
  const t = useTranslations("taskBoard");
  const [selectedDept, setSelectedDept] = useState<string | null>(null);

  const columns: { id: TaskStatus | "failed"; label: string; amber?: boolean }[] = [
    { id: "planned", label: t("planned") },
    { id: "in_progress", label: t("inProgress") },
    { id: "awaiting_approval", label: t("blockedByUser"), amber: true },
    { id: "completed", label: t("completed") },
  ];

  const departments = useMemo(() => {
    const seen = new Set<string>();
    tasks.forEach((t) => { if (t.department) seen.add(t.department); });
    return Array.from(seen).sort();
  }, [tasks]);

  const filtered = selectedDept
    ? tasks.filter((t) => t.department === selectedDept)
    : tasks;

  return (
    <div className="space-y-4">
      <DepartmentFilter
        departments={departments}
        selected={selectedDept}
        onChange={setSelectedDept}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-start">
        {columns.map((col) => {
          const colTasks = filtered.filter((task) =>
            col.id === "completed"
              ? task.status === "completed" || task.status === "failed"
              : task.status === col.id
          );

          return (
            <div key={col.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3
                    className={`text-xs font-semibold uppercase tracking-wide ${
                      col.amber ? "text-amber-600 dark:text-amber-400" : "text-muted-foreground"
                    }`}
                  >
                    {col.label}
                  </h3>
                  <span className="text-[10px] text-muted-foreground tabular-nums">
                    {colTasks.length}
                  </span>
                </div>
                {col.id === "planned" && onAddTask && (
                  <button
                    onClick={onAddTask}
                    className="h-5 w-5 flex items-center justify-center rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    title={t("taskTitle")}
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              {colTasks.length === 0 ? (
                <p className="text-[11px] text-muted-foreground/50 text-center py-6">
                  {t("empty")}
                </p>
              ) : (
                colTasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onApprove={col.id === "awaiting_approval" ? onApprove : undefined}
                    onReject={col.id === "awaiting_approval" ? onReject : undefined}
                    onDelete={onDelete}
                    onUpdated={onUpdated}
                    onRan={onRan}
                    availableDepartments={availableDepartments}
                    businessName={showBusiness ? task.businesses?.name : undefined}
                  />
                ))
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
