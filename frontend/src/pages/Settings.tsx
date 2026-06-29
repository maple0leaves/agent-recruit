import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Database,
  KeyRound,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  Server,
  Settings as SettingsIcon,
  Shield,
  SlidersHorizontal,
  UserRound,
} from "lucide-react";
import apiClient, { getApiBaseURL } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  DEFAULT_PREFERENCES,
  clampMatchCandidateLimit,
  readPreferences,
  writePreferences,
  type LocalPreferences,
} from "@/lib/preferences";
import { useAuthStore } from "@/store/authStore";

const text = {
  accountApi: "\u4e1a\u52a1 API",
  accountInfo: "\u8d26\u6237\u4fe1\u606f",
  accountInfoDesc: "\u5f53\u524d\u767b\u5f55\u7528\u6237\u4e0e\u8fde\u63a5\u4fe1\u606f\u3002",
  aiService: "Python AI \u670d\u52a1",
  aiServiceDesc: "\u8d1f\u8d23\u7b80\u5386\u89e3\u6790\u3001\u5019\u9009\u4eba\u5339\u914d\u3001Skills \u548c AI \u5de5\u4f5c\u6d41\u3002",
  backend: "Java \u4e1a\u52a1\u540e\u7aef",
  backendDesc: "\u8d1f\u8d23\u767b\u5f55\u3001JD\u3001\u5019\u9009\u4eba\u3001\u5339\u914d\u5386\u53f2\u548c\u5bfc\u51fa\u63a5\u53e3\u3002",
  cancel: "\u53d6\u6d88",
  checkRunning: "\u68c0\u67e5\u4e2d",
  confirmNewPassword: "\u786e\u8ba4\u65b0\u5bc6\u7801",
  confirmRebuild: "\u786e\u8ba4\u91cd\u5efa",
  currentUser: "\u7528\u6237\u540d",
  defaultUser: "\u7528\u6237",
  defaultRole: "\u7ba1\u7406\u5458",
  error: "\u5f02\u5e38",
  healthDesc: "\u68c0\u67e5 Java \u4e1a\u52a1\u540e\u7aef\u548c Python AI \u670d\u52a1\u662f\u5426\u53ef\u7528\u3002",
  healthTitle: "\u670d\u52a1\u72b6\u6001",
  localPref: "\u672c\u673a\u504f\u597d",
  localPrefDesc: "\u8fd9\u4e9b\u8bbe\u7f6e\u4fdd\u5b58\u5728\u5f53\u524d\u6d4f\u89c8\u5668\uff0c\u9002\u5408\u4e2a\u4eba\u5de5\u4f5c\u4e60\u60ef\u3002",
  maintenanceDesc: "\u7528\u4e8e\u4fee\u590d\u68c0\u7d22\u7d22\u5f15\u548c\u6392\u67e5\u670d\u52a1\u72b6\u6001\u3002",
  maintenanceTip: "\u4e0a\u4f20\u6216\u6279\u91cf\u89e3\u6790\u7b80\u5386\u540e\uff0c\u5982\u667a\u80fd\u5339\u914d\u641c\u4e0d\u5230\u65b0\u5019\u9009\u4eba\uff0c\u53ef\u4ee5\u91cd\u5efa\u5019\u9009\u4eba\u7d22\u5f15\u3002",
  maintenanceTitle: "\u7ef4\u62a4\u5de5\u5177",
  matchCandidateLimit: "\u667a\u80fd\u5339\u914d\u4eba\u6570",
  matchCandidateLimitDesc: "\u63a7\u5236\u6bcf\u6b21\u4ece\u5019\u9009\u4eba\u5e93\u4e2d\u53ec\u56de\u5e76\u8bc4\u5206\u7684\u4eba\u6570\uff0c\u9ed8\u8ba4 5 \u4f4d\u3002",
  mismatchPassword: "\u4e24\u6b21\u8f93\u5165\u7684\u65b0\u5bc6\u7801\u4e0d\u4e00\u81f4",
  newPassword: "\u65b0\u5bc6\u7801",
  normal: "\u6b63\u5e38",
  oldPassword: "\u539f\u5bc6\u7801",
  passwordChanged: "\u5bc6\u7801\u4fee\u6539\u6210\u529f",
  passwordDesc: "\u5efa\u8bae\u5b9a\u671f\u66f4\u65b0\u7ba1\u7406\u5458\u5bc6\u7801\u3002",
  passwordLength: "\u65b0\u5bc6\u7801\u957f\u5ea6\u4e0d\u80fd\u5c11\u4e8e 6 \u4f4d",
  passwordTitle: "\u4fee\u6539\u5bc6\u7801",
  pendingReview: "\u4f18\u5148\u63d0\u9192\u5f85\u5ba1\u6838\u8bb0\u5f55",
  pendingReviewDesc: "\u5728\u5de5\u4f5c\u6d41\u91cc\u4f18\u5148\u5173\u6ce8\u4ecd\u9700 HR \u51b3\u7b56\u7684\u5339\u914d\u7ed3\u679c\u3002",
  previewMode: "\u7b80\u5386\u9884\u89c8\u65b9\u5f0f",
  rebuildDesc: "\u91cd\u5efa\u671f\u95f4\u667a\u80fd\u5339\u914d\u53ef\u80fd\u77ed\u6682\u53d8\u6162\u3002\u786e\u8ba4\u540e\u4f1a\u63d0\u4ea4\u540e\u53f0\u4efb\u52a1\uff0c\u4e0d\u4f1a\u5220\u9664\u5019\u9009\u4eba\u6570\u636e\u3002",
  rebuildIndex: "\u91cd\u5efa\u5019\u9009\u4eba\u7d22\u5f15",
  rebuildSubmitted: "\u7d22\u5f15\u91cd\u5efa\u4efb\u52a1\u5df2\u63d0\u4ea4",
  refreshStatus: "\u5237\u65b0\u72b6\u6001",
  resetDefault: "\u6062\u590d\u9ed8\u8ba4",
  restoreSuccess: "\u5df2\u6062\u590d\u9ed8\u8ba4\u504f\u597d",
  reviewThreshold: "\u5efa\u8bae\u901a\u8fc7\u5206\u6570\u7ebf",
  reviewThresholdDesc: "\u7528\u4e8e\u4f60\u5224\u65ad AI \u63a8\u8350\u5f3a\u5f31\u7684\u53c2\u8003\u9608\u503c\u3002",
  role: "\u89d2\u8272",
  savePreferences: "\u4fdd\u5b58\u504f\u597d",
  saveSuccess: "\u672c\u673a\u504f\u597d\u5df2\u4fdd\u5b58",
  security1: "\u4f7f\u7528\u5f3a\u5bc6\u7801\u5e76\u907f\u514d\u591a\u4eba\u5171\u7528\u7ba1\u7406\u5458\u8d26\u53f7\u3002",
  security2: "\u5b9a\u671f\u68c0\u67e5 AI \u670d\u52a1\u72b6\u6001\uff0c\u907f\u514d\u5339\u914d\u7ed3\u679c\u53ea\u8d70\u964d\u7ea7\u903b\u8f91\u3002",
  security3: "\u5220\u9664\u5339\u914d\u5386\u53f2\u524d\u5148\u786e\u8ba4\u5ba1\u6838\u5907\u6ce8\u548c\u5bfc\u51fa\u6587\u4ef6\u4e0d\u518d\u9700\u8981\u3002",
  securityTitle: "\u5b89\u5168\u5efa\u8bae",
  serviceDown: "\u4e0d\u53ef\u7528",
  serviceOk: "\u53ef\u8fde\u63a5",
  settings: "\u8bbe\u7f6e",
  settingsDesc: "\u7ba1\u7406\u8d26\u6237\u5b89\u5168\u3001\u7cfb\u7edf\u72b6\u6001\u3001\u62db\u8058\u6d41\u7a0b\u504f\u597d\u548c\u7ef4\u62a4\u5de5\u5177\u3002",
  submitPassword: "\u4fee\u6539\u5bc6\u7801",
  textPreview: "\u89e3\u6790\u6587\u672c",
  originalPdf: "\u539f\u59cb PDF",
};

function StatusPill({
  ok,
  label,
  loading,
}: {
  ok: boolean;
  label: string;
  loading?: boolean;
}) {
  return (
    <Badge
      variant="outline"
      className={
        loading
          ? "border-muted-foreground/30 text-muted-foreground"
          : ok
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
            : "border-destructive/30 bg-destructive/10 text-destructive"
      }
    >
      {loading ? text.checkRunning : label}
    </Badge>
  );
}

export default function Settings() {
  const user = useAuthStore((state) => state.user);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [preferences, setPreferences] = useState<LocalPreferences>(() => readPreferences());
  const [confirmRebuildOpen, setConfirmRebuildOpen] = useState(false);

  const backendHealth = useQuery({
    queryKey: ["settings", "backend-health"],
    queryFn: async () => {
      const res = await apiClient.get<{ status: string }>("/health");
      return res.data;
    },
    retry: 1,
    staleTime: 30_000,
  });

  const aiHealth = useQuery({
    queryKey: ["settings", "ai-health"],
    queryFn: async () => {
      const res = await apiClient.get("/skills");
      return res.data;
    },
    retry: 1,
    staleTime: 30_000,
  });

  useEffect(() => {
    writePreferences(preferences);
  }, [preferences]);

  const passwordMutation = useMutation({
    mutationFn: () =>
      apiClient.patch("/auth/password", {
        old_password: oldPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      toast.success(text.passwordChanged);
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
  });

  const rebuildIndexMutation = useMutation({
    mutationFn: () => apiClient.post("/admin/rebuild-index", {}),
    onSuccess: () => {
      toast.success(text.rebuildSubmitted);
      setConfirmRebuildOpen(false);
    },
  });

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (newPassword.length < 6) {
      toast.error(text.passwordLength);
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error(text.mismatchPassword);
      return;
    }

    passwordMutation.mutate();
  };

  const savePreferences = () => {
    writePreferences(preferences);
    toast.success(text.saveSuccess);
  };

  const resetPreferences = () => {
    setPreferences(DEFAULT_PREFERENCES);
    toast.success(text.restoreSuccess);
  };

  const refreshHealth = () => {
    backendHealth.refetch();
    aiHealth.refetch();
  };

  const backendOk = backendHealth.data?.status === "ok";
  const aiOk = aiHealth.isSuccess;

  return (
    <div className="space-y-6 py-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex items-center gap-3">
          <SettingsIcon className="size-6 text-primary" />
          <div>
            <h1 className="text-2xl font-semibold">{text.settings}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{text.settingsDesc}</p>
          </div>
        </div>
        <Button variant="outline" onClick={refreshHealth} className="gap-2">
          <RefreshCw className="size-4" />
          {text.refreshStatus}
        </Button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(360px,440px)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserRound className="size-4 text-primary" />
                {text.accountInfo}
              </CardTitle>
              <CardDescription>{text.accountInfoDesc}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="text-xs text-muted-foreground">{text.currentUser}</div>
                <div className="mt-1 font-medium">{user?.username || text.defaultUser}</div>
              </div>
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="text-xs text-muted-foreground">{text.role}</div>
                <div className="mt-1 font-medium">{user?.role || text.defaultRole}</div>
              </div>
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="text-xs text-muted-foreground">{text.accountApi}</div>
                <div className="mt-1 truncate font-medium">{getApiBaseURL()}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="size-4 text-primary" />
                {text.healthTitle}
              </CardTitle>
              <CardDescription>{text.healthDesc}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 font-medium">
                    <Server className="size-4" />
                    {text.backend}
                  </div>
                  <StatusPill
                    ok={backendOk}
                    loading={backendHealth.isFetching}
                    label={backendOk ? text.normal : text.error}
                  />
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{text.backendDesc}</p>
              </div>

              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 font-medium">
                    <BrainCircuit className="size-4" />
                    {text.aiService}
                  </div>
                  <StatusPill
                    ok={aiOk}
                    loading={aiHealth.isFetching}
                    label={aiOk ? text.serviceOk : text.serviceDown}
                  />
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{text.aiServiceDesc}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SlidersHorizontal className="size-4 text-primary" />
                {text.localPref}
              </CardTitle>
              <CardDescription>{text.localPrefDesc}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_140px] md:items-center">
                <div>
                  <div className="font-medium">{text.reviewThreshold}</div>
                  <p className="text-sm text-muted-foreground">{text.reviewThresholdDesc}</p>
                </div>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={preferences.reviewThreshold}
                  onChange={(event) =>
                    setPreferences((prev) => ({
                      ...prev,
                      reviewThreshold: Math.max(0, Math.min(100, Number(event.target.value) || 0)),
                    }))
                  }
                />
              </div>

              <Separator />

              <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_140px] md:items-center">
                <div>
                  <div className="font-medium">{text.matchCandidateLimit}</div>
                  <p className="text-sm text-muted-foreground">{text.matchCandidateLimitDesc}</p>
                </div>
                <Input
                  type="number"
                  min={1}
                  max={30}
                  value={preferences.matchCandidateLimit}
                  onChange={(event) =>
                    setPreferences((prev) => ({
                      ...prev,
                      matchCandidateLimit: clampMatchCandidateLimit(Number(event.target.value)),
                    }))
                  }
                />
              </div>

              <Separator />

              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={preferences.notifyPendingReview}
                  onChange={(event) =>
                    setPreferences((prev) => ({
                      ...prev,
                      notifyPendingReview: event.target.checked,
                    }))
                  }
                  className="mt-1 size-4 accent-primary"
                />
                <span>
                  <span className="block font-medium">{text.pendingReview}</span>
                  <span className="text-sm text-muted-foreground">{text.pendingReviewDesc}</span>
                </span>
              </label>

              <div className="grid gap-2">
                <div className="font-medium">{text.previewMode}</div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { value: "pdf", label: text.originalPdf },
                    { value: "text", label: text.textPreview },
                  ].map((option) => (
                    <Button
                      key={option.value}
                      type="button"
                      size="sm"
                      variant={preferences.resumePreviewMode === option.value ? "default" : "outline"}
                      onClick={() =>
                        setPreferences((prev) => ({
                          ...prev,
                          resumePreviewMode: option.value as LocalPreferences["resumePreviewMode"],
                        }))
                      }
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
            <CardFooter className="justify-between gap-2">
              <Button variant="outline" onClick={resetPreferences} className="gap-2">
                <RotateCcw className="size-4" />
                {text.resetDefault}
              </Button>
              <Button onClick={savePreferences} className="gap-2">
                <Save className="size-4" />
                {text.savePreferences}
              </Button>
            </CardFooter>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyRound className="size-4 text-primary" />
                {text.passwordTitle}
              </CardTitle>
              <CardDescription>{text.passwordDesc}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">{text.oldPassword}</label>
                  <Input
                    type="password"
                    value={oldPassword}
                    onChange={(event) => setOldPassword(event.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{text.newPassword}</label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                    required
                    minLength={6}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{text.confirmNewPassword}</label>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    required
                    minLength={6}
                  />
                </div>
                <Button type="submit" disabled={passwordMutation.isPending} className="w-full gap-2">
                  {passwordMutation.isPending && <Loader2 className="size-4 animate-spin" />}
                  {text.submitPassword}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="size-4 text-primary" />
                {text.maintenanceTitle}
              </CardTitle>
              <CardDescription>{text.maintenanceDesc}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-3 text-sm text-muted-foreground">
                {text.maintenanceTip}
              </div>
              <Button variant="outline" onClick={() => setConfirmRebuildOpen(true)} className="w-full gap-2">
                <Database className="size-4" />
                {text.rebuildIndex}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="size-4 text-primary" />
                {text.securityTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              {[text.security1, text.security2, text.security3].map((item) => (
                <div key={item} className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-400" />
                  <span>{item}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={confirmRebuildOpen} onOpenChange={setConfirmRebuildOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-300">
              <AlertTriangle className="size-5" />
            </div>
            <DialogTitle>{text.rebuildIndex}</DialogTitle>
            <DialogDescription>{text.rebuildDesc}</DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmRebuildOpen(false)}>
              {text.cancel}
            </Button>
            <Button
              onClick={() => rebuildIndexMutation.mutate()}
              disabled={rebuildIndexMutation.isPending}
              className="gap-2"
            >
              {rebuildIndexMutation.isPending && <Loader2 className="size-4 animate-spin" />}
              {text.confirmRebuild}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
