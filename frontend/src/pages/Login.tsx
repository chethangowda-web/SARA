import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      if (user.role === 'CITIZEN') navigate('/citizen');
      else if (user.role === 'OFFICER') navigate('/officer');
      else if (user.role === 'SUPERVISOR') navigate('/supervisor');
      else if (user.role === 'ADMIN') navigate('/admin');
    }
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-brand-dark">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <h2 className="text-3xl font-black bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          SARA
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Smart Accountability & Resolution Assistant
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900/60 backdrop-blur-md py-8 px-4 border border-slate-800 shadow-2xl sm:rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3 bg-red-950/40 border border-red-500/30 text-red-400 text-xs font-semibold rounded-lg text-center">
                {error}
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Email address
              </label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full rounded-xl bg-slate-950 border border-slate-800 text-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition"
                  placeholder="e.g. citizen@sara.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Password
              </label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-xl bg-slate-950 border border-slate-800 text-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl text-sm font-bold text-white bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 shadow-lg disabled:opacity-50 transition"
              >
                {submitting ? 'Authenticating...' : 'Sign In'}
              </button>
            </div>
          </form>

          <div className="mt-6 border-t border-slate-800/80 pt-6 text-center">
            <p className="text-xs text-slate-500">
              Demo Credentials: <span className="font-semibold text-slate-400">admin@sara.com</span> / <span className="font-semibold text-slate-400">SARA_demo_pass_2026</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
export default Login;
