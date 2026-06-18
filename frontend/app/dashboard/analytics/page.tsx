import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">Performance metrics and insights across your businesses</p>
      </div>
      <Card className="border-dashed">
        <CardHeader className="items-center text-center pb-2">
          <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-2">
            <BarChart3 className="h-6 w-6 text-muted-foreground" />
          </div>
          <CardTitle className="text-base">Analytics coming soon</CardTitle>
          <CardDescription className="text-xs max-w-sm">
            Aggregated reporting on pipeline runs, content published, leads generated, revenue tracked, and agent costs.
          </CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </div>
  );
}
