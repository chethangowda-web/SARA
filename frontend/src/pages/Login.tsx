import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiFetch, formatApiError, setLocalAccessToken } from '../api/client';
import Button from '../components/ui/Button';
import { ShieldCheck, Cpu, TrendingUp, Lock, ArrowRight, CheckCircle2, User, Key, Globe, Eye, EyeOff } from 'lucide-react';

type PortalRole = 'CITIZEN' | 'OFFICER' | 'SUPERVISOR' | 'ADMIN';

export function Login() {
  const [selectedRole, setSelectedRole] = useState<PortalRole>('CITIZEN');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [googleEmailInput, setGoogleEmailInput] = useState('');

  const { login, user, refreshAccessToken } = useAuth();
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

  const handleGoogleLogin = async (googleEmail: string) => {
    setError(null);
    setSubmitting(true);
    setShowGoogleModal(false);
    try {
      // Simulate ID token generation: mock_token_{role}_{email}
      const mockRole = googleEmail === 'iamchethen2813@gmail.com' ? 'admin' 
        : ['prajwals2006ps@gmail.com', 'dmsudeepreddy17@gmail.com', 'bhoomija24@gmail.com'].includes(googleEmail) ? 'supervisor'
        : ['priyankah.4767@gmail.com', 'charanavs04@gmail.com'].includes(googleEmail) ? 'officer' : 'citizen';
        
      const idToken = `mock_token_${mockRole}_${googleEmail}`;
      
      const data = await apiFetch<{ access_token: string; user: any }>('/auth/google', {
        method: 'POST',
        body: JSON.stringify({ id_token: idToken }),
      });

      // Update state in AuthContext directly by utilizing a local refresh
      setLocalAccessToken(data.access_token);
      await refreshAccessToken();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col lg:flex-row text-slate-100 font-sans select-none">
      {/* Left Column: SARA Branding */}
      <div className="lg:w-7/12 p-8 lg:p-16 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800/80 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950/40">
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

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
            Secure Government Grievance & Accountability Platform. Track complaints, enforce SLAs, and monitor accountability metrics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-10 relative z-10">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2.5 rounded-xl bg-blue-600/20 text-blue-400 w-fit border border-blue-500/30">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-200">AI Classification</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Automated grievance routing and priority verification.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2.5 rounded-xl bg-amber-600/20 text-amber-400 w-fit border border-amber-500/30">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-200">SLA Enforcement</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Automated reminders and supervisors oversight dossiers.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2.5 rounded-xl bg-emerald-600/20 text-emerald-400 w-fit border border-emerald-500/30">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-200">Integrity Check</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Direct verification loops with citizens before case closure.
            </p>
          </div>
        </div>

        <div className="relative z-10 flex items-center gap-2 text-xs text-slate-500 font-mono">
          <Lock className="w-4 h-4 text-slate-400" />
          <span>Secure AES Session • Production-Grade Server Audit Protocol</span>
        </div>
      </div>

      {/* Right Column: Portal Cards & Sign In */}
      <div className="lg:w-5/12 p-8 lg:p-16 flex flex-col justify-center bg-slate-950 relative">
        <div className="max-w-md w-full mx-auto space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Sign In to SARA</h2>
            <p className="text-sm text-slate-400 mt-1">Select your portal role to access your dashboard</p>
          </div>

          {/* Portal Tabs */}
          <div className="grid grid-cols-4 gap-1 p-1 bg-slate-900 border border-slate-800 rounded-xl">
            {(['CITIZEN', 'OFFICER', 'SUPERVISOR', 'ADMIN'] as PortalRole[]).map((role) => (
              <button
                key={role}
                onClick={() => {
                  setSelectedRole(role);
                  setError(null);
                }}
                className={`py-2 text-[10px] sm:text-xs font-bold rounded-lg transition uppercase tracking-wider ${
                  selectedRole === role
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                {role.toLowerCase()}
              </button>
            ))}
          </div>

          {/* Restriction Notice for Staff */}
          {selectedRole !== 'CITIZEN' && (
            <div className="p-3.5 bg-amber-950/40 border border-amber-900/60 rounded-xl flex items-start gap-2.5 text-xs text-amber-300">
              <Lock className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
              <div>
                <span className="font-bold">Authorized Access Only:</span> Access is strictly restricted to authorized government personnel. Public registration is disabled.
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
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
              <div className="relative">
                <User className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={`name@${selectedRole === 'CITIZEN' ? 'domain' : 'sara'}.gov`}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <a
                  href="#forgot"
                  onClick={(e) => {
                    e.preventDefault();
                    alert("Please contact the administrator or use the forgot password flow.");
                  }}
                  className="text-xs text-blue-400 hover:underline"
                >
                  Forgot Password?
                </a>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-10 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 transition"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={submitting}
              className="w-full"
              icon={<ArrowRight className="w-4 h-4" />}
            >
              {submitting ? 'Authenticating Session...' : `Sign In as ${selectedRole.toLowerCase()}`}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative flex items-center justify-center py-2">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800/80"></div>
            </div>
            <span className="relative px-3 bg-slate-950 text-xs text-slate-500 font-semibold uppercase tracking-wider">
              Or
            </span>
          </div>

          {/* Google Sign In */}
          <Button
            type="button"
            variant="secondary"
            size="lg"
            className="w-full justify-center bg-slate-900 border-slate-800 hover:bg-slate-800 text-slate-200"
            onClick={() => setShowGoogleModal(true)}
            icon={<Globe className="w-4 h-4 text-blue-400" />}
          >
            Continue with Google
          </Button>

          {/* Bottom links */}
          <div className="text-center pt-2 text-xs text-slate-400 space-y-1">
            {selectedRole === 'CITIZEN' ? (
              <div>
                Don't have an account?{' '}
                <Link to="/register" className="text-blue-400 hover:underline font-semibold">
                  Create Citizen Account
                </Link>
              </div>
            ) : (
              <div className="text-[11px] text-slate-500">
                Staff accounts must be pre-authorized. Contact admin if you cannot access.
              </div>
            )}
            <div>
              <Link to="/verify-email" className="text-slate-500 hover:text-slate-300 hover:underline">
                Need to verify registration code?
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Google Login Simulation Modal */}
      {showGoogleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl relative">
            <div className="text-center space-y-2">
              <h3 className="text-lg font-bold text-white">Google Sign-In Simulation</h3>
              <p className="text-xs text-slate-400">
                Select an account or input a custom email to authenticate as a secure Google Identity
              </p>
            </div>

            <div className="space-y-2 pt-2">
              <div className="text-[11px] text-slate-500 uppercase tracking-wider font-bold">Authorized Staff Accounts</div>
              
              <button
                onClick={() => handleGoogleLogin('iamchethen2813@gmail.com')}
                className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-red-500/50 text-left hover:bg-slate-800/40 transition flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-bold text-slate-200">iamchethen2813@gmail.com</div>
                  <div className="text-[10px] text-slate-500">System Admin</div>
                </div>
                <span className="px-2 py-0.5 bg-red-950 text-red-400 text-[10px] rounded border border-red-900/50">Admin</span>
              </button>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleGoogleLogin('prajwals2006ps@gmail.com')}
                  className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/50 text-left hover:bg-slate-800/40 transition"
                >
                  <div className="text-xs font-bold text-slate-200 truncate">prajwals2006ps</div>
                  <div className="text-[9px] text-slate-500">Supervisor</div>
                </button>
                <button
                  onClick={() => handleGoogleLogin('bhoomija24@gmail.com')}
                  className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/50 text-left hover:bg-slate-800/40 transition"
                >
                  <div className="text-xs font-bold text-slate-200 truncate">bhoomija24</div>
                  <div className="text-[9px] text-slate-500">Supervisor</div>
                </button>
                <button
                  onClick={() => handleGoogleLogin('priyankah.4767@gmail.com')}
                  className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-purple-500/50 text-left hover:bg-slate-800/40 transition"
                >
                  <div className="text-xs font-bold text-slate-200 truncate">priyankah.4767</div>
                  <div className="text-[9px] text-slate-500">Officer</div>
                </button>
                <button
                  onClick={() => handleGoogleLogin('charanavs04@gmail.com')}
                  className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-purple-500/50 text-left hover:bg-slate-800/40 transition"
                >
                  <div className="text-xs font-bold text-slate-200 truncate">charanavs04</div>
                  <div className="text-[9px] text-slate-500">Officer</div>
                </button>
              </div>

              <div className="relative flex items-center justify-center py-1">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800/80"></div></div>
                <span className="relative px-2 bg-slate-900 text-[10px] text-slate-500">Or custom email</span>
              </div>

              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="custom.email@gmail.com"
                  value={googleEmailInput}
                  onChange={(e) => setGoogleEmailInput(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition"
                />
                <button
                  onClick={() => googleEmailInput && handleGoogleLogin(googleEmailInput)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-xs font-bold rounded-xl text-white transition shrink-0"
                >
                  Verify
                </button>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800/80">
              <button
                onClick={() => setShowGoogleModal(false)}
                className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Login;
