import React, { useEffect, useState } from 'react';
import { sangamApi } from '../../api/sangam';
import type { GovernmentProject } from '../../api/sangam';
import { Building2, Plus, X } from 'lucide-react';

export const InvestmentProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<GovernmentProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    project_code: `GOV-PRJ-${Math.floor(1000 + Math.random() * 9000)}`,
    name: '',
    description: '',
    category: 'WATER_SUPPLY',
    location: '',
    allocated_amount: 5000000,
    spent_amount: 0,
    status: 'PLANNED',
    source: 'VERIFIED_EXTERNAL'
  });

  const loadProjects = () => {
    setLoading(true);
    sangamApi.getProjects()
      .then(data => setProjects(data))
      .catch(err => console.error('Failed to load projects:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await sangamApi.createProject(formData);
      setShowCreateModal(false);
      loadProjects();
    } catch (err) {
      alert('Failed to create government project.');
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-emerald-400" />
            Government Investment Projects
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Tracking public works, infrastructure allocations, and completion status.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-xl flex items-center gap-2 transition self-start"
        >
          <Plus className="w-4 h-4" />
          Add Government Project
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20 text-slate-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map(project => (
            <div key={project.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between hover:border-slate-700 transition">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {project.project_code}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    project.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    project.status === 'IN_PROGRESS' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                    'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    {project.status}
                  </span>
                </div>

                <h3 className="font-bold text-slate-100 text-base mb-2">{project.name}</h3>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4">{project.description}</p>

                <div className="space-y-2 p-3 rounded-xl bg-slate-850 border border-slate-800 text-xs text-slate-300 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Category:</span>
                    <span className="font-semibold text-slate-200">{project.category}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Location:</span>
                    <span className="font-semibold text-slate-200">{project.location}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Allocation:</span>
                    <span className="font-semibold text-emerald-400">₹{project.allocated_amount.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Spent:</span>
                    <span className="font-semibold text-blue-400">₹{project.spent_amount.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                <span>Source: {project.source}</span>
                <span>{new Date(project.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-4 text-slate-100 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-lg">Add New Government Project</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-emerald-500 outline-none"
                  placeholder="e.g. Ward 12 Main Transformer Upgrade"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-emerald-500 outline-none h-20"
                  placeholder="Scope of work and targeted improvements..."
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Category</label>
                  <select
                    value={formData.category}
                    onChange={e => setFormData({...formData, category: e.target.value})}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-emerald-500 outline-none"
                  >
                    <option value="ELECTRICAL">ELECTRICAL</option>
                    <option value="WATER_SUPPLY">WATER_SUPPLY</option>
                    <option value="ROADS">ROADS</option>
                    <option value="SANITATION">SANITATION</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Location</label>
                  <input
                    type="text"
                    required
                    value={formData.location}
                    onChange={e => setFormData({...formData, location: e.target.value})}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-emerald-500 outline-none"
                    placeholder="e.g. Central Ward"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Allocated Amount (₹)</label>
                  <input
                    type="number"
                    value={formData.allocated_amount}
                    onChange={e => setFormData({...formData, allocated_amount: parseFloat(e.target.value)})}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-emerald-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={e => setFormData({...formData, status: e.target.value})}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-emerald-500 outline-none"
                  >
                    <option value="PLANNED">PLANNED</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="ON_HOLD">ON_HOLD</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg transition"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
