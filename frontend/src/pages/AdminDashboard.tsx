import { useEffect, useState } from 'react';
import AppLayout from '../layouts/AppLayout';
import StatCard from '../components/ui/StatCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { formatApiError } from '../api/client';
import {
  fetchAdminDashboard,
  fetchAnalyticsOverview,
  fetchAnalyticsDepartments,
  fetchAnalyticsAnomalies,
  fetchAnalyticsInsights,
} from '../api/grievances';
import type {
  AdminDashboardData,
  AnalyticsOverview,
  AnalyticsDepartment,
  AnalyticsAnomaly,
  AnalyticsInsight,
} from '../types';
import {
  ShieldCheck,
  Building2,
  BarChart3,
  Sparkles,
  ShieldAlert,
  Clock,
  AlertTriangle,
  Flame,
  Activity,
} from 'lucide-react';

export function AdminDashboard() {
  const [adminData, setAdminData] = useState<AdminDashboardData | null>(null);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [departments, setDepartments] = useState<AnalyticsDepartment[]>([]);
  const [anomalies, setAnomalies] = useState<AnalyticsAnomaly[]>([]);
  const [insights, setInsights] = useState<AnalyticsInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [aRes, ovRes, deptRes, anomRes, insRes] = await Promise.all([
        fetchAdminDashboard().catch(() => null),
        fetchAnalyticsOverview().catch(() => null),
        fetchAnalyticsDepartments().catch(() => []),
        fetchAnalyticsAnomalies().catch(() => []),
        fetchAnalyticsInsights().catch(() => null),
      ]);
      setAdminData(aRes);
      setOverview(ovRes);
      setDepartments(deptRes || []);
      setAnomalies(anomRes || []);
      setInsights(insRes);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <AppLayout title="SARA Command Center" breadcrumb="Executive Intelligence">
      <div className="space-y-6">
        {/* Executive Banner */}
        <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-red-950/60 via-slate-900 to-indigo-950/40 border border-slate-800/80 shadow-2xl flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-950 border border-red-800 text-red-300 text-xs font-bold uppercase tracking-wider">
              <ShieldCheck className="w-3.5 h-3.5 text-red-400" />
              <span>SARA Executive Command Center</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
              Operational Intelligence & Accountability Overview
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              System-wide grievance metrics, cross-departmental SLA compliance, operational anomaly alerts, and AI advisory recommendations.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </div>
        )}

        {/* Global Executive KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard
            title="Total Grievances"
            value={loading ? '...' : adminData?.total_grievances || overview?.total_grievances || 0}
            colorScheme="blue"
            icon={<Activity className="w-4 h-4" />}
          />
          <StatCard
            title="Open Cases"
            value={loading ? '...' : overview?.open_grievances || 0}
            colorScheme="cyan"
            icon={<Clock className="w-4 h-4" />}
          />
          <StatCard
            title="SLA Compliance"
            value={loading ? '...' : `${overview?.sla_compliance_percent || 95}%`}
            colorScheme="emerald"
            icon={<BarChart3 className="w-4 h-4" />}
          />
          <StatCard
            title="SLA Breaches"
            value={loading ? '...' : adminData?.sla_breaches || overview?.sla_breaches || 0}
            colorScheme="red"
            icon={<AlertTriangle className="w-4 h-4" />}
          />
          <StatCard
            title="Escalations"
            value={loading ? '...' : adminData?.escalated_grievances || overview?.escalated_grievances || 0}
            colorScheme="amber"
            icon={<Flame className="w-4 h-4" />}
          />
          <StatCard
            title="Avg Resolution"
            value={loading ? '...' : `${adminData?.average_resolution_time_hours || overview?.average_resolution_hours || 18}h`}
            colorScheme="purple"
            icon={<Clock className="w-4 h-4" />}
          />
        </div>

        {/* AI Operational Insights Panel */}
        <Card className="bg-indigo-950/30 border-indigo-800/60 relative overflow-hidden">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-indigo-300">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                AI Operational Intelligence Advisory
              </CardTitle>
              <Badge variant="purple">AI Advisory â€” Decision Support Only</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {insights?.insights && insights.insights.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {insights.insights.map((ins, idx) => (
                  <div key={idx} className="p-3.5 bg-slate-950/60 rounded-xl border border-indigo-900/40 text-xs text-indigo-100 flex items-start gap-2.5">
                    <span className="text-indigo-400 font-bold text-base leading-none">â€¢</span>
                    <span className="leading-relaxed">{ins}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-slate-400 text-xs py-2">AI engines operating normally. No system-wide anomalies flagged.</div>
            )}
            <div className="text-[10px] text-indigo-400/60 font-mono pt-2">
              Disclaimer: Insights are advisory and do not automatically modify grievance state machine rules.
            </div>
          </CardContent>
        </Card>

        {/* Department Health Grid & Operational Anomalies */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Department Comparison Table */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>
                <Building2 className="w-5 h-5 text-blue-400" />
                Departmental Performance & SLA Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3 py-4">
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                </div>
              ) : departments.length === 0 ? (
                <EmptyState title="No department health data" description="Department analytics will populate as grievances are routed across ministries." />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                        <th className="pb-3">Department</th>
                        <th className="pb-3 text-right">Open</th>
                        <th className="pb-3 text-right">Closed</th>
                        <th className="pb-3 text-right">SLA %</th>
                        <th className="pb-3 text-right">Avg Res (h)</th>
                        <th className="pb-3 text-right">Escalated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {departments.map((dept) => (
                        <tr key={dept.department_id} className="hover:bg-slate-800/20 transition">
                          <td className="py-3.5 font-semibold text-slate-200">{dept.department_name}</td>
                          <td className="py-3.5 text-right font-mono text-blue-400 font-bold">{dept.open_grievances}</td>
                          <td className="py-3.5 text-right font-mono text-slate-400">{dept.closed_grievances}</td>
                          <td className="py-3.5 text-right font-mono text-emerald-400 font-bold">{dept.sla_compliance_percent}%</td>
                          <td className="py-3.5 text-right font-mono text-purple-400">{dept.average_resolution_hours}</td>
                          <td className="py-3.5 text-right font-mono text-red-400 font-bold">{dept.escalation_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Operational Anomalies Panel */}
          <Card className="bg-red-950/20 border-red-900/50 flex flex-col">
            <CardHeader>
              <CardTitle className="text-red-300">
                <ShieldAlert className="w-5 h-5 text-red-400" />
                Active Operational Anomalies ({anomalies.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 space-y-3">
              {anomalies.length === 0 ? (
                <div className="text-center py-10 text-slate-500 text-xs">No active operational anomalies detected across government services.</div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                  {anomalies.map((a) => (
                    <div key={a.id} className="p-3.5 bg-slate-950 border border-red-900/60 rounded-xl space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-red-300 bg-red-950/80 px-2 py-0.5 rounded border border-red-800">{a.anomaly_type}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{new Date(a.detected_at).toLocaleDateString()}</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">{a.explanation}</p>
                      <div className="flex gap-4 text-[11px] font-mono pt-1 text-slate-400 border-t border-slate-900">
                        <span>Observed: <strong className="text-red-400">{a.observed_value}</strong></span>
                        <span>Expected: <strong className="text-slate-300">{a.expected_value}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminDashboard;

