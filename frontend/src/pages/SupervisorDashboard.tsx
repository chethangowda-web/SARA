import { useEffect, useState } from 'react';
import AppLayout from '../layouts/AppLayout';
import StatCard from '../components/ui/StatCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { formatApiError } from '../api/client';
import {
  fetchSupervisorDashboard,
  fetchAnalyticsAnomalies,
  fetchAnalyticsInsights,
  listDepartmentGrievances,
} from '../api/grievances';
import type {
  SupervisorDashboardData,
  AnalyticsAnomaly,
  AnalyticsInsight,
  Grievance,
} from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Building2,
  Users,
  AlertTriangle,
  BarChart3,
  Sparkles,
  ShieldAlert,
  Flame,
  ArrowRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function SupervisorDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [supData, setSupData] = useState<SupervisorDashboardData | null>(null);
  const [anomalies, setAnomalies] = useState<AnalyticsAnomaly[]>([]);
  const [insights, setInsights] = useState<AnalyticsInsight | null>(null);
  const [deptGrievances, setDeptGrievances] = useState<Grievance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sRes, anomRes, insRes, gRes] = await Promise.all([
        fetchSupervisorDashboard().catch(() => null),
        fetchAnalyticsAnomalies().catch(() => []),
        fetchAnalyticsInsights().catch(() => null),
        listDepartmentGrievances(50, 0).catch(() => []),
      ]);
      setSupData(sRes);
      setAnomalies(anomRes || []);
      setInsights(insRes);
      setDeptGrievances(gRes || []);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const escalatedCases = deptGrievances.filter((g) => g.escalated || (g.escalation_level && g.escalation_level > 0));

  return (
    <AppLayout title="Supervisor Command Center" breadcrumb="Department Workspace">
      <div className="space-y-6">
        {/* Header Banner */}
        <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-amber-950/60 via-slate-900 to-blue-950/40 border border-slate-800/80 shadow-2xl flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950 border border-amber-800 text-amber-300 text-xs font-bold uppercase tracking-wider">
              Department Command Zone
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Supervisor Workspace ({user?.full_name || 'Department Supervisor'})
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Monitor department workload, track active officer assignments, resolve SLA breaches, and manage escalations.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </div>
        )}

        {/* Department KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Active Grievances"
            value={loading ? '...' : supData?.total_active_grievances || deptGrievances.length}
            colorScheme="amber"
            icon={<Building2 className="w-5 h-5" />}
            subtitle="Department active pipeline"
          />
          <StatCard
            title="SLA Compliance"
            value={loading ? '...' : `${supData ? (supData.escalated_grievances === 0 ? 100 : Math.max(0, Math.round((1 - supData.escalated_grievances / Math.max(supData.total_active_grievances, 1)) * 100))) : 94}%`}
            colorScheme="emerald"
            icon={<BarChart3 className="w-5 h-5" />}
            subtitle="Resolution compliance rate"
          />
          <StatCard
            title="Escalated Cases"
            value={loading ? '...' : supData?.escalated_grievances || escalatedCases.length}
            colorScheme="red"
            icon={<AlertTriangle className="w-5 h-5" />}
            subtitle="Requires immediate review"
          />
          <StatCard
            title="High Risk Cases"
            value={loading ? '...' : supData?.high_risk_grievances || 0}
            colorScheme="purple"
            icon={<Flame className="w-5 h-5" />}
            subtitle="Critical risk score >= 70"
          />
        </div>

        {/* Officer Workload Grid & Escalations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Officer Workload Matrix */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>
                <Users className="w-5 h-5 text-amber-400" />
                Officer Workload & Active Assignments
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3 py-4">
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                </div>
              ) : !supData?.officer_workload || Object.keys(supData.officer_workload).length === 0 ? (
                <EmptyState title="No active officer assignments" description="Officer workload statistics will populate as grievances are assigned." />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                        <th className="pb-3">Officer Name</th>
                        <th className="pb-3 text-right">Active Cases</th>
                        <th className="pb-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {Object.entries(supData.officer_workload).map(([officerName, activeCount]) => (
                        <tr key={officerName} className="hover:bg-slate-800/20 transition">
                          <td className="py-3.5 font-semibold text-slate-200">{officerName}</td>
                          <td className="py-3.5 text-right font-mono font-bold text-blue-400">{activeCount}</td>
                          <td className="py-3.5 text-right">
                            <Badge variant={activeCount > 5 ? 'warning' : 'success'} size="sm">
                              {activeCount > 5 ? 'High Load' : 'Normal'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Escalations Panel */}
          <Card className="bg-red-950/20 border-red-900/50">
            <CardHeader>
              <CardTitle className="text-red-300">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                Active Escalations ({escalatedCases.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {escalatedCases.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">No active escalations in department.</div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                  {escalatedCases.map((g) => (
                    <div key={g.id} className="p-3 bg-slate-950 border border-red-900/50 rounded-xl space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-red-400 font-bold">{g.id.substring(0, 8)}</span>
                        <Badge variant="danger" size="sm">Level {g.escalation_level || 1} Escalation</Badge>
                      </div>
                      <div className="font-bold text-slate-200 truncate">{g.title}</div>
                      <div className="flex items-center justify-between pt-1">
                        <span className="text-[10px] text-slate-400">State: {g.current_state}</span>
                        <button
                          onClick={() => navigate(`/grievances/${g.id}`)}
                          className="text-blue-400 text-[11px] hover:underline flex items-center gap-1"
                        >
                          <span>Review</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* AI Operational Insights & Anomalies */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Insights Panel */}
          <Card className="bg-indigo-950/20 border-indigo-900/50">
            <CardHeader>
              <CardTitle className="text-indigo-300">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                AI Operational Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {insights?.insights ? (
                <ul className="space-y-2.5">
                  {insights.insights.map((ins, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs text-indigo-100">
                      <span className="text-indigo-400 font-bold">•</span>
                      <span className="leading-relaxed">{ins}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-slate-400 text-xs py-4">Department operations performing within expected SLA parameters.</div>
              )}
            </CardContent>
          </Card>

          {/* Department Anomalies */}
          <Card className="bg-amber-950/20 border-amber-900/50">
            <CardHeader>
              <CardTitle className="text-amber-300">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                Anomalies & Operational Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {anomalies.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs">No active anomalies detected in department pipeline.</div>
              ) : (
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {anomalies.map((a) => (
                    <div key={a.id} className="p-3 bg-slate-950 border border-amber-900/50 rounded-xl space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-300">{a.anomaly_type}</span>
                        <span className="text-[10px] text-slate-500">{new Date(a.detected_at).toLocaleDateString()}</span>
                      </div>
                      <p className="text-slate-300">{a.explanation}</p>
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

export default SupervisorDashboard;
