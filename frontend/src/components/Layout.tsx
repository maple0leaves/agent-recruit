import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/button";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import {
  LayoutDashboard,
  FileText,
  Users,
  BrainCircuit,
  History,
  Settings,
  LogOut,
} from "lucide-react";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/jd", label: "JD管理", icon: FileText },
  { path: "/candidates", label: "候选人", icon: Users },
  { path: "/matching", label: "智能匹配", icon: BrainCircuit },
  { path: "/match-history", label: "匹配历史", icon: History },
  { path: "/settings", label: "设置", icon: Settings },
];

export default function Layout() {
  const { user, logout, isLoggingOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => location.pathname.startsWith(path);

  const handleLogout = async () => {
    await logout();
  };

  const userInitial = user?.username?.charAt(0).toUpperCase() || "?";

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <aside className="fixed left-0 top-0 z-30 flex h-screen w-[272px] flex-col border-r border-border bg-sidebar text-sidebar-foreground">
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="flex size-11 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-lg shadow-primary/20">
            <BrainCircuit className="size-5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-lg font-semibold leading-none text-foreground">
              AgentRecruit
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              多智能体智能招聘
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-4 py-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={[
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60",
                  active
                    ? "bg-primary/15 text-primary ring-1 ring-primary/20"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground",
                ].join(" ")}
              >
                <Icon className="size-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="border-t border-border p-4">
          <div className="mb-3 flex items-center gap-3 rounded-lg bg-muted/40 p-2">
            <Avatar className="size-9">
              <AvatarFallback className="bg-primary/15 text-sm font-medium text-primary">
                {userInitial}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-foreground">
                {user?.username || "用户"}
              </div>
              <div className="text-xs text-muted-foreground">
                {user?.role === "admin"
                  ? "管理员"
                  : user?.role === "recruiter"
                    ? "招聘专员"
                    : user?.role === "hiring-manager"
                      ? "部门主管"
                      : user?.role || ""}
              </div>
            </div>
          </div>

          <Button
            variant="ghost"
            className="w-full justify-start text-destructive hover:bg-destructive/10 hover:text-destructive"
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            <LogOut className="mr-2 size-4" />
            退出登录
          </Button>
        </div>
      </aside>

      <div className="ml-[272px] flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/90 px-8 backdrop-blur">
          <div>
            <h1 className="text-xl font-semibold leading-none text-foreground">
              {navItems.find((item) => isActive(item.path))?.label || "HR 智能招聘系统"}
            </h1>
          </div>
        </header>

        <main className="min-h-0 flex-1 overflow-auto bg-background px-8 py-6">
          <div className="mx-auto w-full max-w-[1480px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
