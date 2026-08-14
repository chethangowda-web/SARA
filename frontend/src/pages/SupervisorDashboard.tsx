import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  fetchAnalyticsOverview, 
  fetchAnalyticsTrends,
  fetchAnalyticsAnomalies,
  fetchAnalyticsInsights
} from '../api/grievances';

export function SupervisorDashboard() {
  const { user, logout } = useAuth();
  const [overview, setOverview] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Supervisor endpoints implicitly filter to their department
    Promise.all([
      fetchAnalyticsOverview(),
      fetchAnalyticsTrends(),
      fetchAnalyticsAnomalies(),
      fetchAnalyticsInsights()
    ]).then(([ovData, _trendsData, anomData, insData]) => {
      setOverview(ovData);
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
          <span className="px-2 py-1 bg-amber-950/40 border border-amber-500/20 text-[10px] font-bold text-amber-400 rounded uppercase tracking-wider">
            Supervisor Zone
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
      
      <main className="max-w-6xl mx-auto p-6 space-y-8 mt-6">
        {loading ? (
          <div className="text-slate-400 text-center py-20">Initializing Command Center...</div>
        ) : (
          <>
            {/* Dept KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">Department Volume</div>
                <div className="text-3xl font-black text-white">{overview?.total_grievances}</div>
                <div className="text-xs text-slate-400 mt-2">
                  <span className="text-blue-400">{overview?.open_grievances}</span> Open
                </div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">SLA Health</div>
                <div className="text-3xl font-black text-emerald-400">{overview?.sla_compliance_percent}%</div>
                <div className="text-xs text-slate-400 mt-2">
                  <span className="text-red-400">{overview?.sla_breaches}</span> Breaches
                </div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">Avg Resolution</div>
                <div className="text-3xl font-black text-purple-400">{overview?.average_resolution_hours}h</div>
                <div className="text-xs text-slate-400 mt-2">
                  Assignment Avg: {overview?.average_assignment_hours}h
                </div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
                <div className="text-slate-500 text-xs font-semibold mb-1">Escalations</div>
                <div className="text-3xl font-black text-orange-500">{overview?.escalated_grievances}</div>
                <div className="text-xs text-slate-400 mt-2">
                  <span className="text-red-500">{overview?.critical_high_risk}</span> High Risk
                </div>
              </div>
            </div>

            {/* AI Insights & Anomalies Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Dept Insights */}
              <div className="bg-indigo-950/20 border border-indigo-900/50 rounded-xl p-6">
                <h2 className="text-lg font-bold text-indigo-300 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  Operational Insights
                </h2>
                <ul className="space-y-3">
                  {insights?.insights?.map((insight: string, idx: number) => (
                    <li key={idx} className="flex gap-3 text-sm text-indigo-100">
                      <span className="text-indigo-500 mt-0.5">•</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Dept Anomalies */}
              <div className="bg-amber-950/10 border border-amber-900/30 rounded-xl p-6">
                <h3 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  Anomalies & Alerts
                </h3>
                <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                  {anomalies.length === 0 ? (
                    <div className="text-center text-sm text-slate-500 py-8">Operations normal. No anomalies.</div>
                  ) : (
                    anomalies.map((a: any) => (
                      <div key={a.id} className="bg-slate-900/80 border border-amber-900/50 rounded-lg p-3">
                        <div className="text-xs font-bold text-amber-300 mb-1">{a.anomaly_type}</div>
                        <div className="text-sm text-slate-300">{a.explanation}</div>
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
export default SupervisorDashboard;
