import React, { useEffect, useState } from 'react';
import { sangamApi } from '../../api/sangam';
import type { NeedCluster } from '../../api/sangam';
import { EvidenceDrawer } from '../../components/sangam/EvidenceDrawer';
import { TrendingUp, MapPin, Eye } from 'lucide-react';

export const PrioritiesPage: React.FC = () => {
  const [priorities, setPriorities] = useState<NeedCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  useEffect(() => {
    sangamApi.getPriorities()
      .then(data => setPriorities(data))
      .catch(err => console.error('Failed to load priorities:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="pb-6 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-emerald-400" />
          Evidence-Based Priority Ranking
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Objective 0–100 priority scoring model with transparent factor breakdowns.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20 text-slate-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {priorities.map((cluster, index) => (
            <div key={cluster.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-slate-700 transition">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-2xl bg-slate-800 border border-slate-700 font-extrabold text-slate-200 flex items-center justify-center shrink-0">
                  #{index + 1}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {cluster.category}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                      {cluster.location_name}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-100 text-lg">{cluster.title}</h3>
                  
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
                    <span>Complaint Volume: <strong className="text-slate-200">{cluster.complaint_count}</strong></span>
                    <span>Severity: <strong className="text-slate-200">{cluster.severity_score}/100</strong></span>
                    <span>Persistence: <strong className="text-slate-200">{cluster.persistence_score}/100</strong></span>
                    <span>Unresolved: <strong className="text-amber-400">{cluster.unresolved_count}</strong></span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 self-end md:self-center">
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Priority Score</span>
                  <span className="text-2xl font-extrabold text-emerald-400">{cluster.priority_score}<span className="text-xs text-slate-500 font-normal">/100</span></span>
                </div>

                <button
                  onClick={() => setSelectedClusterId(cluster.id)}
                  className="px-4 py-2.5 text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl flex items-center gap-1.5 transition"
                >
                  <Eye className="w-4 h-4" />
                  View Evidence
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <EvidenceDrawer 
        clusterId={selectedClusterId} 
        onClose={() => setSelectedClusterId(null)} 
      />
    </div>
  );
};
