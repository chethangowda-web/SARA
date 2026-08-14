import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  fetchAnalyticsOverview, 
  fetchAnalyticsDepartments,
  fetchAnalyticsTrends,
  fetchAnalyticsAnomalies,
  fetchAnalyticsInsights
} from '../api/grievances';

export function AdminDashboard() {
  const { user, logout } = useAuth();
  const [overview, setOverview] = useState<any>(null);
  const [departments, setDepartments] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAnalyticsOverview(),
      fetchAnalyticsDepartments(),
      fetchAnalyticsTrends(),
      fetchAnalyticsAnomalies(),
      fetchAnalyticsInsights()
    ]).then(([ovData, deptData, _trendsData, anomData, insData]) => {
      setOverview(ovData);
      setDepartments(deptData as any[]);
      setAnomalies(anomData as any[]);
      setInsights(insData);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-brand-dark text-slate-200">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-black bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            SARA Command Center
          </h1>
          <span className="px-2 py-1 bg-red-950/40 border border-red-500/20 text-[10px] font-bold text-red-400 rounded uppercase tracking-wider">
            Admin Zone
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400">
            <strong className="text-slate-300">{user?.full_name}</strong>
          </span>
          <button 
            onClick={() => logout()}
            className="px-3 py-1.5 text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
          >
            Logout
          </button>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto p-6 space-y-8 mt-6">
        {loading ? (
          <div className="text-slate-400 text-center py-20">Initializing Command Center...</div>
        ) : (
          <>
            {/* Global KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">Total Grievances</div>
                <div className="text-3xl font-black text-white">{overview?.total_grievances}</div>
                <div className="text-xs text-slate-400 mt-2">
                  <span className="text-blue-400">{overview?.open_grievances}</span> Open | <span className="text-emerald-400">{overview?.closed_grievances}</span> Closed
                </div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">SLA Compliance</div>
                <div className="text-3xl font-black text-emerald-400">{overview?.sla_compliance_percent}%</div>
                <div className="text-xs text-slate-400 mt-2">
                  <span className="text-orange-400">{overview?.sla_warnings}</span> Warnings | <span className="text-red-400">{overview?.sla_breaches}</span> Breaches
                </div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">Avg Resolution Time</div>
                <div className="text-3xl font-black text-purple-400">{overview?.average_resolution_hours}h</div>
                <div className="text-xs text-slate-400 mt-2">
                  Assign: {overview?.average_assignment_hours}h | Ack: {overview?.average_acknowledgement_hours}h
                </div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">Critical/High Risk</div>
                <div className="text-3xl font-black text-red-500">{overview?.critical_high_risk}</div>
                <div className="text-xs text-slate-400 mt-2">
                  <span className="text-yellow-400">{overview?.escalated_grievances}</span> Active Escalations
                </div>
              </div>
            </div>

            {/* AI Insights Panel */}
            <div className="bg-indigo-950/20 border border-indigo-900/50 rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <svg className="w-24 h-24 text-indigo-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 22h20L12 2zm0 4.5l6.5 13h-13L12 6.5z"/></svg>
              </div>
              <h2 className="text-lg font-bold text-indigo-300 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                AI Operational Insights
              </h2>
              <ul className="space-y-3 relative z-10">
                {insights?.insights?.map((insight: string, idx: number) => (
                  <li key={idx} className="flex gap-3 text-sm text-indigo-100">
                    <span className="text-indigo-500 mt-0.5">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 text-[10px] text-indigo-400/60 font-mono">
                Powered by {insights?.provider} | Generated: {new Date(insights?.generated_at).toLocaleString()}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Department Comparison */}
              <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h3 className="text-md font-bold mb-4">Department Workload & SLA</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="text-slate-500 border-b border-slate-800">
                        <th className="pb-3 font-semibold">Department</th>
                        <th className="pb-3 font-semibold text-right">Active</th>
                        <th className="pb-3 font-semibold text-right">Closed</th>
                        <th className="pb-3 font-semibold text-right">SLA %</th>
                        <th className="pb-3 font-semibold text-right">Avg Res (h)</th>
                        <th className="pb-3 font-semibold text-right">Escalated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {departments.map((d: any) => (
                        <tr key={d.department_id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-3 font-medium text-slate-300">{d.department_name}</td>
                          <td className="py-3 text-right font-mono text-blue-400">{d.open_grievances}</td>
                          <td className="py-3 text-right font-mono text-slate-400">{d.closed_grievances}</td>
                          <td className="py-3 text-right font-mono text-emerald-400">{d.sla_compliance_percent}%</td>
                          <td className="py-3 text-right font-mono text-slate-300">{d.average_resolution_hours}</td>
                          <td className="py-3 text-right font-mono text-orange-400">{d.escalation_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Anomalies Panel */}
              <div className="bg-red-950/10 border border-red-900/30 rounded-xl p-6 flex flex-col">
                <h3 className="text-md font-bold text-red-400 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  Active Anomalies
                </h3>
                <div className="flex-1 overflow-y-auto space-y-3">
                  {anomalies.length === 0 ? (
                    <div className="text-center text-sm text-slate-500 py-10">No active anomalies detected.</div>
                  ) : (
                    anomalies.map((a: any) => (
                      <div key={a.id} className="bg-slate-900/50 border border-red-900/50 rounded-lg p-3">
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-xs font-bold text-red-300 bg-red-900/30 px-2 py-0.5 rounded">{a.anomaly_type}</span>
                          <span className="text-[10px] text-slate-500">{new Date(a.detected_at).toLocaleDateString()}</span>
                        </div>
                        <div className="text-sm text-slate-300 mb-2">{a.explanation}</div>
                        <div className="flex gap-4 text-xs font-mono">
                          <span className="text-slate-400">Observed: <span className="text-red-400">{a.observed_value}</span></span>
                          <span className="text-slate-400">Expected: {a.expected_value}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>
          </>
        )}
      </main>
    </div>
  );
}
export default AdminDashboard;
