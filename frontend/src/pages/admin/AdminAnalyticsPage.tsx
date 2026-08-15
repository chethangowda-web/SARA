import { useEffect, useState } from 'react';
import AppLayout from '../../layouts/AppLayout';
import StatCard from '../../components/ui/StatCard';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { formatApiError } from '../../api/client';
import { fetchAnalyticsOverview, fetchAnalyticsTrends } from '../../api/grievances';
import type { AnalyticsOverview, AnalyticsTrend } from '../../types';
import { BarChart3, FileText, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

export function AdminAnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ovRes, trRes] = await Promise.all([
        fetchAnalyticsOverview(),
        fetchAnalyticsTrends().catch(() => []),
      ]);
      setOverview(ovRes);
      setTrends(trRes || []);
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
    <AppLayout title="Analytics & Trends" breadcrumb="Admin Intelligence">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">System Analytics & Historical Trends</h1>
            <p className="text-xs text-slate-400 mt-1">
              Time-series metrics, volume velocity, closure rates, and SLA compliance statistics.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Volume"
            value={loading ? '...' : overview?.total_grievances || 0}
            colorScheme="blue"
            icon={<FileText className="w-5 h-5" />}
            subtitle="Lifetime complaints logged"
          />
          <StatCard
            title="SLA Compliance"
            value={loading ? '...' : `${overview?.sla_compliance_percent || 100}%`}
            colorScheme="emerald"
            icon={<CheckCircle2 className="w-5 h-5" />}
            subtitle="Resolution SLA rate"
          />
          <StatCard
            title="Avg Resolution"
            value={loading ? '...' : `${overview?.average_resolution_hours || 0}h`}
            colorScheme="amber"
            icon={<Clock className="w-5 h-5" />}
            subtitle="Turnaround lead time"
          />
          <StatCard
            title="SLA Breaches"
            value={loading ? '...' : overview?.sla_breaches || 0}
            colorScheme="red"
            icon={<AlertTriangle className="w-5 h-5" />}
            subtitle="Escalated breaches"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Time-Series Trends Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3 py-4">
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : trends.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">No time-series trend data points accumulated yet.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trends.map((t) => (
                  <div key={t.metric} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                    <div className="text-xs font-bold text-blue-400 uppercase tracking-wider">{t.metric}</div>
                    <div className="text-xs text-slate-400 font-mono">
                      Data points: {t.points ? t.points.length : 0}
                    </div>
                    {t.points && t.points.length > 0 && (
                      <div className="space-y-1 pt-2 border-t border-slate-800/60 max-h-32 overflow-y-auto text-[11px]">
                        {t.points.map((pt, idx) => (
                          <div key={idx} className="flex justify-between font-mono text-slate-300">
                            <span>{pt.timestamp}</span>
                            <span className="font-bold text-emerald-400">{pt.value}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}

export default AdminAnalyticsPage;

