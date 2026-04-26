import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/button";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import {
  LayoutDashboard,
  FileText,
  Users,
  BrainCircuit,
  LogOut,
  Briefcase,
} from "lucide-react";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/jd", label: "JD管理", icon: FileText },
  { path: "/candidates", label: "候选人", icon: Users },
  { path: "/matching", label: "智能匹配", icon: BrainCircuit },
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
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-30 flex h-screen w-[240px] flex-col bg-slate-900">
        {/* Logo / Brand */}
        <div className="flex items-center gap-2 px-6 py-5">
          <Briefcase className="h-6 w-6 text-white" />
          <span className="text-lg font-semibold text-white">hellojobs</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`
                  flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors
                  ${
                    active
                      ? "bg-[#1e3a5f] text-blue-400 border-l-3 border-blue-600 pl-[11px]"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                  }
                `}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Area */}
        <div className="border-t border-slate-700 p-4">
          <div className="mb-3 flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-slate-600 text-xs text-slate-200">
                {userInitial}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-slate-100">
                {user?.username || "用户"}
              </span>
              <span className="text-xs text-slate-400">
                {user?.role === "admin"
                  ? "管理员"
                  : user?.role === "recruiter"
                    ? "招聘专员"
                    : user?.role === "hiring-manager"
                      ? "部门主管"
                      : user?.role || ""}
              </span>
            </div>
          </div>

          <Button
            variant="ghost"
            className="w-full justify-start text-red-300 hover:bg-slate-800 hover:text-red-200"
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            <LogOut className="mr-2 h-4 w-4" />
            退出登录
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="ml-[240px] flex flex-1 flex-col">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center border-b border-slate-200 bg-white px-8">
          <h1 className="text-lg font-semibold text-slate-900">
            {navItems.find((item) => isActive(item.path))?.label || "HR 智能招聘系统"}
          </h1>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
