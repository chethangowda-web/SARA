import React from 'react';
import type { Priority } from '../../types';
import Badge from './Badge';
import { AlertCircle, AlertTriangle, ArrowUpRight, Flame } from 'lucide-react';

export interface PriorityBadgeProps {
  priority?: Priority | string | null;
  size?: 'sm' | 'md';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority = 'MEDIUM', size = 'md' }) => {
  const normalized = String(priority).toUpperCase();

  const config: Record<string, { label: string; variant: 'neutral' | 'info' | 'warning' | 'danger'; icon: React.ReactNode }> = {
    LOW: { label: 'Low', variant: 'neutral', icon: <ArrowUpRight className="w-3 h-3 text-slate-400" /> },
    MEDIUM: { label: 'Medium', variant: 'info', icon: <AlertCircle className="w-3 h-3 text-cyan-400" /> },
    HIGH: { label: 'High Priority', variant: 'warning', icon: <AlertTriangle className="w-3 h-3 text-amber-400" /> },
    CRITICAL: { label: 'Critical Priority', variant: 'danger', icon: <Flame className="w-3 h-3 text-red-400" /> },
  };

  const current = config[normalized] || { label: normalized, variant: 'neutral', icon: <AlertCircle className="w-3 h-3" /> };

  return (
    <Badge variant={current.variant} size={size} icon={current.icon}>
      {current.label}
    </Badge>
  );
};

export default PriorityBadge;
