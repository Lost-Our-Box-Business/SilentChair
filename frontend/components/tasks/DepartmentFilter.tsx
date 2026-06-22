"use client";

interface Props {
  departments: string[];
  selected: string | null;
  onChange: (dept: string | null) => void;
}

export function DepartmentFilter({ departments, selected, onChange }: Props) {
  if (departments.length === 0) return null;

  const all = ["All", ...departments];

  return (
    <div className="flex gap-1.5 flex-wrap">
      {all.map((dept) => {
        const isActive = dept === "All" ? selected === null : selected === dept;
        return (
          <button
            key={dept}
            onClick={() => onChange(dept === "All" ? null : dept)}
            className={`text-xs px-3 py-1 rounded-full border transition-colors focus-visible:outline-none ${
              isActive
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:border-primary/50 hover:text-foreground"
            }`}
          >
            {dept}
          </button>
        );
      })}
    </div>
  );
}
