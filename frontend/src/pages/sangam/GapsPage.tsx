import React, { useEffect, useState } from 'react';
import { sangamApi } from '../../api/sangam';
import type { IntelligenceAlert } from '../../api/sangam';
import { EvidenceDrawer } from '../../components/sangam/EvidenceDrawer';
import { ShieldAlert, Eye } from 'lucide-react';

export const GapsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<IntelligenceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  useEffect(() => {
    sangamApi.getGapsAndMismatches()
      .then(data => setAlerts(data))
      .catch(err => console.error('Failed to load gaps:', err))
      .finally(() => setLoading(false));
  }, []);

  const unservedGaps = alerts.filter(a => a.type === 'UNSERVED_GAP');
  const outcomeMismatches = alerts.filter(a => a.type === 'POTENTIAL_OUTCOME_MISMATCH');

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div className="pb-6 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-rose-400" />
          Unserved Gaps & Outcome Mismatches
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Objective intelligence alerts identifying unaddressed public needs and project outcome verification requirements.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20 text-slate-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Section 1: Potential Unserved Gaps */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-3 rounded-full bg-rose-500"></span>
              <h2 className="text-lg font-bold text-slate-100">Potential Unserved Gaps ({unservedGaps.length})</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {unservedGaps.map(alert => (
                <div key={alert.id} className="bg-slate-900 border border-rose-900/30 rounded-2xl p-6 shadow-xl flex flex-col justify-between hover:border-rose-700/50 transition">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {alert.severity} SEVERITY
                      </span>
                      <span className="text-xs text-slate-400">{new Date(alert.created_at).toLocaleDateString()}</span>
                    </div>

                    <h3 className="font-bold text-slate-100 text-base mb-2">{alert.title}</h3>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">{alert.description}</p>
                  </div>

                  {alert.need_cluster_id && (
                    <button
                      onClick={() => setSelectedClusterId(alert.need_cluster_id!)}
                      className="w-full py-2 px-3 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl flex items-center justify-center gap-2 transition"
                    >
                      <Eye className="w-4 h-4 text-rose-400" />
                      Inspect Gap Evidence
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Potential Outcome Mismatches */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-3 rounded-full bg-purple-500"></span>
              <h2 className="text-lg font-bold text-slate-100">Potential Outcome Mismatches ({outcomeMismatches.length})</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {outcomeMismatches.map(alert => (
                <div key={alert.id} className="bg-slate-900 border border-purple-900/30 rounded-2xl p-6 shadow-xl flex flex-col justify-between hover:border-purple-700/50 transition">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        REQUIRES HUMAN VERIFICATION
                      </span>
                      <span className="text-xs text-slate-400">{new Date(alert.created_at).toLocaleDateString()}</span>
                    </div>

                    <h3 className="font-bold text-slate-100 text-base mb-2">{alert.title}</h3>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">{alert.description}</p>
                  </div>

                  {alert.need_cluster_id && (
                    <button
                      onClick={() => setSelectedClusterId(alert.need_cluster_id!)}
                      className="w-full py-2 px-3 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl flex items-center justify-center gap-2 transition"
                    >
                      <Eye className="w-4 h-4 text-purple-400" />
                      Inspect Mismatch Evidence
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <EvidenceDrawer 
        clusterId={selectedClusterId} 
        onClose={() => setSelectedClusterId(null)} 
      />
    </div>
  );
};
