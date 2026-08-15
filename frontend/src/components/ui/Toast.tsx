import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, X, AlertTriangle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextType {
  showToast: (title: string, message?: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (title: string, message?: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none">
        {toasts.map((toast) => {
          const config = {
            success: { bg: 'bg-emerald-950 border-emerald-800 text-emerald-300', icon: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" /> },
            error: { bg: 'bg-red-950 border-red-800 text-red-300', icon: <AlertCircle className="w-5 h-5 text-red-400 shrink-0" /> },
            warning: { bg: 'bg-amber-950 border-amber-800 text-amber-300', icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" /> },
            info: { bg: 'bg-blue-950 border-blue-800 text-blue-300', icon: <Info className="w-5 h-5 text-blue-400 shrink-0" /> },
          }[toast.type];

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto border rounded-xl p-4 shadow-2xl backdrop-blur-md flex items-start gap-3 transition-all duration-300 animate-slideUp ${config.bg}`}
            >
              {config.icon}
              <div className="flex-1">
                <div className="font-bold text-sm text-slate-100">{toast.title}</div>
                {toast.message && <div className="text-xs text-slate-300 mt-0.5">{toast.message}</div>}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-400 hover:text-white p-0.5 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};
