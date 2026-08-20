import React, { useEffect, useState } from 'react';
import { sangamApi } from '../../api/sangam';
import type { EvidenceDrawerData } from '../../api/sangam';
import { X, AlertTriangle, FileText, ShieldAlert, MapPin, User } from 'lucide-react';

interface EvidenceDrawerProps {
  clusterId: string | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ clusterId, onClose }) => {
  const [data, setData] = useState<EvidenceDrawerData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'reasoning' | 'grievances' | 'projects' | 'alerts'>('reasoning');

  useEffect(() => {
    if (!clusterId) return;
    setLoading(true);
    sangamApi.getEvidenceDrawerData(clusterId)
      .then(res => setData(res))
      .catch(err => console.error('Failed to load evidence drawer data:', err))
      .finally(() => setLoading(false));
  }, [clusterId]);

  if (!clusterId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-sm flex justify-end transition-opacity animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 text-slate-100 h-full shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/50">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                SARA Intelligence Evidence
              </span>
              {data?.need_cluster && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  data.need_cluster.priority_score >= 70 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                  data.need_cluster.priority_score >= 40 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                  'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                }`}>
                  Priority {data.need_cluster.priority_score}/100
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              {data?.need_cluster.title || 'Loading Intelligence Evidence...'}
            </h2>
            {data?.need_cluster && (
              <p className="text-sm text-slate-400 mt-1 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-400" />
                {data.need_cluster.location_name} • Category: <span className="text-slate-200 font-medium">{data.need_cluster.category}</span>
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/30 px-6 gap-6">
          <button
            onClick={() => setActiveTab('reasoning')}
            className={`py-3 text-sm font-medium border-b-2 transition ${
              activeTab === 'reasoning' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Detection Reasoning
          </button>
          <button
            onClick={() => setActiveTab('grievances')}
            className={`py-3 text-sm font-medium border-b-2 transition ${
              activeTab === 'grievances' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Citizen Grievances ({data?.contributing_grievances.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('projects')}
            className={`py-3 text-sm font-medium border-b-2 transition ${
              activeTab === 'projects' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Matched Projects ({data?.matched_projects.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`py-3 text-sm font-medium border-b-2 transition ${
              activeTab === 'alerts' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Alerts ({data?.associated_alerts.length || 0})
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
              <span>Synthesizing evidence signals...</span>
            </div>
          ) : data ? (
            <>
              {activeTab === 'reasoning' && (
                <div className="space-y-6">
                  {/* Synthesis card */}
                  <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                    <h3 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-emerald-400" />
                      Algorithmic Detection Reasoning
                    </h3>
                    <p className="text-sm text-slate-300 leading-relaxed">
                      {data.detection_reasoning}
                    </p>
                  </div>

                  {/* Priority score breakdown */}
                  {data.need_cluster.priority_breakdown && (
                    <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                      <h3 className="text-sm font-semibold text-slate-200 mb-4">Transparent Priority Factor Breakdown</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                          <span className="text-xs text-slate-400">Complaint Volume</span>
                          <p className="text-lg font-bold text-emerald-400 mt-1">{data.need_cluster.priority_breakdown.complaint_volume_score} pts</p>
                          <span className="text-xs text-slate-500">{data.need_cluster.complaint_count} reports</span>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                          <span className="text-xs text-slate-400">Severity Assessment</span>
                          <p className="text-lg font-bold text-amber-400 mt-1">{data.need_cluster.priority_breakdown.severity_score} pts</p>
                          <span className="text-xs text-slate-500">Score {data.need_cluster.severity_score}/100</span>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                          <span className="text-xs text-slate-400">Persistence</span>
                          <p className="text-lg font-bold text-blue-400 mt-1">{data.need_cluster.priority_breakdown.persistence_score} pts</p>
                          <span className="text-xs text-slate-500">Score {data.need_cluster.persistence_score}/100</span>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                          <span className="text-xs text-slate-400">Unresolved & Reopened</span>
                          <p className="text-lg font-bold text-rose-400 mt-1">
                            {(data.need_cluster.priority_breakdown.unresolved_score + data.need_cluster.priority_breakdown.reopened_score).toFixed(1)} pts
                          </p>
                          <span className="text-xs text-slate-500">{data.need_cluster.unresolved_count} unresolved, {data.need_cluster.reopened_count} reopened</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'grievances' && (
                <div className="space-y-3">
                  {data.contributing_grievances.map(g => (
                    <div key={g.id} className="p-4 rounded-xl bg-slate-850 border border-slate-800 hover:border-slate-700 transition">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          #{g.tracking_number}
                        </span>
                        <span className="text-xs text-slate-400">{new Date(g.created_at).toLocaleDateString()}</span>
                      </div>
                      <h4 className="font-semibold text-slate-200 text-sm mb-1">{g.title}</h4>
                      <p className="text-xs text-slate-400 line-clamp-2 mb-3">{g.description}</p>
                      <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
                        <span className="flex items-center gap-1">
                          <User className="w-3.5 h-3.5 text-slate-500" />
                          {g.citizen_name || 'Citizen User'}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                          {g.current_state}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'projects' && (
                <div className="space-y-3">
                  {data.matched_projects.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 bg-slate-850 rounded-xl border border-slate-800">
                      <ShieldAlert className="w-8 h-8 text-rose-400 mx-auto mb-2 opacity-80" />
                      <p className="font-semibold text-slate-300">No Government Investment Project Matched</p>
                      <p className="text-xs text-slate-400 mt-1">This cluster has been flagged as a Potential Unserved Gap.</p>
                    </div>
                  ) : (
                    data.matched_projects.map(m => (
                      <div key={m.id} className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            Match Score {(m.match_score * 100).toFixed(0)}%
                          </span>
                          <span className="text-xs font-medium text-slate-400">{m.government_project?.status}</span>
                        </div>
                        <h4 className="font-semibold text-slate-200 text-sm mb-1">{m.government_project?.name}</h4>
                        <p className="text-xs text-slate-400 mb-3">{m.government_project?.description}</p>
                        <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-xs space-y-1 mb-3">
                          <p className="text-slate-300"><strong>Match Reasoning:</strong> {m.match_reason}</p>
                          <p className="text-slate-400"><strong>Allocation:</strong> ₹{m.government_project?.allocated_amount.toLocaleString()} | <strong>Spent:</strong> ₹{m.government_project?.spent_amount.toLocaleString()}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === 'alerts' && (
                <div className="space-y-3">
                  {data.associated_alerts.map(a => (
                    <div key={a.id} className={`p-4 rounded-xl border ${
                      a.type === 'UNSERVED_GAP' ? 'bg-rose-950/20 border-rose-800/40 text-rose-200' : 'bg-amber-950/20 border-amber-800/40 text-amber-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-xs font-bold uppercase tracking-wider">{a.type.replace(/_/g, ' ')}</span>
                      </div>
                      <h4 className="font-semibold text-sm mb-1">{a.title}</h4>
                      <p className="text-xs text-slate-300 leading-relaxed mb-3">{a.description}</p>
                      {a.evidence_json?.recommendation && (
                        <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
                          <strong>Human Action Required:</strong> {a.evidence_json.recommendation}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
          >
            Close Evidence Drawer
          </button>
        </div>
      </div>
    </div>
  );
};
