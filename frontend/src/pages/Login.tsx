import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatApiError } from '../api/client';
import Button from '../components/ui/Button';
import {
  SUPPORTED_LANGUAGES,
  getTranslation,
  type SupportedLanguage,
} from '../utils/translations';
import {
  ShieldCheck,
  Cpu,
  TrendingUp,
  Lock,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Eye,
  EyeOff,
  User,
  Briefcase,
  Users,
  Shield,
  ArrowLeft,
  Globe,
} from 'lucide-react';

export type AppRole = 'CITIZEN' | 'OFFICER' | 'SUPERVISOR' | 'ADMIN';

interface RoleConfig {
  id: AppRole;
  titleKey: string;
  descKey: string;
  detailKey: string;
  icon: React.ElementType;
  badgeBg: string;
  badgeBorder: string;
  badgeText: string;
  hoverBorder: string;
  accentGradient: string;
  demoAccount: string;
}

const ROLES: RoleConfig[] = [
  {
    id: 'CITIZEN',
    titleKey: 'citizenRole',
    descKey: 'citizenDesc',
    detailKey: 'citizenDetail',
    icon: User,
    badgeBg: 'bg-blue-950/60',
    badgeBorder: 'border-blue-800/60',
    badgeText: 'text-blue-400',
    hoverBorder: 'hover:border-blue-500/80 hover:shadow-blue-950/30',
    accentGradient: 'from-blue-600/20 via-blue-500/10 to-transparent',
    demoAccount: 'citizen@sara.gov',
  },
  {
    id: 'OFFICER',
    titleKey: 'officerRole',
    descKey: 'officerDesc',
    detailKey: 'officerDetail',
    icon: Briefcase,
    badgeBg: 'bg-purple-950/60',
    badgeBorder: 'border-purple-800/60',
    badgeText: 'text-purple-400',
    hoverBorder: 'hover:border-purple-500/80 hover:shadow-purple-950/30',
    accentGradient: 'from-purple-600/20 via-purple-500/10 to-transparent',
    demoAccount: 'officer@sara.gov',
  },
  {
    id: 'SUPERVISOR',
    titleKey: 'supervisorRole',
    descKey: 'supervisorDesc',
    detailKey: 'supervisorDetail',
    icon: Users,
    badgeBg: 'bg-amber-950/60',
    badgeBorder: 'border-amber-800/60',
    badgeText: 'text-amber-400',
    hoverBorder: 'hover:border-amber-500/80 hover:shadow-amber-950/30',
    accentGradient: 'from-amber-600/20 via-amber-500/10 to-transparent',
    demoAccount: 'supervisor@sara.gov',
  },
  {
    id: 'ADMIN',
    titleKey: 'adminRole',
    descKey: 'adminDesc',
    detailKey: 'adminDetail',
    icon: Shield,
    badgeBg: 'bg-emerald-950/60',
    badgeBorder: 'border-emerald-800/60',
    badgeText: 'text-emerald-400',
    hoverBorder: 'hover:border-emerald-500/80 hover:shadow-emerald-950/30',
    accentGradient: 'from-emerald-600/20 via-emerald-500/10 to-transparent',
    demoAccount: 'admin@sara.gov',
  },
];

export function Login() {
  const [selectedRole, setSelectedRole] = useState<AppRole | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [demoMenuOpen, setDemoMenuOpen] = useState(false);
  const [lang, setLang] = useState<SupportedLanguage>('en');

  const { login, logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const t = (key: string, params?: Record<string, string>) => getTranslation(lang, key, params);

  // Check state or URL params for role pre-selection or messages
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
    }
    if (location.state?.role) {
      const stateRole = location.state.role.toUpperCase() as AppRole;
      if (['CITIZEN', 'OFFICER', 'SUPERVISOR', 'ADMIN'].includes(stateRole)) {
        setSelectedRole(stateRole);
      }
    } else {
      const urlRole = searchParams.get('role')?.toUpperCase() as AppRole;
      if (urlRole && ['CITIZEN', 'OFFICER', 'SUPERVISOR', 'ADMIN'].includes(urlRole)) {
        setSelectedRole(urlRole);
      }
    }
  }, [location, searchParams]);

  // Auto redirect if user is already authenticated
  useEffect(() => {
    if (user) {
      if (user.role === 'CITIZEN') navigate('/citizen');
      else if (user.role === 'OFFICER') navigate('/officer');
      else if (user.role === 'SUPERVISOR') navigate('/supervisor');
      else if (user.role === 'ADMIN') navigate('/admin');
    }
  }, [user, navigate]);

  const handleSelectRole = (role: AppRole) => {
    setSelectedRole(role);
    setError(null);
    setEmail('');
    setPassword('');
  };

  const handleBackToRoles = () => {
    setSelectedRole(null);
    setError(null);
    setEmail('');
    setPassword('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRole) return;
    await doLogin(email, password);
  };

  const doLogin = async (loginEmail: string, loginPassword: string) => {
    setError(null);
    setSubmitting(true);
    try {
      // Perform backend login (retrieves JWT & UserProfile)
      await login(loginEmail, loginPassword);
    } catch (err: any) {
      setError(formatApiError(err));
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
  };

  // Enforce role check when user state updates after a login attempt
  useEffect(() => {
    if (user && selectedRole) {
      if (user.role !== selectedRole) {
        // Role Mismatch! Immediately logout and display clear error
        const actualRoleName = t(`${user.role.toLowerCase()}Role`);
        const targetRoleName = t(`${selectedRole.toLowerCase()}Role`);
        const mismatchMessage = t('roleMismatchError', {
          actualRole: actualRoleName,
          targetRole: targetRoleName,
        });

        // Perform cleanup
        logout();
        setError(mismatchMessage);
      }
    }
  }, [user, selectedRole, logout, lang]);

  const fillDemoUser = (demoEmail: string, role: AppRole, demoPass: string = 'SARA_demo_pass_2026') => {
    setSelectedRole(role);
    setEmail(demoEmail);
    setPassword(demoPass);
    setDemoMenuOpen(false);
    doLogin(demoEmail, demoPass);
  };

  const currentRoleConfig = ROLES.find((r) => r.id === selectedRole);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col lg:flex-row text-slate-100 font-sans select-none relative overflow-hidden">
      {/* Top Header Bar for Language Selection */}
      <div className="absolute top-4 right-4 z-50 flex items-center gap-2 bg-slate-900/90 border border-slate-800/80 rounded-2xl px-3 py-1.5 backdrop-blur-md shadow-lg">
        <Globe className="w-4 h-4 text-blue-400 shrink-0" />
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value as SupportedLanguage)}
          className="bg-transparent text-xs font-semibold text-slate-200 focus:outline-none cursor-pointer pr-1"
          aria-label="Select Language"
        >
          {SUPPORTED_LANGUAGES.map((l) => (
            <option key={l.code} value={l.code} className="bg-slate-900 text-slate-100">
              {l.nativeName} ({l.name})
            </option>
          ))}
        </select>
      </div>

      {/* Left Column: SARA Branding & Product Value */}
      <div className="lg:w-6/12 p-8 lg:p-14 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800/80 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950/40">
        {/* Background glow effects */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header */}
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-blue-950/80 border border-blue-800/60 text-blue-400 text-xs font-bold uppercase tracking-wider mb-6">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span>{t('portalBadge')}</span>
          </div>

          <h1 className="text-4xl lg:text-6xl font-black tracking-tight text-white leading-none">
            {t('appTitle')}
          </h1>
          <p className="text-xl lg:text-2xl font-bold bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent mt-2">
            {t('appSubtitle')}
          </p>
          <p className="mt-4 text-slate-400 max-w-xl text-sm lg:text-base leading-relaxed">
            Track every complaint. Understand every delay. Hold every resolution accountable through automated SLA enforcement and AI operational intelligence.
          </p>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-8 relative z-10">
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2 rounded-xl bg-blue-600/20 text-blue-400 w-fit border border-blue-500/30">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-xs text-slate-200">AI Classification</h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Automated category detection, priority calculation, and semantic duplicate matching.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2 rounded-xl bg-amber-600/20 text-amber-400 w-fit border border-amber-500/30">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-xs text-slate-200">Automated Escalation</h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Strict SLA tracking with automated multi-tier escalation to supervisors.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md space-y-2 hover:border-slate-700/80 transition">
            <div className="p-2 rounded-xl bg-emerald-600/20 text-emerald-400 w-fit border border-emerald-500/30">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-xs text-slate-200">Citizen Verification</h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
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

      {/* Right Column: Dynamic Role Selection OR Role Login Form */}
      <div className="lg:w-6/12 p-8 lg:p-14 flex flex-col justify-center bg-slate-950 relative">
        <div className="max-w-lg w-full mx-auto space-y-6 pt-6 lg:pt-0">
          
          {/* Messages */}
          {successMessage && (
            <div className="p-4 bg-emerald-950/70 border border-emerald-800/80 text-emerald-300 text-xs font-semibold rounded-2xl space-y-1 animate-fadeIn">
              <div className="font-bold text-emerald-200">Success</div>
              <div>{successMessage}</div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-950/70 border border-red-800/80 text-red-300 text-xs font-semibold rounded-2xl space-y-1.5 animate-fadeIn shadow-lg shadow-red-950/40">
              <div className="font-bold text-red-200 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-red-400" />
                <span>Authentication Error</span>
              </div>
              <div className="leading-relaxed">{error}</div>
            </div>
          )}

          {/* SCREEN 1: ROLE SELECTION CARDS */}
          {selectedRole === null ? (
            <div className="space-y-6 animate-fadeIn">
              <div className="space-y-1">
                <h2 className="text-2xl lg:text-3xl font-black text-slate-100 tracking-tight">
                  {t('welcomeHeading')}
                </h2>
                <p className="text-sm font-semibold text-blue-400">
                  {t('chooseAccess')}
                </p>
              </div>

              {/* 4 Role Selection Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {ROLES.map((role) => {
                  const IconComp = role.icon;
                  const title = t(role.titleKey);
                  const desc = t(role.descKey);
                  const detail = t(role.detailKey);

                  return (
                    <div
                      key={role.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleSelectRole(role.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleSelectRole(role.id);
                        }
                      }}
                      className={`group relative p-5 rounded-3xl bg-slate-900/70 border border-slate-800/90 hover:bg-slate-900 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-lg ${role.hoverBorder} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                      aria-label={`Select ${title} Role: ${desc}`}
                    >
                      {/* Top icon and role badge */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <div className={`p-3 rounded-2xl ${role.badgeBg} ${role.badgeBorder} border ${role.badgeText} group-hover:scale-105 transition-transform duration-200`}>
                            <IconComp className="w-6 h-6" />
                          </div>
                          <span className="text-[10px] font-bold tracking-widest text-slate-500 uppercase font-mono group-hover:text-slate-300 transition-colors">
                            {role.id}
                          </span>
                        </div>

                        <h3 className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors flex items-center gap-1.5">
                          {title}
                        </h3>
                        
                        <p className="text-xs font-semibold text-slate-300 mt-1 leading-snug">
                          {desc}
                        </p>
                        
                        <p className="text-[11px] text-slate-500 mt-2 leading-relaxed font-normal">
                          {detail}
                        </p>
                      </div>

                      {/* Bottom action indicator */}
                      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs font-bold text-slate-400 group-hover:text-blue-400 transition-colors">
                        <span>Select Role</span>
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="text-center text-xs text-slate-400 pt-2">
                Need to file a public complaint as a new citizen?{' '}
                <Link to="/signup" className="text-blue-400 hover:underline font-bold transition-colors">
                  {t('createCitizenAccount')}
                </Link>
              </div>
            </div>
          ) : (
            /* SCREEN 2: ROLE-SPECIFIC LOGIN FORM */
            <div className="space-y-6 animate-fadeIn">
              {/* Back Button & Selected Role Header */}
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                <button
                  type="button"
                  onClick={handleBackToRoles}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-slate-200 transition py-1 px-2.5 rounded-xl hover:bg-slate-900 border border-transparent hover:border-slate-800"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>{t('backToRoles')}</span>
                </button>

                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${currentRoleConfig?.badgeBg} ${currentRoleConfig?.badgeBorder} border ${currentRoleConfig?.badgeText} text-xs font-bold`}>
                  {currentRoleConfig && <currentRoleConfig.icon className="w-3.5 h-3.5" />}
                  <span>{t(currentRoleConfig?.titleKey || '')} Login</span>
                </div>
              </div>

              {/* Header Title for Active Role */}
              <div>
                <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
                  {currentRoleConfig && <currentRoleConfig.icon className="w-6 h-6 text-blue-400" />}
                  <span>{t(currentRoleConfig?.titleKey || '')} Login</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  {t(
                    selectedRole === 'CITIZEN'
                      ? 'citizenSignInSub'
                      : selectedRole === 'OFFICER'
                      ? 'officerSignInSub'
                      : selectedRole === 'SUPERVISOR'
                      ? 'supervisorSignInSub'
                      : 'adminSignInSub'
                  )}
                </p>
              </div>

              {/* Login Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                    {t('emailLabel')}
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={currentRoleConfig?.demoAccount || 'e.g. user@sara.gov'}
                    className="w-full bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                      {t('passwordLabel')}
                    </label>
                    <a
                      href="#forgot"
                      onClick={(e) => {
                        e.preventDefault();
                        alert('Contact system administrator to reset credentials.');
                      }}
                      className="text-xs text-blue-400 hover:underline"
                    >
                      {t('forgotPassword')}
                    </a>
                  </div>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={t('passwordPlaceholder')}
                      className="w-full bg-slate-900 border border-slate-800 rounded-2xl pl-4 pr-12 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 focus:outline-none"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4.5 h-4.5" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-400 hover:text-slate-300 select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-800 bg-slate-900 text-blue-600 focus:ring-blue-500"
                    />
                    <span>{t('rememberMe')}</span>
                  </label>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  loading={submitting}
                  className="w-full shadow-lg shadow-blue-950/50"
                  icon={<ArrowRight className="w-4 h-4" />}
                >
                  {submitting ? t('authenticating') : `${t('signInBtn')} (${t(currentRoleConfig?.titleKey || '')})`}
                </Button>

                {selectedRole === 'CITIZEN' && (
                  <div className="text-center text-xs text-slate-400 mt-3">
                    {t('noAccount')}{' '}
                    <Link to="/signup" className="text-blue-400 hover:underline font-bold transition-colors">
                      {t('createCitizenAccount')}
                    </Link>
                  </div>
                )}
              </form>
            </div>
          )}

          {/* Quick Demo Credentials Menu */}
          <div className="pt-4 border-t border-slate-800/80">
            <button
              onClick={() => setDemoMenuOpen(!demoMenuOpen)}
              className="w-full flex items-center justify-between p-3 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-slate-200 transition"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>{t('quickDemoMenu')}</span>
              </span>
              <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300 font-mono">
                {demoMenuOpen ? t('hideDemo') : t('showDemo')}
              </span>
            </button>

            {demoMenuOpen && (
              <div className="mt-3 p-3.5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3 text-xs animate-fadeIn max-h-72 overflow-y-auto">
                <div className="text-[11px] text-slate-400 font-medium">{t('clickToAutofill')}</div>

                {/* Citizen */}
                <div className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-blue-400">Citizen</div>
                  <button
                    onClick={() => fillDemoUser('citizen@sara.gov', 'CITIZEN')}
                    className="w-full p-2 rounded-xl bg-blue-950/60 border border-blue-800/50 hover:bg-blue-900/60 text-blue-300 font-medium text-left transition text-xs flex items-center justify-between"
                  >
                    <span>👤 Citizen Account</span>
                    <span className="text-[10px] font-mono opacity-75">citizen@sara.gov</span>
                  </button>
                </div>

                {/* Officer */}
                <div className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-purple-400">Officers</div>
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => fillDemoUser('officer@sara.gov', 'OFFICER')}
                      className="p-2 rounded-xl bg-purple-950/60 border border-purple-800/50 hover:bg-purple-900/60 text-purple-300 font-medium text-left transition text-[11px]"
                    >
                      ⚡ Electrical Officer
                    </button>
                    <button
                      onClick={() => fillDemoUser('water.officer@sara.gov', 'OFFICER')}
                      className="p-2 rounded-xl bg-purple-950/60 border border-purple-800/50 hover:bg-purple-900/60 text-purple-300 font-medium text-left transition text-[11px]"
                    >
                      💧 Water Officer
                    </button>
                    <button
                      onClick={() => fillDemoUser('roads.officer01@sara.gov', 'OFFICER')}
                      className="p-2 rounded-xl bg-purple-950/60 border border-purple-800/50 hover:bg-purple-900/60 text-purple-300 font-medium text-left transition text-[11px]"
                    >
                      🛣️ Roads Officer
                    </button>
                    <button
                      onClick={() => fillDemoUser('sanitation.officer@sara.gov', 'OFFICER')}
                      className="p-2 rounded-xl bg-purple-950/60 border border-purple-800/50 hover:bg-purple-900/60 text-purple-300 font-medium text-left transition text-[11px]"
                    >
                      🧹 Sanitation Officer
                    </button>
                  </div>
                </div>

                {/* Supervisor */}
                <div className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400">Supervisors</div>
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => fillDemoUser('supervisor@sara.gov', 'SUPERVISOR')}
                      className="p-2 rounded-xl bg-amber-950/60 border border-amber-800/50 hover:bg-amber-900/60 text-amber-300 font-medium text-left transition text-[11px]"
                    >
                      ⚡ Electrical Sup.
                    </button>
                    <button
                      onClick={() => fillDemoUser('water.supervisor@sara.gov', 'SUPERVISOR')}
                      className="p-2 rounded-xl bg-amber-950/60 border border-amber-800/50 hover:bg-amber-900/60 text-amber-300 font-medium text-left transition text-[11px]"
                    >
                      💧 Water Sup.
                    </button>
                  </div>
                </div>

                {/* Admin */}
                <div className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">System Admin</div>
                  <button
                    onClick={() => fillDemoUser('admin@sara.gov', 'ADMIN')}
                    className="w-full p-2 rounded-xl bg-emerald-950/60 border border-emerald-800/50 hover:bg-emerald-900/60 text-emerald-300 font-medium text-left transition text-xs flex items-center justify-between"
                  >
                    <span>🛡️ System Admin</span>
                    <span className="text-[10px] font-mono opacity-75">admin@sara.gov</span>
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
