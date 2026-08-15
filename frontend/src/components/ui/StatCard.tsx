import React from 'react';
import { Card } from './Card';

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: React.ReactNode;
  icon?: React.ReactNode;
  trend?: {
    label: string;
    positive?: boolean;
  };
  colorScheme?: 'blue' | 'emerald' | 'amber' | 'purple' | 'red' | 'cyan' | 'slate';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  colorScheme = 'blue',
}) => {
  const colorStyles = {
    blue: {
      bg: 'from-blue-600/10 to-blue-900/5',
      border: 'border-blue-500/20',
      iconBg: 'bg-blue-950/80 border-blue-800/60 text-blue-400',
      value: 'text-white',
    },
    emerald: {
      bg: 'from-emerald-600/10 to-emerald-900/5',
      border: 'border-emerald-500/20',
      iconBg: 'bg-emerald-950/80 border-emerald-800/60 text-emerald-400',
      value: 'text-emerald-400',
    },
    amber: {
      bg: 'from-amber-600/10 to-amber-900/5',
      border: 'border-amber-500/20',
      iconBg: 'bg-amber-950/80 border-amber-800/60 text-amber-400',
      value: 'text-amber-400',
    },
    purple: {
      bg: 'from-purple-600/10 to-purple-900/5',
      border: 'border-purple-500/20',
      iconBg: 'bg-purple-950/80 border-purple-800/60 text-purple-400',
      value: 'text-purple-400',
    },
    red: {
      bg: 'from-red-600/10 to-red-900/5',
      border: 'border-red-500/20',
      iconBg: 'bg-red-950/80 border-red-800/60 text-red-400',
      value: 'text-red-400',
    },
    cyan: {
      bg: 'from-cyan-600/10 to-cyan-900/5',
      border: 'border-cyan-500/20',
      iconBg: 'bg-cyan-950/80 border-cyan-800/60 text-cyan-400',
      value: 'text-cyan-400',
    },
    slate: {
      bg: 'from-slate-800/20 to-slate-900/20',
      border: 'border-slate-800',
      iconBg: 'bg-slate-800 text-slate-400 border-slate-700',
      value: 'text-slate-200',
    },
  };

  const current = colorStyles[colorScheme];

  return (
    <Card className={`p-5 bg-gradient-to-br ${current.bg} ${current.border} relative overflow-hidden`}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
          <div className={`text-2xl sm:text-3xl font-black ${current.value} tracking-tight font-mono`}>{value}</div>
        </div>

        {icon && (
          <div className={`p-2.5 rounded-xl border ${current.iconBg} shadow-sm shrink-0`}>
            {icon}
          </div>
        )}
      </div>

      {(subtitle || trend) && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/40 flex items-center justify-between text-xs text-slate-400">
          {subtitle && <div>{subtitle}</div>}
          {trend && (
            <span
              className={`font-semibold px-2 py-0.5 rounded-md text-[11px] ${
                trend.positive ? 'bg-emerald-950/60 text-emerald-400' : 'bg-red-950/60 text-red-400'
              }`}
            >
              {trend.label}
            </span>
          )}
        </div>
      )}
    </Card>
  );
};

export default StatCard;
