import Link from "next/link";
import { User, CreditCard, Bell, Link2, BarChart3 } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getTranslations } from "next-intl/server";

export default async function SettingsPage() {
  const t = await getTranslations("settings");

  const sections = [
    {
      href: "/dashboard/settings/profile",
      icon: User,
      title: t("profile"),
      description: t("profileDesc"),
    },
    {
      href: "/dashboard/settings/billing",
      icon: CreditCard,
      title: t("billing"),
      description: t("billingDesc"),
      badge: "Phase 5",
    },
    {
      href: "/dashboard/settings/notifications",
      icon: Bell,
      title: t("notifications"),
      description: t("notificationsDesc"),
      badge: "Phase 8",
    },
    {
      href: "/dashboard/settings/connected-accounts",
      icon: Link2,
      title: t("connectedAccounts"),
      description: t("connectedAccountsDesc"),
      badge: "Phase 8",
    },
    {
      href: "/dashboard/analytics",
      icon: BarChart3,
      title: t("analytics"),
      description: t("analyticsDesc"),
      badge: "Post-V1",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {sections.map(({ href, icon: Icon, title, description, badge }) => (
          <Link key={href} href={href}>
            <Card className="h-full transition-colors hover:bg-muted/50 cursor-pointer">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center shrink-0">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  {badge && (
                    <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                      {badge}
                    </span>
                  )}
                </div>
                <CardTitle className="text-sm mt-2">{title}</CardTitle>
                <CardDescription className="text-xs">{description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
