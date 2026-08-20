import React, { useEffect, useState } from 'react';
import { sangamApi } from '../../api/sangam';
import type { NeedCluster } from '../../api/sangam';
import { EvidenceDrawer } from '../../components/sangam/EvidenceDrawer';
import { Layers, MapPin, Eye, Search } from 'lucide-react';

export const NeedClustersPage: React.FC = () => {
  const [clusters, setClusters] = useState<NeedCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    sangamApi.getNeedClusters()
      .then(data => setClusters(data))
      .catch(err => console.error('Failed to load need clusters:', err))
      .finally(() => setLoading(false));
  }, []);

  const filteredClusters = clusters.filter(c => 
    c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.location_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-6 h-6 text-emerald-400" />
            Citizen Need Clusters
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Aggregated citizen complaints grouped by category and geographic location.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Filter clusters..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20 text-slate-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredClusters.map(cluster => (
            <div key={cluster.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {cluster.category}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    cluster.priority_score >= 70 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                    cluster.priority_score >= 40 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                    'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  }`}>
                    Priority {cluster.priority_score}/100
                  </span>
                </div>

                <h3 className="font-bold text-slate-100 text-lg mb-2">{cluster.title}</h3>

                <p className="text-xs text-slate-400 flex items-center gap-1 mb-4">
                  <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                  {cluster.location_name}
                </p>

                <div className="grid grid-cols-2 gap-2 p-3 rounded-xl bg-slate-850 border border-slate-800 text-xs text-slate-300 mb-6">
                  <div>
                    <span className="text-slate-500 block">Total Complaints</span>
                    <strong className="text-sm font-semibold">{cluster.complaint_count}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Unresolved</span>
                    <strong className="text-sm font-semibold text-amber-400">{cluster.unresolved_count}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Severity Score</span>
                    <strong className="text-sm font-semibold">{cluster.severity_score}/100</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Persistence</span>
                    <strong className="text-sm font-semibold">{cluster.persistence_score}/100</strong>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSelectedClusterId(cluster.id)}
                className="w-full py-2.5 px-4 text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl flex items-center justify-center gap-2 transition"
              >
                <Eye className="w-4 h-4" />
                Inspect Cluster Evidence
              </button>
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
