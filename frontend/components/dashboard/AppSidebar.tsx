"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LayoutDashboard, Building2, Users, ListTodo, BarChart3, Settings, ChevronsUpDown, LogOut, Plus, Globe, KanbanSquare, UserRound } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useTranslations } from "next-intl";

interface AppSidebarProps {
  userEmail?: string;
  businesses?: { id: string; name: string }[];
}

export function AppSidebar({ userEmail, businesses = [] }: AppSidebarProps) {
  const t = useTranslations("sidebar");
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createClient();

  const navItems = [
    { href: "/dashboard", label: t("overview"), icon: LayoutDashboard },
    { href: "/dashboard/business", label: t("business"), icon: Building2 },
    { href: "/dashboard/agents", label: t("agents"), icon: Users },
    { href: "/dashboard/tasks", label: t("tasks"), icon: ListTodo },
    { href: "/dashboard/analytics", label: t("analytics"), icon: BarChart3 },
    { href: "/dashboard/settings", label: t("settings"), icon: Settings },
  ];

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/auth/login");
  }

  const initials = userEmail ? userEmail[0].toUpperCase() : "U";

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
            <span className="text-primary-foreground text-xs font-bold">SC</span>
          </div>
          <span className="font-semibold text-sm">SilentChair</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{t("workspace")}</SidebarGroupLabel>
          <SidebarMenu>
            {navItems.map(({ href, label, icon: Icon }) => (
              <SidebarMenuItem key={href}>
                <SidebarMenuButton isActive={pathname === href} onClick={() => router.push(href)}>
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>{t("businesses")}</SidebarGroupLabel>
          <SidebarMenu>
            {businesses.map((biz) => (
              <SidebarMenuItem key={biz.id}>
                <SidebarMenuButton
                  isActive={pathname.startsWith(`/dashboard/business/${biz.id}`)}
                  onClick={() => router.push(`/dashboard/business/${biz.id}`)}
                >
                  <Building2 className="h-4 w-4" />
                  <span className="truncate">{biz.name}</span>
                </SidebarMenuButton>
                {pathname.startsWith(`/dashboard/business/${biz.id}`) && (
                  <SidebarMenuSub>
                    <SidebarMenuSubItem>
                      <SidebarMenuSubButton
                        isActive={pathname === `/dashboard/business/${biz.id}/tasks`}
                        onClick={() => router.push(`/dashboard/business/${biz.id}/tasks`)}
                      >
                        <KanbanSquare className="h-3.5 w-3.5" />
                        <span>{t("subTasks")}</span>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                    <SidebarMenuSubItem>
                      <SidebarMenuSubButton
                        isActive={pathname === `/dashboard/business/${biz.id}/website`}
                        onClick={() => router.push(`/dashboard/business/${biz.id}/website`)}
                      >
                        <Globe className="h-3.5 w-3.5" />
                        <span>{t("subWebsite")}</span>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                    <SidebarMenuSubItem>
                      <SidebarMenuSubButton
                        isActive={pathname === `/dashboard/business/${biz.id}/coach`}
                        onClick={() => router.push(`/dashboard/business/${biz.id}/coach`)}
                      >
                        <UserRound className="h-3.5 w-3.5" />
                        <span>{t("subCoach")}</span>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  </SidebarMenuSub>
                )}
              </SidebarMenuItem>
            ))}
            <SidebarMenuItem>
              <SidebarMenuButton onClick={() => router.push("/onboarding")}>
                <Plus className="h-4 w-4" />
                <span>{t("newBusiness")}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex w-full items-center gap-2 rounded-md p-2 text-sm hover:bg-muted transition-colors outline-none">
            <Avatar className="h-6 w-6">
              <AvatarFallback className="text-[10px]">{initials}</AvatarFallback>
            </Avatar>
            <span className="flex-1 truncate text-left text-xs">{userEmail}</span>
            <ChevronsUpDown className="h-3 w-3 text-muted-foreground" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={handleSignOut} className="text-xs">
              <LogOut className="mr-2 h-3 w-3" />
              {t("signOut")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
