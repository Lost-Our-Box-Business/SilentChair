"use client";

import { useState, useMemo } from "react";
import { Plus } from "lucide-react";
import { TaskCard } from "./TaskCard";
import { DepartmentFilter } from "./DepartmentFilter";
import type { Task, TaskStatus } from "@/lib/tasks-api";

const COLUMNS: { id: TaskStatus | "failed"; label: string; amber?: boolean }[] = [
  { id: "planned", label: "Planned" },
  { id: "in_progress", label: "In Progress" },
  { id: "awaiting_approval", label: "Blocked by User", amber: true },
  { id: "completed", label: "Completed" },
];

interface Props {
  tasks: Task[];
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string, reason: string) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  onAddTask?: () => void;
  showBusiness?: boolean;
}

export function TaskBoard({ tasks, onApprove, onReject, onDelete, onAddTask, showBusiness = false }: Props) {
  const [selectedDept, setSelectedDept] = useState<string | null>(null);

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
        {COLUMNS.map((col) => {
          const colTasks = filtered.filter((t) =>
            col.id === "completed"
              ? t.status === "completed" || t.status === "failed"
              : t.status === col.id
          );

          return (
            <div key={col.id} className="space-y-2">
              {/* Column header */}
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
                    title="Add task"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              {/* Cards */}
              {colTasks.length === 0 ? (
                <p className="text-[11px] text-muted-foreground/50 text-center py-6">
                  Empty
                </p>
              ) : (
                colTasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onApprove={col.id === "awaiting_approval" ? onApprove : undefined}
                    onReject={col.id === "awaiting_approval" ? onReject : undefined}
                    onDelete={onDelete}
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
