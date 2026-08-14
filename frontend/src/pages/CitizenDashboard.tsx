import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchCitizenDashboard } from '../api/grievances';
import { apiFetch } from '../api/client';

export function CitizenDashboard() {
  const { user, logout } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [formError, setFormError] = useState('');

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const res = await fetchCitizenDashboard();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    try {
      await apiFetch('/grievances', {
        method: 'POST',
        body: JSON.stringify({ title, description, location })
      });
      setTitle('');
      setDescription('');
      setLocation('');
      loadDashboard();
    } catch (err: any) {
      setFormError(err.message || 'Failed to submit grievance');
    }
  };

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
      
      <main className="max-w-4xl mx-auto p-6 mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Submit Form */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
          <h2 className="text-lg font-bold mb-4">Report a Grievance</h2>
          {formError && <div className="text-red-400 text-xs mb-3">{formError}</div>}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input 
              type="text" 
              placeholder="Title" 
              required
              className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
            <textarea 
              placeholder="Description" 
              required
              rows={3}
              className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
            <input 
              type="text" 
              placeholder="Location" 
              required
              className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
              value={location}
              onChange={e => setLocation(e.target.value)}
            />
            <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded text-sm transition">
              Submit
            </button>
          </form>
        </div>

        {/* Dashboard Stats */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-col gap-4">
          <h2 className="text-lg font-bold">Your Grievances</h2>
          {loading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400 text-xs">Total</span>
                <div className="text-2xl font-black">{data?.total_grievances || 0}</div>
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-sm font-semibold">Recent</span>
                {data?.recent_grievances?.map((g: any) => (
                  <div key={g.id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-sm flex justify-between items-center">
                    <div>
                      <div className="font-bold">{g.title}</div>
                      <div className="text-xs text-slate-500">{g.id.substring(0,8)}</div>
                    </div>
                    <span className="px-2 py-1 bg-slate-800 text-xs rounded text-blue-400">{g.current_state}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

      </main>
    </div>
  );
}
export default CitizenDashboard;
