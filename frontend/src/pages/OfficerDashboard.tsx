import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchOfficerDashboard } from '../api/grievances';

export function OfficerDashboard() {
  const { user, logout } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOfficerDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-brand-dark text-slate-200">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-black bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          SARA
        </h1>
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400">
            Welcome, <strong className="text-slate-300">{user?.full_name}</strong> ({user?.role})
          </span>
          <button 
            onClick={() => logout()}
            className="px-3 py-1.5 text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
          >
            Logout
          </button>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto p-6 mt-10">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-950/40 border border-purple-500/20 text-xs font-semibold text-purple-400 rounded-full mb-4">
            Authorized Officer Zone
          </div>
          <h2 className="text-2xl font-bold mb-4">Officer Dashboard</h2>
          
          {loading ? (
            <div className="text-slate-400">Loading...</div>
          ) : (
            <div className="flex flex-col gap-4 mt-6">
              <h3 className="text-lg font-bold">Assigned Grievances</h3>
              {data?.assigned_grievances?.length === 0 && (
                <div className="text-slate-500 text-sm">No grievances assigned to you.</div>
              )}
              {data?.assigned_grievances?.map((g: any) => (
                <div key={g.id} className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-sm flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-bold text-base text-blue-100">{g.title}</div>
                      <div className="text-xs text-slate-500 font-mono mt-1">{g.id}</div>
                    </div>
                    <span className="px-2 py-1 bg-purple-900/50 text-xs rounded text-purple-300 border border-purple-700/50">{g.current_state}</span>
                  </div>
                  <p className="text-slate-400 text-xs line-clamp-2 mt-2">{g.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
export default OfficerDashboard;
