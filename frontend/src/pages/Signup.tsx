import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
  Lock,
  ArrowRight,
  UserPlus,
  Eye,
  EyeOff,
  Globe,
  Phone,
  User,
  Mail,
} from 'lucide-react';

export function Signup() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState<SupportedLanguage>('en');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { signup } = useAuth();
  const navigate = useNavigate();

  const t = (key: string, params?: Record<string, string>) => getTranslation(preferredLanguage, key, params);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validations
    if (!fullName.trim() || !email.trim() || !password || !confirmPassword) {
      setError(t('allFieldsRequired'));
      return;
    }

    if (password.length < 8) {
      setError(t('passwordLengthError'));
      return;
    }

    if (password !== confirmPassword) {
      setError(t('passwordsDoNotMatch'));
      return;
    }

    setSubmitting(true);
    try {
      await signup(fullName.trim(), email.trim(), password, preferredLanguage);
      
      // On success: redirect to login with Citizen role selected & success message
      navigate('/login', {
        state: {
          message: t('signupSuccess'),
          role: 'CITIZEN',
        },
      });
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 lg:p-8 text-slate-100 font-sans select-none relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full bg-slate-900/70 border border-slate-800/90 backdrop-blur-md rounded-3xl p-6 lg:p-8 shadow-2xl relative z-10 my-6">
        {/* Top Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950/80 border border-blue-800/60 text-blue-400 text-[10px] font-bold uppercase tracking-wider mb-3 mx-auto">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span>{t('portalBadge')}</span>
          </div>

          <h2 className="text-2xl lg:text-3xl font-black tracking-tight text-white leading-none">
            {t('signupTitle')}
          </h2>
          <p className="text-xs text-slate-400 mt-2">
            {t('signupSubtitle')}
          </p>
        </div>

        {/* Public Citizen Signup Notice */}
        <div className="p-3 mb-5 bg-blue-950/40 border border-blue-800/40 rounded-2xl flex items-start gap-2.5 text-xs text-blue-300">
          <UserPlus className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{t('signupNote')}</span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3.5 bg-red-950/70 border border-red-800/80 text-red-300 text-xs font-semibold rounded-2xl space-y-1 animate-fadeIn">
              <div className="font-bold text-red-200">Registration Issue</div>
              <div>{error}</div>
            </div>
          )}

          {/* Full Name */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              {t('fullNameLabel')}
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder={t('fullNamePlaceholder')}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-2xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          {/* Email Address */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              {t('emailLabel')}
            </label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('emailPlaceholder')}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-2xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          {/* Phone Number (Optional/Supported) */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              {t('phoneLabel')} <span className="text-[10px] text-slate-500 font-normal">(Optional)</span>
            </label>
            <div className="relative">
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder={t('phonePlaceholder')}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-2xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
              <Phone className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          {/* Preferred Language */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              {t('preferredLangLabel')}
            </label>
            <div className="relative">
              <select
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value as SupportedLanguage)}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-2xl pl-10 pr-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 appearance-none transition"
              >
                {SUPPORTED_LANGUAGES.map((langOpt) => (
                  <option key={langOpt.code} value={langOpt.code} className="bg-slate-900 text-slate-100">
                    {langOpt.nativeName} ({langOpt.name})
                  </option>
                ))}
              </select>
              <Globe className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              {t('passwordLabel')}
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full bg-slate-950/60 border border-slate-800 rounded-2xl pl-4 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 focus:outline-none"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              {t('confirmPasswordLabel')}
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t('confirmPasswordPlaceholder')}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-2xl pl-4 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 focus:outline-none"
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={submitting}
            className="w-full mt-3 shadow-lg shadow-blue-950/50"
            icon={<ArrowRight className="w-4 h-4" />}
          >
            {submitting ? t('creatingProfile') : t('signUpBtn')}
          </Button>

          <div className="text-center text-xs text-slate-400 mt-4">
            {t('alreadyHaveAccount')}{' '}
            <Link to="/login" className="text-blue-400 hover:underline font-bold transition-colors duration-150">
              {t('signInBtn')}
            </Link>
          </div>
        </form>

        {/* Footer Security Badge */}
        <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-center gap-2 text-[10px] text-slate-500 font-mono text-center">
          <Lock className="w-3 h-3 text-slate-400" />
          <span>Immutable Security Audit Protocol Active</span>
        </div>
      </div>
    </div>
  );
}

export default Signup;
