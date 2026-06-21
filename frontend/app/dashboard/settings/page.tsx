import Link from "next/link";
import { User, CreditCard, Bell, Link2, BarChart3 } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const sections = [
  {
    href: "/dashboard/settings/profile",
    icon: User,
    title: "Profile",
    description: "Name, language preference, and timezone.",
  },
  {
    href: "/dashboard/settings/billing",
    icon: CreditCard,
    title: "Billing",
    description: "Subscription plan, AI spend balance, and top-ups.",
    badge: "Phase 5",
  },
  {
    href: "/dashboard/settings/notifications",
    icon: Bell,
    title: "Notifications",
    description: "Control when and how you're alerted for approvals.",
    badge: "Phase 8",
  },
  {
    href: "/dashboard/settings/connected-accounts",
    icon: Link2,
    title: "Connected Accounts",
    description: "OAuth connections for social and ad platforms.",
    badge: "Phase 8",
  },
  {
    href: "/dashboard/analytics",
    icon: BarChart3,
    title: "Analytics",
    description: "Aggregated performance across all businesses.",
    badge: "Post-V1",
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Account, billing, and notification preferences</p>
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
