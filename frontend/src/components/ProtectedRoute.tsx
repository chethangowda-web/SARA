import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-dark text-slate-300">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
          <p className="text-sm font-medium tracking-wider">Verifying session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-brand-dark text-slate-300">
        <div className="max-w-md w-full bg-slate-900 border border-red-500/30 rounded-2xl p-8 text-center shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-red-950/50 border border-red-500/40 flex items-center justify-center mx-auto mb-4 text-red-400 font-bold text-xl">
            !
          </div>
          <h2 className="text-xl font-bold text-red-400 mb-2">Access Denied</h2>
          <p className="text-sm text-slate-400 mb-6">
            You do not have the required permissions ({allowedRoles.join(', ')}) to view this dashboard. Your current role is <span className="font-semibold text-slate-200">{user.role}</span>.
          </p>
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => window.location.href = '/'}
              className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
            >
              Go Home
            </button>
            <button 
              onClick={() => logout()}
              className="px-4 py-2 text-xs font-semibold bg-red-600 hover:bg-red-500 text-white rounded-lg transition"
            >
              Logout & Switch User
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
export default ProtectedRoute;
