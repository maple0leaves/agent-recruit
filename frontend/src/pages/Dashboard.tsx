import { useNavigate } from "react-router-dom";
import { Briefcase, Users, ClipboardCheck } from "lucide-react";
import { Skeleton } from "../components/ui/skeleton";
import { useDashboardStats, useDashboardTrend } from "../hooks/useDashboard";
import StatsCard from "../components/Dashboard/StatsCard";
import TrendChart from "../components/Dashboard/TrendChart";

export default function Dashboard() {
  const navigate = useNavigate();
  const { data, isLoading } = useDashboardStats();
  const { data: trendData } = useDashboardTrend();

  return (
    <div className="py-6">
      <h1 className="text-2xl font-semibold">仪表盘</h1>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        {isLoading ? (
          <>
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </>
        ) : (
          <>
            <StatsCard
              title="活跃 JD"
              value={data?.active_jds ?? 0}
              icon={Briefcase}
              onClick={() => navigate("/jd")}
            />
            <StatsCard
              title="候选人总数"
              value={data?.total_candidates ?? 0}
              icon={Users}
              onClick={() => navigate("/candidates")}
            />
            <StatsCard
              title="待审核"
              value={data?.pending_approvals ?? 0}
              icon={ClipboardCheck}
              onClick={() => navigate("/match-history")}
            />
          </>
        )}
      </div>

      {trendData && trendData.length > 0 && (
        <div className="mt-8">
          <TrendChart data={trendData} />
        </div>
      )}

      {data && data.pending_approvals > 0 && (
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          您有 <strong>{data.pending_approvals}</strong> 个匹配结果待审核，请前往{" "}
          <button
            className="underline cursor-pointer"
            onClick={() => navigate("/match-history")}
          >
            匹配历史页面
          </button>{" "}
          审核。
        </div>
      )}
    </div>
  );
}
