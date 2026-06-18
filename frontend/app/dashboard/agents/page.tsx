import { Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Agents</h1>
        <p className="text-sm text-muted-foreground">View and manage your AI workforce across all businesses</p>
      </div>
      <Card className="border-dashed">
        <CardHeader className="items-center text-center pb-2">
          <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-2">
            <Users className="h-6 w-6 text-muted-foreground" />
          </div>
          <CardTitle className="text-base">Agent management coming soon</CardTitle>
          <CardDescription className="text-xs max-w-sm">
            A unified view of all active agents across your businesses — roles, status, recent actions, and model usage.
          </CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </div>
  );
}
