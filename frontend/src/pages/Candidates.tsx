import { Card, CardContent } from "../components/ui/card";
import { Users } from "lucide-react";

export default function Candidates() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 py-12">
          <Users className="h-12 w-12 text-muted-foreground" />
          <h2 className="text-xl font-semibold">候选人</h2>
          <p className="text-sm text-muted-foreground">功能开发中，敬请期待</p>
        </CardContent>
      </Card>
    </div>
  );
}
