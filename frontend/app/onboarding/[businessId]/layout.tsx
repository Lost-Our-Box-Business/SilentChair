import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

const STEPS = [
  { label: "Departments", path: "departments" },
  { label: "Tools", path: "tools" },
  { label: "Staff", path: "staff" },
  { label: "Launch", path: "launch" },
  { label: "Website", path: "website" },
];

export default async function WizardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ businessId: string }>;
}) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/auth/login");

  const { businessId } = await params;

  const { data: business } = await supabase
    .from("businesses")
    .select("name")
    .eq("id", businessId)
    .single();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
              <span className="text-primary-foreground text-xs font-bold">SC</span>
            </div>
            <span className="text-sm font-medium text-muted-foreground">
              Setting up{business?.name ? ` — ${business.name}` : ""}
            </span>
          </div>
          <nav className="hidden sm:flex items-center gap-1">
            {STEPS.map((step, i) => (
              <div key={step.path} className="flex items-center gap-1">
                {i > 0 && <div className="w-6 h-px bg-border" />}
                <span className="text-xs text-muted-foreground px-2 py-1">{step.label}</span>
              </div>
            ))}
          </nav>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-6 py-10">{children}</main>
    </div>
  );
}
