import { Settings } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Account, billing, and notification preferences</p>
      </div>
      <Card className="border-dashed">
        <CardHeader className="items-center text-center pb-2">
          <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-2">
            <Settings className="h-6 w-6 text-muted-foreground" />
          </div>
          <CardTitle className="text-base">Settings coming soon</CardTitle>
          <CardDescription className="text-xs max-w-sm">
            Profile management, notification preferences, billing, and API key management will live here.
          </CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </div>
  );
}
