"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getStaffSuggestions, hireStaff, type StaffRole } from "@/lib/hiring-api";
import { createClient } from "@/lib/supabase/client";
import { CheckCircle2, Circle, ArrowRight, Loader2, Users } from "lucide-react";

type DeptWithStaff = {
  id: string;
  dept_type: string;
  name: string;
  staff: StaffRole[];
  selected: Set<string>;
};

export default function StaffPage() {
  const { businessId } = useParams<{ businessId: string }>();
  const router = useRouter();
  const [departments, setDepartments] = useState<DeptWithStaff[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const { data: depts } = await supabase
        .from("departments")
        .select("id, dept_type, name")
        .eq("business_id", businessId)
        .eq("is_active", true);

      if (!depts) { setLoading(false); return; }

      const results = await Promise.all(
        depts.map(async (dept: { id: string; dept_type: string; name: string }) => {
          const staff = await getStaffSuggestions(dept.dept_type).catch(() => []);
          return {
            ...dept,
            staff,
            selected: new Set<string>(staff.map((s: StaffRole) => s.role)),
          };
        })
      );
      setDepartments(results);
      setLoading(false);
    }
    load();
  }, [businessId]);

  function toggleRole(deptId: string, role: string) {
    setDepartments((prev) =>
      prev.map((d) => {
        if (d.id !== deptId) return d;
        const next = new Set(d.selected);
        next.has(role) ? next.delete(role) : next.add(role);
        return { ...d, selected: next };
      })
    );
  }

  async function handleContinue() {
    setSaving(true);
    try {
      await Promise.all(
        departments.map((dept) =>
          hireStaff(businessId, dept.id, Array.from(dept.selected))
        )
      );
      router.push(`/onboarding/${businessId}/launch`);
    } catch {
      setError("Failed to hire staff. Please try again.");
      setSaving(false);
    }
  }

  const totalSelected = departments.reduce((sum, d) => sum + d.selected.size, 0);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-4 w-96" />
        {[...Array(2)].map((_, i) => <Skeleton key={i} className="h-48 rounded-xl" />)}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Hire your staff</h1>
        <p className="text-muted-foreground">
          Your managers have recommended these specialist roles. All are selected by default —
          deselect any you don't want to hire.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="space-y-6">
        {departments.map((dept) => (
          <div key={dept.id} className="space-y-3">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold">{dept.name} Department</h2>
              <Badge variant="outline" className="text-[10px]">
                {dept.selected.size} / {dept.staff.length} hired
              </Badge>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {dept.staff.map((role) => {
                const isSelected = dept.selected.has(role.role);
                return (
                  <button
                    key={role.role}
                    onClick={() => toggleRole(dept.id, role.role)}
                    className={`text-left rounded-lg border-2 p-4 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                      isSelected
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/40"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      {isSelected
                        ? <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                        : <Circle className="h-4 w-4 text-muted-foreground shrink-0" />
                      }
                      <span className="text-sm font-medium">{role.role}</span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed pl-6">
                      {role.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2">
        <p className="text-sm text-muted-foreground">
          {totalSelected} staff member{totalSelected !== 1 ? "s" : ""} selected
        </p>
        <Button onClick={handleContinue} disabled={saving}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {saving ? "Hiring staff…" : "Continue to launch"}
          {!saving && <ArrowRight className="ml-2 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
