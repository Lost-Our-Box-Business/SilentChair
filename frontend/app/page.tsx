import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Bot, Zap, BarChart3 } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
              <span className="text-primary-foreground text-xs font-bold">SC</span>
            </div>
            <span className="font-semibold text-sm">SilentChair</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" render={<Link href="/auth/login" />} nativeButton={false}>
              Sign in
            </Button>
            <Button size="sm" render={<Link href="/auth/login" />} nativeButton={false}>
              Get started
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-24 space-y-24">
        <section className="text-center space-y-6 max-w-3xl mx-auto">
          <Badge variant="secondary" className="text-xs">Now in early access</Badge>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-tight">
            Your business, run by<br />
            <span className="text-primary">an AI workforce</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto">
            Describe the business you want to build. SilentChair hires AI managers and staff,
            gives them the tools they need, and puts them to work — while you stay in control.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Button size="lg" render={<Link href="/auth/login" />} nativeButton={false}>
              Build your business
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </section>

        <section className="grid sm:grid-cols-3 gap-6">
          {[
            {
              icon: Bot,
              title: "Hire your team",
              description: "Tell us your business idea. An AI analyst interviews you and recommends the right departments and managers — all experts in their field.",
            },
            {
              icon: Zap,
              title: "Set it in motion",
              description: "Managers request the tools they need. We provide access and handle billing. Your agents start working with full context of your goals.",
            },
            {
              icon: BarChart3,
              title: "Stay in control",
              description: "Choose how autonomous your business runs — from fully hands-off to step-by-step approvals. Get updates via email, Slack, or Discord.",
            },
          ].map(({ icon: Icon, title, description }) => (
            <div key={title} className="rounded-xl border p-6 space-y-3">
              <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold text-sm">{title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t mt-24">
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-center">
          <p className="text-xs text-muted-foreground">© 2026 SilentChair</p>
        </div>
      </footer>
    </div>
  );
}
