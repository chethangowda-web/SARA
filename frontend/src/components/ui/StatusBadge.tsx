import React from 'react';
import type { GrievanceState } from '../../types';
import Badge from './Badge';
import {
  FileText,
  Cpu,
  CornerUpRight,
  UserCheck,
  CheckCircle2,
  Clock,
  Send,
  ShieldAlert,
  CheckCheck,
  RotateCcw,
} from 'lucide-react';

export interface StatusBadgeProps {
  state: GrievanceState | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ state, size = 'md' }) => {
  const config: Record<
    string,
    { label: string; variant: 'neutral' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'purple'; icon: React.ReactNode }
  > = {
    SUBMITTED: { label: 'Submitted', variant: 'neutral', icon: <FileText className="w-3.5 h-3.5" /> },
    CLASSIFIED: { label: 'AI Classified', variant: 'info', icon: <Cpu className="w-3.5 h-3.5" /> },
    ROUTED: { label: 'Routed', variant: 'info', icon: <CornerUpRight className="w-3.5 h-3.5" /> },
    ASSIGNED: { label: 'Officer Assigned', variant: 'purple', icon: <UserCheck className="w-3.5 h-3.5" /> },
    ACKNOWLEDGED: { label: 'Acknowledged', variant: 'primary', icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
    IN_PROGRESS: { label: 'In Progress', variant: 'warning', icon: <Clock className="w-3.5 h-3.5 animate-pulse" /> },
    RESOLUTION_SUBMITTED: { label: 'Resolution Submitted', variant: 'info', icon: <Send className="w-3.5 h-3.5" /> },
    VERIFICATION: { label: 'Citizen Verification', variant: 'warning', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
    CLOSED: { label: 'Closed / Resolved', variant: 'success', icon: <CheckCheck className="w-3.5 h-3.5" /> },
    REOPENED: { label: 'Reopened', variant: 'danger', icon: <RotateCcw className="w-3.5 h-3.5" /> },
  };

  const current = config[state] || { label: state, variant: 'neutral', icon: <FileText className="w-3.5 h-3.5" /> };

  return (
    <Badge variant={current.variant} size={size} icon={current.icon}>
      {current.label}
    </Badge>
  );
};

export default StatusBadge;
