import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatApiError } from '../api/client';
import Button from '../components/ui/Button';
import {
  ShieldCheck,
  Cpu,
  TrendingUp,
  Lock,
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [demoMenuOpen, setDemoMenuOpen] = useState(false);

  const { login, user } = useAuth();
  const navigate = useNavigate();

  // Redirect logged-in users to their role workspace
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
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoUser = (demoEmail: string, demoPass: string = 'SARA_demo_pass_2026') => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setDemoMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col lg:flex-row text-slate-100 font-sans select-none">
      {/* Left Column: SARA Branding & Product Value */}
      <div className="lg:w-7/12 p-8 lg:p-16 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800/80 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950/40">
        {/* Background glow effects */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header */}
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-blue-950/80 border border-blue-800/60 text-blue-400 text-xs font-bold uppercase tracking-wider mb-6">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span>Official Government Portal</span>
          </div>

          <h1 className="text-4xl lg:text-6xl font-black tracking-tight text-white leading-none">
            SARA
          </h1>
          <p className="text-xl lg:text-2xl font-bold bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent mt-2">
            Smart Accountability & Resolution Assistant
          </p>
          <p className="mt-4 text-slate-400 max-w-xl text-sm lg:text-base leading-relaxed">
            Track every complaint. Understand every delay. Hold every resolution accountable through automated SLA enforcement and AI operational intelligence.
          </p>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-10 relative z-10">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2.5 rounded-xl bg-blue-600/20 text-blue-400 w-fit border border-blue-500/30">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-200">AI Classification</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Automated category detection, priority calculation, and semantic duplicate matching.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2.5 rounded-xl bg-amber-600/20 text-amber-400 w-fit border border-amber-500/30">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-200">Automated Escalation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Strict SLA tracking with automated multi-tier escalation to supervisors and leadership.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2.5 rounded-xl bg-emerald-600/20 text-emerald-400 w-fit border border-emerald-500/30">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-200">Citizen Verification</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              No grievance is closed until the citizen explicitly verifies resolution quality.
            </p>
          </div>
        </div>

        {/* Footer Security Badge */}
        <div className="relative z-10 flex items-center gap-2 text-xs text-slate-500 font-mono">
          <Lock className="w-4 h-4 text-slate-400" />
          <span>256-bit Encrypted Session • Immutable Security Audit Protocol</span>
        </div>
      </div>

      {/* Right Column: Authentication Form */}
      <div className="lg:w-5/12 p-8 lg:p-16 flex flex-col justify-center bg-slate-950 relative">
        <div className="max-w-md w-full mx-auto space-y-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Sign In to SARA</h2>
            <p className="text-sm text-slate-400 mt-1">Access your role-based governance dashboard</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 bg-red-950/60 border border-red-800/80 text-red-300 text-xs font-semibold rounded-xl space-y-1 animate-fadeIn">
                <div className="font-bold text-red-200">Authentication Error</div>
                <div>{error}</div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. citizen@sara.gov"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <a href="#forgot" onClick={(e) => { e.preventDefault(); alert("Contact system administrator to reset credentials."); }} className="text-xs text-blue-400 hover:underline">
                  Forgot Password?
                </a>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={submitting}
              className="w-full"
              icon={<ArrowRight className="w-4 h-4" />}
            >
              {submitting ? 'Authenticating Session...' : 'Sign In'}
            </Button>
          </form>

          {/* Discrete Demo Credentials Menu */}
          <div className="pt-4 border-t border-slate-800/80">
            <button
              onClick={() => setDemoMenuOpen(!demoMenuOpen)}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-slate-200 transition"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                Quick Demo Role Selector
              </span>
              <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300 font-mono">
                {demoMenuOpen ? 'Hide' : 'Show Roles'}
              </span>
            </button>

            {demoMenuOpen && (
              <div className="mt-3 p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-2 text-xs animate-fadeIn">
                <div className="text-[11px] text-slate-400 font-medium mb-1">Click any role to autofill test credentials:</div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => fillDemoUser('citizen@sara.gov')}
                    className="p-2 rounded-lg bg-blue-950/60 border border-blue-800/50 hover:bg-blue-900/60 text-blue-300 font-medium text-left transition"
                  >
                    Citizen Account
                  </button>
                  <button
                    onClick={() => fillDemoUser('officer@sara.gov')}
                    className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/50 hover:bg-purple-900/60 text-purple-300 font-medium text-left transition"
                  >
                    Officer Account
                  </button>
                  <button
                    onClick={() => fillDemoUser('supervisor@sara.gov')}
                    className="p-2 rounded-lg bg-amber-950/60 border border-amber-800/50 hover:bg-amber-900/60 text-amber-300 font-medium text-left transition"
                  >
                    Supervisor Account
                  </button>
                  <button
                    onClick={() => fillDemoUser('admin@sara.gov')}
                    className="p-2 rounded-lg bg-red-950/60 border border-red-800/50 hover:bg-red-900/60 text-red-300 font-medium text-left transition"
                  >
                    Admin Account
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
