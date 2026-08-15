import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/ui/EmptyState';
import { formatApiError } from '../../api/client';
import {
  listDepartmentGrievances,
  fetchAnalyticsAnomalies,
  fetchAnalyticsInsights,
} from '../../api/grievances';
import type { Grievance, AnalyticsAnomaly, AnalyticsInsight } from '../../types';
import { AlertTriangle, ShieldAlert, Sparkles, ArrowRight } from 'lucide-react';

export function SupervisorEscalationMonitorPage() {
  const navigate = useNavigate();
  const [deptGrievances, setDeptGrievances] = useState<Grievance[]>([]);
  const [anomalies, setAnomalies] = useState<AnalyticsAnomaly[]>([]);
  const [insights, setInsights] = useState<AnalyticsInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [gList, anomList, insData] = await Promise.all([
        listDepartmentGrievances(100, 0),
        fetchAnalyticsAnomalies().catch(() => []),
        fetchAnalyticsInsights().catch(() => null),
      ]);
      setDeptGrievances(gList || []);
      setAnomalies(anomList || []);
      setInsights(insData);
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
    <AppLayout title="Escalation Monitor" breadcrumb="Supervisor Workspace">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Escalation & Anomaly Monitor</h1>
            <p className="text-xs text-slate-400 mt-1">
              Active SLA breach alerts, citizen rejection escalations, and AI anomaly detection indicators.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Escalations List */}
          <Card className="bg-red-950/20 border-red-900/50">
            <CardHeader>
              <CardTitle className="text-red-300">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                Active Department Escalations ({escalatedCases.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3 py-4">
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                </div>
              ) : escalatedCases.length === 0 ? (
                <EmptyState title="No active escalations" description="No department grievances currently flagged for SLA breach or rejection escalation." />
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
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
                          <span>Review Details</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Department Anomalies & AI Panel */}
          <div className="space-y-6">
            <Card className="bg-amber-950/20 border-amber-900/50">
              <CardHeader>
                <CardTitle className="text-amber-300">
                  <ShieldAlert className="w-5 h-5 text-amber-400" />
                  Detected Anomalies & Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                {anomalies.length === 0 ? (
                  <div className="text-slate-500 text-xs py-4 text-center">No active anomalies detected in pipeline.</div>
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

            <Card className="bg-indigo-950/20 border-indigo-900/50">
              <CardHeader>
                <CardTitle className="text-indigo-300">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  AI Operational Advisory
                </CardTitle>
              </CardHeader>
              <CardContent>
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
                  <div className="text-slate-400 text-xs py-4">Department operations performing within normal SLA parameters.</div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default SupervisorEscalationMonitorPage;
