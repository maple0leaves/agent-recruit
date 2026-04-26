import { useJDTemplates } from "@/hooks/useJDs";
import type { JDTemplate } from "@/types/jd";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface TemplateSelectorProps {
  onSelect: (template: JDTemplate | null) => void;
  selectedName?: string;
}

export default function TemplateSelector({
  onSelect,
  selectedName,
}: TemplateSelectorProps) {
  const { data: templates, isLoading } = useJDTemplates();

  if (isLoading) {
    return <p className="text-muted-foreground text-center py-8">加载模板中...</p>;
  }

  if (!templates || templates.length === 0) {
    return <p className="text-muted-foreground text-center py-8">暂无可用模板</p>;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <Card
            key={template.name}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedName === template.name
                ? "ring-2 ring-primary border-primary"
                : ""
            }`}
            onClick={() => onSelect(template)}
          >
            <CardHeader>
              <CardTitle className="text-base">{template.name}</CardTitle>
              <p className="text-xs text-muted-foreground">
                {template.description}
              </p>
            </CardHeader>
            <CardContent className="space-y-1 text-sm">
              <p>
                <span className="text-muted-foreground">技能：</span>
                {template.skills}
              </p>
              <p>
                <span className="text-muted-foreground">经验：</span>
                {template.experience_years}年
              </p>
              <p>
                <span className="text-muted-foreground">学历：</span>
                {template.education}
              </p>
              <p>
                <span className="text-muted-foreground">薪资：</span>
                {template.salary_min}-{template.salary_max}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="text-center">
        <Button
          variant="ghost"
          onClick={() => onSelect(null)}
        >
          跳过模板，手动填写
        </Button>
      </div>
    </div>
  );
}
