import React from 'react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 sm:p-12 space-y-4">
      {icon && <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/50 text-slate-400 mb-2">{icon}</div>}
      <h4 className="text-lg font-bold text-slate-200 tracking-tight">{title}</h4>
      {description && <p className="text-sm text-slate-400 max-w-md leading-relaxed">{description}</p>}
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};

export default EmptyState;
