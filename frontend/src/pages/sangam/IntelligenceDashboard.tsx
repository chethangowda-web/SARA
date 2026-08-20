import React, { useEffect, useState } from 'react';
import { sangamApi } from '../../api/sangam';
import type { SangamOverview } from '../../api/sangam';
import { EvidenceDrawer } from '../../components/sangam/EvidenceDrawer';
import { 
  AlertTriangle, 
  ShieldAlert, 
  TrendingUp, 
  MapPin, 
  Layers, 
  ChevronRight, 
  Eye,
  DollarSign,
  Activity
} from 'lucide-react';

export const IntelligenceDashboard: React.FC = () => {
  const [overview, setOverview] = useState<SangamOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  useEffect(() => {
    sangamApi.getOverview()
      .then(data => setOverview(data))
      .catch(err => console.error('Failed to load Sangam overview:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-slate-400">
        <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="font-medium text-slate-300">Initializing Sangam Civic Intelligence Layer...</span>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
              SARA Civic Intelligence
            </span>
            <span className="text-xs text-slate-400">Sangam Alignment Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Sangam Intelligence Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Connecting citizen-reported needs with government investment to detect unserved gaps and outcome mismatches.
          </p>
        </div>
      </div>

      {/* 5 KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Need Clusters</span>
            <Layers className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-3xl font-extrabold text-slate-100">{overview?.total_active_needs || 0}</div>
            <span className="text-xs text-slate-400">Synthesized citizen needs</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Hotspots</span>
            <Activity className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="text-3xl font-extrabold text-amber-400">{overview?.active_hotspots_count || 0}</div>
            <span className="text-xs text-slate-400">Priority score ≥ 40</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Unserved Gaps</span>
            <ShieldAlert className="w-5 h-5 text-rose-400" />
          </div>
          <div>
            <div className="text-3xl font-extrabold text-rose-400">{overview?.unserved_gaps_count || 0}</div>
            <span className="text-xs text-slate-400">High need, 0 projects</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Outcome Mismatches</span>
            <AlertTriangle className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <div className="text-3xl font-extrabold text-purple-400">{overview?.outcome_mismatches_count || 0}</div>
            <span className="text-xs text-slate-400">Project executed, complaints persist</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Matched Investment</span>
            <DollarSign className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <div className="text-2xl font-extrabold text-blue-400">
              ₹{((overview?.total_matched_investment || 0) / 100000).toFixed(1)}L
            </div>
            <span className="text-xs text-slate-400">Mapped public capital</span>
          </div>
        </div>
      </div>

      {/* Main Intelligence Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 cols): Top Priority Clusters & Evidence Trigger */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  Top Priority Citizen Need Clusters
                </h2>
                <p className="text-xs text-slate-400">Ranked using complaint volume, severity, persistence, and resolution debt.</p>
              </div>
            </div>

            <div className="space-y-4">
              {overview?.top_priority_clusters.map(cluster => (
                <div 
                  key={cluster.id}
                  className="p-4 rounded-xl bg-slate-850 border border-slate-800 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        cluster.priority_score >= 70 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        cluster.priority_score >= 40 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                        'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      }`}>
                        Priority {cluster.priority_score}/100
                      </span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                        {cluster.location_name}
                      </span>
                    </div>
                    <h3 className="font-semibold text-slate-200 text-base">{cluster.title}</h3>
                    <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
                      <span><strong>{cluster.complaint_count}</strong> Reports</span>
                      <span><strong>{cluster.unresolved_count}</strong> Unresolved</span>
                      <span>Category: <strong className="text-slate-300">{cluster.category}</strong></span>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedClusterId(cluster.id)}
                    className="px-4 py-2 text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl flex items-center gap-1.5 transition self-start md:self-center"
                  >
                    <Eye className="w-4 h-4" />
                    View Evidence
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (1 col): Recent Intelligence Alerts */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              Civic Intelligence Alerts
            </h2>

            <div className="space-y-4">
              {overview?.recent_alerts.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-8">No open intelligence alerts detected.</p>
              ) : (
                overview?.recent_alerts.slice(0, 5).map(alert => (
                  <div 
                    key={alert.id}
                    className={`p-4 rounded-xl border ${
                      alert.type === 'UNSERVED_GAP' 
                        ? 'bg-rose-950/10 border-rose-800/30 text-rose-200' 
                        : 'bg-purple-950/10 border-purple-800/30 text-purple-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-950/60">
                        {alert.type.replace(/_/g, ' ')}
                      </span>
                      <span className="text-[10px] text-slate-400">{new Date(alert.created_at).toLocaleDateString()}</span>
                    </div>
                    <h4 className="font-semibold text-sm mb-1 text-slate-100">{alert.title}</h4>
                    <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{alert.description}</p>
                    
                    {alert.need_cluster_id && (
                      <button
                        onClick={() => setSelectedClusterId(alert.need_cluster_id!)}
                        className="mt-3 text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition"
                      >
                        Inspect Evidence <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer 
        clusterId={selectedClusterId} 
        onClose={() => setSelectedClusterId(null)} 
      />
    </div>
  );
};
