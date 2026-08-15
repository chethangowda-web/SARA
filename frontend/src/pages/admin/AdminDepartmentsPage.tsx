import { useEffect, useState } from 'react';
import AppLayout from '../../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/ui/EmptyState';
import { formatApiError } from '../../api/client';
import { fetchAnalyticsDepartments } from '../../api/grievances';
import type { AnalyticsDepartment } from '../../types';
import { Building2 } from 'lucide-react';

export function AdminDepartmentsPage() {
  const [departments, setDepartments] = useState<AnalyticsDepartment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchAnalyticsDepartments();
      setDepartments(res || []);
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
    <AppLayout title="Departments Performance" breadcrumb="Admin Intelligence">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Cross-Departmental Performance Matrix</h1>
            <p className="text-xs text-slate-400 mt-1">
              Analyze department throughput, resolution lead times, SLA compliance rates, and active workload volumes.
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
              <Building2 className="w-5 h-5 text-indigo-400" />
              Department Metrics ({departments.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3 py-4">
                <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
                <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : departments.length === 0 ? (
              <EmptyState title="No department metrics found" description="Department metrics will populate as grievances are routed and processed." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                      <th className="pb-3">Department Name</th>
                      <th className="pb-3 text-right">Total Cases</th>
                      <th className="pb-3 text-right">Open</th>
                      <th className="pb-3 text-right">Closed</th>
                      <th className="pb-3 text-right">Avg Resolution</th>
                      <th className="pb-3 text-right">SLA Compliance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {departments.map((dept) => (
                      <tr key={dept.department_id} className="hover:bg-slate-800/20 transition">
                        <td className="py-4 font-semibold text-slate-200">{dept.department_name}</td>
                        <td className="py-4 text-right font-mono text-slate-300">{dept.total_grievances}</td>
                        <td className="py-4 text-right font-mono text-amber-400 font-bold">{dept.open_grievances}</td>
                        <td className="py-4 text-right font-mono text-emerald-400 font-bold">{dept.closed_grievances}</td>
                        <td className="py-4 text-right font-mono text-slate-300">{dept.average_resolution_hours}h</td>
                        <td className="py-4 text-right">
                          <Badge variant={dept.sla_compliance_percent >= 90 ? 'success' : 'warning'} size="sm">
                            {dept.sla_compliance_percent}%
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

export default AdminDepartmentsPage;
