import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Building2, Users, Bell, Plus, ArrowRight } from "lucide-react";
import { getTranslations, getLocale } from "next-intl/server";

async function getBusinesses(userId: string) {
  const supabase = await createClient();
  const { data } = await supabase
    .from("businesses")
    .select("id, name, status, created_at")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });
  return data ?? [];
}

async function getDashboardStats(userId: string) {
  const supabase = await createClient();
  const { data: bizData } = await supabase
    .from("businesses")
    .select("id")
    .eq("user_id", userId)
    .eq("status", "active");
  const bizIds = (bizData ?? []).map((b: { id: string }) => b.id);

  if (bizIds.length === 0) return { agents: 0, pendingApprovals: 0 };

  const { count: agentCount } = await supabase
    .from("agents")
    .select("id", { count: "exact", head: true })
    .in("business_id", bizIds)
    .eq("is_active", true);

  const { count: approvalCount } = await supabase
    .from("activity_log")
    .select("id", { count: "exact", head: true })
    .in("business_id", bizIds)
    .eq("requires_approval", true)
    .is("approved_at", null);

  return { agents: agentCount ?? 0, pendingApprovals: approvalCount ?? 0 };
}

const statusColors: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  onboarding: "secondary",
  paused: "outline",
  archived: "outline",
};

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  const businesses = user ? await getBusinesses(user.id) : [];
  const stats = user ? await getDashboardStats(user.id) : { agents: 0, pendingApprovals: 0 };
  const t = await getTranslations("dashboard");
  const locale = await getLocale();

  if (businesses.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 text-center">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold">{t("welcome")}</h1>
          <p className="text-muted-foreground max-w-md">{t("welcomeSubtitle")}</p>
        </div>
        <Button size="lg" render={<Link href="/onboarding" />} nativeButton={false}>
          <Plus className="mr-2 h-4 w-4" />
          {t("createFirstBusiness")}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button size="sm" render={<Link href="/onboarding" />} nativeButton={false}>
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          {t("newBusiness")}
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <Building2 className="h-3.5 w-3.5" /> {t("businesses")}
            </CardDescription>
            <CardTitle className="text-2xl">{businesses.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <Users className="h-3.5 w-3.5" /> {t("activeAgents")}
            </CardDescription>
            <CardTitle className="text-2xl">{stats.agents}</CardTitle>
          </CardHeader>
        </Card>
        <Card className={stats.pendingApprovals > 0 ? "border-yellow-500/50" : ""}>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <Bell className="h-3.5 w-3.5" /> {t("pendingApprovals")}
            </CardDescription>
            <CardTitle className={`text-2xl ${stats.pendingApprovals > 0 ? "text-yellow-600" : ""}`}>
              {stats.pendingApprovals}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="space-y-3">
        <h2 className="text-sm font-medium">{t("yourBusinesses")}</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {businesses.map((biz) => (
            <Card key={biz.id} className="group hover:border-primary/50 transition-colors">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base line-clamp-1">{biz.name}</CardTitle>
                  <Badge variant={statusColors[biz.status] ?? "outline"} className="text-[10px] capitalize ml-2 shrink-0">
                    {biz.status}
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  {new Date(biz.created_at).toLocaleDateString(locale)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-between text-xs"
                  render={<Link href={`/dashboard/business/${biz.id}`} />}
                  nativeButton={false}
                >
                  {t("viewBusiness")}
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
