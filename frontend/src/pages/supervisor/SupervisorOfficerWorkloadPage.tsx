import { useEffect, useState } from 'react';
import AppLayout from '../../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/ui/EmptyState';
import { formatApiError } from '../../api/client';
import { fetchSupervisorDashboard } from '../../api/grievances';
import type { SupervisorDashboardData } from '../../types';
import { Users, UserCheck } from 'lucide-react';

export function SupervisorOfficerWorkloadPage() {
  const [supData, setSupData] = useState<SupervisorDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchSupervisorDashboard();
      setSupData(res);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const officerWorkload = supData?.officer_workload || {};
  const officerEntries = Object.entries(officerWorkload);

  return (
    <AppLayout title="Officer Workload" breadcrumb="Supervisor Workspace">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Department Officer Workload Matrix</h1>
            <p className="text-xs text-slate-400 mt-1">
              Inspect officer capacity, active case distribution, and workload balancing parameters.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>
              <Users className="w-5 h-5 text-amber-400" />
              Active Officer Roster & Capacity ({officerEntries.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3 py-4">
                <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : officerEntries.length === 0 ? (
              <EmptyState
                icon={<UserCheck className="w-10 h-10 text-slate-500" />}
                title="No active officer assignments"
                description="Officer workload statistics will populate as grievances are assigned to department officers."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                      <th className="pb-3">Officer Name / ID</th>
                      <th className="pb-3 text-right">Active Assigned Cases</th>
                      <th className="pb-3 text-right">Load Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {officerEntries.map(([name, count]) => (
                      <tr key={name} className="hover:bg-slate-800/20 transition">
                        <td className="py-4 font-semibold text-slate-200">{name}</td>
                        <td className="py-4 text-right font-mono font-bold text-blue-400 text-base">{count}</td>
                        <td className="py-4 text-right">
                          <Badge variant={count > 5 ? 'warning' : 'success'} size="sm">
                            {count > 5 ? 'High Load (>5)' : 'Optimal Load'}
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
      </div>
    </AppLayout>
  );
}

export default SupervisorOfficerWorkloadPage;
