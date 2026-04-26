import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { JDTemplate } from "@/types/jd";

const EDUCATION_OPTIONS = ["高中", "大专", "本科", "硕士", "博士", "不限"] as const;

const jdFormSchema = z
  .object({
    title: z.string().min(1, "职位名称不能为空").max(200),
    department: z.string().min(1, "部门不能为空").max(100),
    skills: z.string().min(1, "技能要求不能为空"),
    experience_years: z.coerce.number().int().min(0, "工作经验不能为负数"),
    education: z.string().min(1, "请选择学历要求"),
    salary_min: z.coerce.number().int().min(0, "最低薪资不能为负数"),
    salary_max: z.coerce.number().int().min(0, "最高薪资不能为负数"),
    description: z.string().optional().default(""),
  })
  .refine((data) => data.salary_max >= data.salary_min, {
    message: "最高薪资不能低于最低薪资",
    path: ["salary_max"],
  });

type FormValues = z.infer<typeof jdFormSchema>;

interface JDFormProps {
  defaultValues?: Partial<FormValues>;
  templateValues?: JDTemplate | null;
  onSubmit: (values: FormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
  mode: "create" | "edit";
}

export default function JDForm({
  defaultValues,
  templateValues,
  onSubmit,
  onCancel,
  isSubmitting = false,
  mode,
}: JDFormProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(jdFormSchema) as any,
    defaultValues: {
      title: templateValues?.name || defaultValues?.title || "",
      department: defaultValues?.department || "",
      skills: templateValues?.skills || defaultValues?.skills || "",
      experience_years:
        templateValues?.experience_years ?? defaultValues?.experience_years ?? 0,
      education: templateValues?.education || defaultValues?.education || "本科",
      salary_min: templateValues?.salary_min ?? defaultValues?.salary_min ?? 0,
      salary_max: templateValues?.salary_max ?? defaultValues?.salary_max ?? 0,
      description: templateValues?.description || defaultValues?.description || "",
    },
  });

  // Reset form when templateValues change (e.g., template selected)
  useEffect(() => {
    if (templateValues) {
      form.reset({
        title: templateValues.name || defaultValues?.title || "",
        department: defaultValues?.department || "",
        skills: templateValues.skills || defaultValues?.skills || "",
        experience_years: templateValues.experience_years ?? defaultValues?.experience_years ?? 0,
        education: templateValues.education || defaultValues?.education || "本科",
        salary_min: templateValues.salary_min ?? defaultValues?.salary_min ?? 0,
        salary_max: templateValues.salary_max ?? defaultValues?.salary_max ?? 0,
        description: templateValues.description || defaultValues?.description || "",
      });
    }
  }, [templateValues, form.reset, defaultValues]);

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit(values);
  });

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  职位名称 <span className="text-red-500">*</span>
                </FormLabel>
                <FormControl>
                  <Input placeholder="例如：高级前端工程师" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="department"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  部门 <span className="text-red-500">*</span>
                </FormLabel>
                <FormControl>
                  <Input placeholder="例如：技术部" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="experience_years"
            render={({ field }) => (
              <FormItem>
                <FormLabel>工作经验（年）</FormLabel>
                <FormControl>
                  <Input type="number" min={0} placeholder="例如：3" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="education"
            render={({ field }) => (
              <FormItem>
                <FormLabel>学历要求</FormLabel>
                <Select
                  value={field.value}
                  onValueChange={field.onChange}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="选择学历要求" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {EDUCATION_OPTIONS.map((opt) => (
                      <SelectItem key={opt} value={opt}>
                        {opt}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="salary_min"
            render={({ field }) => (
              <FormItem>
                <FormLabel>最低薪资（元/月）</FormLabel>
                <FormControl>
                  <Input type="number" min={0} placeholder="例如：15000" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="salary_max"
            render={({ field }) => (
              <FormItem>
                <FormLabel>最高薪资（元/月）</FormLabel>
                <FormControl>
                  <Input type="number" min={0} placeholder="例如：30000" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="skills"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                技能要求 <span className="text-red-500">*</span>
              </FormLabel>
              <FormControl>
                <Input placeholder="例如：Java, Python, React, Docker" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>职位描述</FormLabel>
              <FormControl>
                <Textarea
                  rows={5}
                  placeholder="请填写详细的职位描述..."
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={onCancel}>
            取消
          </Button>
          <Button type="submit" disabled={isSubmitting} className="gap-2">
            {isSubmitting ? "保存中..." : mode === "create" ? "创建" : "保存"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
