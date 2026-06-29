import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import PipelineActions from "./PipelineActions";
import { useCandidate, useUpdateCandidate } from "@/hooks/useCandidates";
import type { Candidate, CandidateUpdate } from "@/types/candidate";
import { ArrowLeft, Edit2, X, Clock, Search, Trash2 } from "lucide-react";

interface CandidateDetailProps {
  candidateId: number;
  onBack: () => void;
  onDelete?: (candidate: Candidate) => void;
}

function InfoField({
  label,
  value,
  multiline,
}: {
  label: string;
  value: string;
  multiline?: boolean;
}) {
  const isEmpty =
    !value ||
    value === "未填写" ||
    value === "未提取" ||
    value === "未解析";

  return (
    <div>
      <dt className="text-sm font-medium text-muted-foreground mb-1">
        {label}
      </dt>
      <dd
        className={`text-sm ${
          multiline ? "whitespace-pre-wrap" : ""
        } ${
          isEmpty ? "text-muted-foreground italic" : ""
        }`}
      >
        {value || "暂无"}
      </dd>
    </div>
  );
}

function InlineEditForm({
  candidate,
  onSave,
  onCancel,
}: {
  candidate: Candidate;
  onSave: (values: CandidateUpdate) => Promise<void>;
  onCancel: () => void;
}) {
  const [formValues, setFormValues] = useState<CandidateUpdate>({
    name: candidate.name,
    email: candidate.email,
    phone: candidate.phone,
    skills: candidate.skills,
    education: candidate.education,
    experience: candidate.experience,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onSave(formValues);
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateField = (field: keyof CandidateUpdate, value: string) => {
    setFormValues((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-2">
        <Label>姓名</Label>
        <Input
          value={formValues.name || ""}
          onChange={(e) => updateField("name", e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label>邮箱</Label>
        <Input
          value={formValues.email || ""}
          onChange={(e) => updateField("email", e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label>电话</Label>
        <Input
          value={formValues.phone || ""}
          onChange={(e) => updateField("phone", e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label>技能</Label>
        <Input
          value={formValues.skills || ""}
          onChange={(e) => updateField("skills", e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label>教育</Label>
        <Input
          value={formValues.education || ""}
          onChange={(e) => updateField("education", e.target.value)}
        />
      </div>
      <div className="md:col-span-2 space-y-2">
        <Label>工作经历</Label>
        <Textarea
          value={formValues.experience || ""}
          onChange={(e) => updateField("experience", e.target.value)}
          rows={5}
        />
      </div>
      <div className="flex justify-end gap-2 md:col-span-2">
        <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
          取消
        </Button>
        <Button onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? "保存中..." : "保存"}
        </Button>
      </div>
    </div>
  );
}

export default function CandidateDetail({
  candidateId,
  onBack,
  onDelete,
}: CandidateDetailProps) {
  const { data: candidate, isLoading, isError } = useCandidate(candidateId);
  const updateMutation = useUpdateCandidate();
  const [isEditing, setIsEditing] = useState(false);
  const navigate = useNavigate();

  const handleSave = async (values: CandidateUpdate) => {
    try {
      await updateMutation.mutateAsync({ id: candidateId, data: values });
      setIsEditing(false);
    } catch {
      // Error handled by mutation
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-24" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-8 w-full" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (isError || !candidate) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <p className="text-muted-foreground">候选人不存在</p>
        <Button variant="outline" onClick={onBack}>
          返回列表
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Button variant="ghost" onClick={onBack} className="gap-2">
        <ArrowLeft className="h-4 w-4" /> 返回列表
      </Button>

      {/* Section 1: Parsed Data Area (D-12) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>基本信息</CardTitle>
          <div className="flex items-center gap-2">
            {onDelete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={() => onDelete(candidate)}
                className="gap-2"
              >
                <Trash2 className="h-4 w-4" /> 删除
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
              className="gap-2"
            >
              {isEditing ? (
                <>
                  <X className="h-4 w-4" /> 取消编辑
                </>
              ) : (
                <>
                  <Edit2 className="h-4 w-4" /> 编辑
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isEditing ? (
            <InlineEditForm
              candidate={candidate}
              onSave={handleSave}
              onCancel={() => setIsEditing(false)}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <InfoField label="姓名" value={candidate.name} />
              <InfoField label="邮箱" value={candidate.email || "未填写"} />
              <InfoField label="电话" value={candidate.phone || "未填写"} />
              <InfoField label="技能" value={candidate.skills || "未提取"} />
              <InfoField label="教育" value={candidate.education || "未提取"} />
              <InfoField
                label="解析时间"
                value={
                  candidate.parsed_at
                    ? new Date(candidate.parsed_at).toLocaleString("zh-CN")
                    : "未解析"
                }
              />
              <div className="md:col-span-2">
                <InfoField
                  label="工作经历"
                  value={candidate.experience || "未提取"}
                  multiline
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Separator between sections */}
      <Separator />

      {/* Section 2: Match History Area (D-13 placeholder) */}
      <Card>
        <CardHeader>
          <CardTitle>匹配历史</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Clock className="h-8 w-8 mb-2" />
            <p className="text-sm">暂无匹配记录</p>
            <p className="text-xs mt-1">
              匹配 JD 后将在此处显示评分和历史记录
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Separator */}
      <Separator />

      {/* Section 3: Pipeline Status Area (D-12) */}
      <Card>
        <CardHeader>
          <CardTitle>流程状态</CardTitle>
        </CardHeader>
        <CardContent>
          <PipelineActions
            currentStatus={candidate.status}
            candidateId={candidate.id}
            onStatusChanged={() => {
              // The useCandidate queryKey ["candidates", id] will be invalidated
              // by useUpdateCandidateStatus's onSuccess
            }}
          />
        </CardContent>
      </Card>

      {/* Separator */}
      <Separator />

      {/* Section 4: Reverse Matching (D-01) */}
      <Card>
        <CardHeader>
          <CardTitle>反向匹配</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            查找与候选人技能匹配的职位
          </p>
          <Button
            variant="default"
            className="gap-2"
            onClick={() => navigate(`/matching?candidateId=${candidateId}`)}
          >
            <Search className="h-4 w-4" />
            反向匹配
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
