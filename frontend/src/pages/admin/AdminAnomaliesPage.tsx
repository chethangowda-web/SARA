import { useEffect, useState } from 'react';
import AppLayout from '../../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/ui/EmptyState';
import { formatApiError } from '../../api/client';
import { fetchAnalyticsAnomalies, fetchAnalyticsInsights } from '../../api/grievances';
import type { AnalyticsAnomaly, AnalyticsInsight } from '../../types';
import { ShieldAlert, Sparkles, AlertCircle } from 'lucide-react';

export function AdminAnomaliesPage() {
  const [anomalies, setAnomalies] = useState<AnalyticsAnomaly[]>([]);
  const [insights, setInsights] = useState<AnalyticsInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [anomRes, insRes] = await Promise.all([
        fetchAnalyticsAnomalies().catch(() => []),
        fetchAnalyticsInsights().catch(() => null),
      ]);
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
    <AppLayout title="Anomalies & AI Advisory" breadcrumb="Admin Intelligence">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">System Anomalies & AI Decision Advisory</h1>
            <p className="text-xs text-slate-400 mt-1">
              Automated anomaly detection models and governance advisory insights.
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
          <Card className="bg-amber-950/20 border-amber-900/50">
            <CardHeader>
              <CardTitle className="text-amber-300">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                Detected Operational Anomalies ({anomalies.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3 py-4">
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                </div>
              ) : anomalies.length === 0 ? (
                <EmptyState
                  icon={<AlertCircle className="w-10 h-10 text-slate-500" />}
                  title="No operational anomalies detected"
                  description="System metrics demonstrate normal baseline performance across all departments."
                />
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {anomalies.map((a) => (
                    <div key={a.id} className="p-4 bg-slate-950 border border-amber-900/50 rounded-xl space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-300 text-sm">{a.anomaly_type}</span>
                        <Badge variant="warning" size="sm">{a.severity}</Badge>
                      </div>
                      <p className="text-slate-300 leading-relaxed">{a.explanation}</p>
                      <div className="flex justify-between text-[10px] text-slate-500 font-mono pt-1">
                        <span>Observed: {a.observed_value}</span>
                        <span>Detected: {new Date(a.detected_at).toLocaleString()}</span>
                      </div>
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
                AI Governance Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3 py-4">
                  <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                </div>
              ) : insights?.insights ? (
                <div className="space-y-4">
                  <div className="text-xs text-indigo-300 font-mono">
                    Provider: {insights.provider} {insights.is_fallback ? '(Fallback Mode)' : ''}
                  </div>
                  <ul className="space-y-3">
                    {insights.insights.map((ins, idx) => (
                      <li key={idx} className="p-3 bg-slate-950/80 border border-indigo-900/40 rounded-xl text-xs text-indigo-100 leading-relaxed">
                        • {ins}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="text-slate-400 text-xs py-4">AI insights unavailable at present.</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminAnomaliesPage;
