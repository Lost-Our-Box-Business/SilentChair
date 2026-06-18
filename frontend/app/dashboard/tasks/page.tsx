import { ListTodo } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function TasksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Tasks</h1>
        <p className="text-sm text-muted-foreground">Track work in progress across all your businesses</p>
      </div>
      <Card className="border-dashed">
        <CardHeader className="items-center text-center pb-2">
          <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-2">
            <ListTodo className="h-6 w-6 text-muted-foreground" />
          </div>
          <CardTitle className="text-base">Task tracking coming soon</CardTitle>
          <CardDescription className="text-xs max-w-sm">
            A cross-business task queue showing what agents are working on, queued next, and recently completed.
          </CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </div>
  );
}
