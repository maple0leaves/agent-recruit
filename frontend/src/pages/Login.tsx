import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  AlertCircle,
  BrainCircuit,
  Gauge,
  Loader2,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

const features = [
  {
    icon: BrainCircuit,
    title: "智能简历解析",
    desc: "自动提取技能与经历，秒级结构化",
  },
  {
    icon: Gauge,
    title: "精准人岗匹配",
    desc: "按岗位语义打分排序，好简历不遗漏",
  },
  {
    icon: ShieldCheck,
    title: "人工最终把关",
    desc: "关键决策由 HR 确认，AI 只做建议",
  },
];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{
    username?: string;
    password?: string;
  }>({});
  const { login, isLoggingIn } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const validate = (): boolean => {
    const errors: { username?: string; password?: string } = {};
    if (!username.trim() || username.trim().length < 2) {
      errors.username = "请输入用户名";
    }
    if (!password) {
      errors.password = "请输入密码";
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    if (!validate()) return;

    try {
      await login({ username: username.trim(), password });
      const redirect = searchParams.get("redirect") || "/dashboard";
      navigate(redirect, { replace: true });
    } catch (err: any) {
      setPassword("");
      if (err.response) {
        setError(err.response?.data?.detail || "用户名或密码错误");
      } else if (err.request) {
        setError("网络连接失败，请检查网络后重试");
      } else {
        setError("登录失败");
      }
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#060f0d] text-white">
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute -left-40 -top-40 h-[600px] w-[600px] rounded-full bg-emerald-500/10 blur-[120px]" />
        <div className="absolute -bottom-32 right-0 h-[500px] w-[500px] rounded-full bg-teal-400/8 blur-[100px]" />
        <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-600/5 blur-[80px]" />
      </div>

      <div className="relative grid min-h-screen lg:grid-cols-[1fr_480px]">
        <section className="hidden flex-col justify-between p-12 lg:flex xl:p-16">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 shadow-[0_8px_24px_rgba(52,211,153,0.35)]">
              <BrainCircuit className="size-5 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-tight">
              AgentRecruit
            </span>
          </div>

          <div className="max-w-lg space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/8 px-4 py-1.5 text-sm text-emerald-400">
              <Sparkles className="size-3.5" />
              多智能体招聘平台
            </div>

            <div className="space-y-5">
              <h1 className="text-5xl font-bold leading-[1.15] tracking-tight xl:text-6xl">
                让每一次招聘
                <br />
                <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
                  又快又准
                </span>
              </h1>
              <p className="text-base leading-7 text-white/55">
                自动解析简历、智能匹配岗位、生成评估报告，
                <br />
                让招聘流程回到一个清晰的操作台里。
              </p>
            </div>

            <div className="space-y-3">
              {features.map(({ icon: Icon, title, desc }) => (
                <div
                  key={title}
                  className="flex items-center gap-4 rounded-xl border border-white/6 bg-white/[0.03] px-4 py-3 backdrop-blur-sm transition-colors hover:border-emerald-500/20 hover:bg-emerald-500/5"
                >
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
                    <Icon className="size-4 text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white/88">
                      {title}
                    </div>
                    <div className="text-xs text-white/45">{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-xs text-white/25">
            AgentRecruit · Powered by LangGraph + Spring Boot
          </div>
        </section>

        <main className="flex items-center justify-center border-l border-white/6 bg-white/[0.018] px-8 py-12 backdrop-blur-sm">
          <div className="w-full max-w-sm">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 shadow-[0_6px_16px_rgba(52,211,153,0.3)]">
                <BrainCircuit className="size-4 text-white" />
              </div>
              <span className="text-base font-semibold">AgentRecruit</span>
            </div>

            <div className="space-y-2 mb-8">
              <h2 className="text-2xl font-bold tracking-tight">欢迎回来</h2>
              <p className="text-sm text-white/45">请输入账号密码继续使用招聘工作台</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/70">
                  用户名
                </label>
                <div className="relative">
                  <UserRound className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-white/35" />
                  <Input
                    placeholder="请输入用户名"
                    value={username}
                    autoComplete="username"
                    onChange={(event) => {
                      setUsername(event.target.value);
                      if (fieldErrors.username) {
                        setFieldErrors((prev) => ({ ...prev, username: undefined }));
                      }
                    }}
                    disabled={isLoggingIn}
                    className="border-white/10 bg-white/5 pl-9 text-white placeholder:text-white/30 focus:border-emerald-500/50 focus:ring-emerald-500/20"
                  />
                </div>
                {fieldErrors.username && (
                  <p className="text-xs text-red-400">{fieldErrors.username}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/70">
                  密码
                </label>
                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-white/35" />
                  <Input
                    type="password"
                    placeholder="请输入密码"
                    value={password}
                    autoComplete="current-password"
                    onChange={(event) => {
                      setPassword(event.target.value);
                      if (fieldErrors.password) {
                        setFieldErrors((prev) => ({ ...prev, password: undefined }));
                      }
                    }}
                    disabled={isLoggingIn}
                    className="border-white/10 bg-white/5 pl-9 text-white placeholder:text-white/30 focus:border-emerald-500/50 focus:ring-emerald-500/20"
                  />
                </div>
                {fieldErrors.password && (
                  <p className="text-xs text-red-400">{fieldErrors.password}</p>
                )}
              </div>

              {error && (
                <div className="flex items-start gap-2.5 rounded-lg border border-red-500/20 bg-red-500/8 px-3.5 py-3 text-sm text-red-400">
                  <AlertCircle className="mt-0.5 size-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <Button
                type="submit"
                disabled={isLoggingIn}
                className="h-10 w-full gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 font-medium text-white shadow-[0_4px_20px_rgba(52,211,153,0.25)] transition-all hover:from-emerald-400 hover:to-teal-400 hover:shadow-[0_6px_28px_rgba(52,211,153,0.35)] disabled:opacity-60"
              >
                {isLoggingIn && <Loader2 className="size-4 animate-spin" />}
                {isLoggingIn ? "登录中..." : "登录"}
              </Button>
            </form>

            <p className="mt-8 text-center text-xs text-white/22">
              © 2026 AgentRecruit · 智能招聘平台
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
