import { Card, CardContent } from "../components/ui/card";
import { LayoutDashboard } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 py-12">
          <LayoutDashboard className="h-12 w-12 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Dashboard</h2>
          <p className="text-sm text-muted-foreground">功能开发中，敬请期待</p>
        </CardContent>
      </Card>
    </div>
  );
}
