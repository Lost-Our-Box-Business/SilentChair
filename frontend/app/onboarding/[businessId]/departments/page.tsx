"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { suggestDepartments, activateDepartments, type DepartmentSuggestion } from "@/lib/hiring-api";
import { createClient } from "@/lib/supabase/client";
import { CheckCircle2, Circle, Users, Wrench, ArrowRight, Loader2 } from "lucide-react";

export default function DepartmentsPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const [departments, setDepartments] = useState<DepartmentSuggestion[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const { data: business } = await supabase
        .from("businesses")
        .select("profile")
        .eq("id", businessId)
        .single();

      if (!business?.profile) {
        setError("Business profile not found.");
        setLoading(false);
        return;
      }

      try {
        const res = await suggestDepartments(businessId, business.profile);
        setDepartments(res.departments);
        const required = new Set(res.departments.filter((d) => d.is_required).map((d) => d.dept_type));
        setSelected(required);
      } catch {
        setError("Failed to load department suggestions.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [businessId]);

  function toggleDept(deptType: string, isRequired: boolean) {
    if (isRequired) return;
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(deptType) ? next.delete(deptType) : next.add(deptType);
      return next;
    });
  }

  async function handleContinue() {
    setSaving(true);
    try {
      await activateDepartments(businessId, Array.from(selected));
      router.push(`/onboarding/${businessId}/tools`);
    } catch {
      setError("Failed to save selections. Please try again.");
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-44 rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Build your team</h1>
        <p className="text-muted-foreground">
          Select the departments you want to hire for. Required departments are pre-selected.
          Each department comes with a specialist manager agent.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        {departments.map((dept) => {
          const isSelected = selected.has(dept.dept_type);
          return (
            <button
              key={dept.dept_type}
              onClick={() => toggleDept(dept.dept_type, dept.is_required)}
              className={`text-left rounded-xl border-2 p-5 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                isSelected
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/40"
              } ${dept.is_required ? "cursor-default" : "cursor-pointer"}`}
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  {isSelected
                    ? <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
                    : <Circle className="h-5 w-5 text-muted-foreground shrink-0" />
                  }
                  <h3 className="font-semibold text-sm">{dept.name}</h3>
                </div>
                {dept.is_required && (
                  <Badge variant="secondary" className="text-[10px] shrink-0">Required</Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed mb-4">{dept.description}</p>
              <div className="space-y-2 border-t pt-3">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Users className="h-3.5 w-3.5" />
                  <span className="font-medium text-foreground">{dept.manager_title}</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{dept.manager_description}</p>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-2">
                  <Wrench className="h-3.5 w-3.5 shrink-0" />
                  <span>{dept.tools.map((t) => t.display_name).join(", ")}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex items-center justify-between pt-2">
        <p className="text-sm text-muted-foreground">
          {selected.size} department{selected.size !== 1 ? "s" : ""} selected
        </p>
        <Button onClick={handleContinue} disabled={selected.size === 0 || saving}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {saving ? "Hiring managers…" : "Continue to tools"}
          {!saving && <ArrowRight className="ml-2 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
