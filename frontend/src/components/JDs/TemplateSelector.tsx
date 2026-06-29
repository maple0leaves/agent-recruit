import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useJDTemplates } from "@/hooks/useJDs";
import type { JDTemplate } from "@/types/jd";
import {
  BriefcaseBusiness,
  Check,
  Clock3,
  GraduationCap,
  Sparkles,
  WalletCards,
} from "lucide-react";

interface TemplateSelectorProps {
  onSelect: (template: JDTemplate | null) => void;
  selectedName?: string;
}

function formatSalary(template: JDTemplate) {
  if (template.salary_min === 0 && template.salary_max === 0) return "面议";
  return `${template.salary_min.toLocaleString()}-${template.salary_max.toLocaleString()}`;
}

export default function TemplateSelector({
  onSelect,
  selectedName,
}: TemplateSelectorProps) {
  const { data: templates, isLoading } = useJDTemplates();

  if (isLoading) {
    return (
      <div className="rounded-lg border border-dashed bg-muted/30 py-12 text-center text-sm text-muted-foreground">
        正在加载 JD 模板...
      </div>
    );
  }

  if (!templates || templates.length === 0) {
    return (
      <div className="rounded-lg border border-dashed bg-muted/30 py-12 text-center text-sm text-muted-foreground">
        暂无可用模板
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-5">
      <div className="shrink-0 rounded-lg border bg-muted/30 p-4">
        <div className="flex items-start gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="size-4" />
          </div>
          <div className="min-w-0 space-y-1">
            <h3 className="text-base font-medium leading-none">从模板快速创建 JD</h3>
            <p className="text-sm text-muted-foreground">
              选择最接近的岗位模板后可以继续编辑字段，也可以跳过模板直接手动填写。
            </p>
          </div>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 auto-rows-fr grid-cols-1 gap-3 overflow-y-auto pr-1 md:grid-cols-3">
        {templates.map((template) => {
          const selected = selectedName === template.name;

          return (
            <button
              key={template.name}
              type="button"
              className={[
                "group relative flex h-full min-h-[320px] flex-col rounded-lg border bg-card p-4 text-left text-card-foreground transition-all md:min-h-0",
                "hover:-translate-y-0.5 hover:border-foreground/25 hover:shadow-lg focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/40 focus-visible:outline-none",
                selected ? "border-primary ring-2 ring-primary/40" : "border-border",
              ].join(" ")}
              onClick={() => onSelect(template)}
            >
              {selected && (
                <span className="absolute right-3 top-3 flex size-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <Check className="size-3.5" />
                </span>
              )}

              <div className="mb-4 flex items-start gap-3 pr-8">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                  <BriefcaseBusiness className="size-4" />
                </div>
                <div className="min-w-0 space-y-1">
                  <h4 className="line-clamp-2 text-base font-semibold leading-snug">
                    {template.name}
                  </h4>
                  <p className="line-clamp-3 text-sm leading-5 text-muted-foreground">
                    {template.description}
                  </p>
                </div>
              </div>

              <div className="mb-4 flex flex-1 content-start flex-wrap gap-1.5 overflow-hidden">
                {template.skills
                  .split(/[,，、]/)
                  .map((skill) => skill.trim())
                  .filter(Boolean)
                  .slice(0, 14)
                  .map((skill) => (
                    <Badge key={skill} variant="secondary" className="max-w-full">
                      <span className="truncate">{skill}</span>
                    </Badge>
                  ))}
              </div>

              <div className="mt-auto grid gap-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock3 className="size-4" />
                  <span>{template.experience_years} 年经验</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <GraduationCap className="size-4" />
                  <span>{template.education}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <WalletCards className="size-4" />
                  <span>{formatSalary(template)}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-auto flex shrink-0 justify-center border-t pt-4">
        <Button variant="outline" onClick={() => onSelect(null)}>
          跳过模板，手动填写
        </Button>
      </div>
    </div>
  );
}
