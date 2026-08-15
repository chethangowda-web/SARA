import React from 'react';
import Badge from './Badge';
import { ShieldAlert, ShieldCheck } from 'lucide-react';

export interface RiskBadgeProps {
  score?: number | null;
  size?: 'sm' | 'md';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score: rawScore, size = 'md' }) => {
  const score = rawScore ?? 0;
  let label = 'Low Risk';
  let variant: 'neutral' | 'info' | 'warning' | 'danger' = 'neutral';
  let icon = <ShieldCheck className="w-3 h-3 text-emerald-400" />;

  if (score >= 70) {
    label = `Critical Risk (${score})`;
    variant = 'danger';
    icon = <ShieldAlert className="w-3 h-3 text-red-400" />;
  } else if (score >= 40) {
    label = `Medium Risk (${score})`;
    variant = 'warning';
    icon = <ShieldAlert className="w-3 h-3 text-amber-400" />;
  } else {
    label = `Low Risk (${score})`;
    variant = 'neutral';
  }

  return (
    <Badge variant={variant} size={size} icon={icon}>
      {label}
    </Badge>
  );
};

export default RiskBadge;
