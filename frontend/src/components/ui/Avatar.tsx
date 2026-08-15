import React from 'react';
import type { UserRole } from '../../types';

export interface AvatarProps {
  name?: string;
  role?: UserRole | string;
  size?: 'sm' | 'md' | 'lg';
}

export const Avatar: React.FC<AvatarProps> = ({ name = 'User', role, size = 'md' }) => {
  const getInitials = (n: string) => {
    const parts = n.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return n.substring(0, 2).toUpperCase();
  };

  const roleColors: Record<string, string> = {
    CITIZEN: 'bg-blue-600 border-blue-400 text-white',
    OFFICER: 'bg-purple-600 border-purple-400 text-white',
    SUPERVISOR: 'bg-amber-600 border-amber-400 text-white',
    ADMIN: 'bg-red-600 border-red-400 text-white',
  };

  const sizeStyles = {
    sm: 'w-7 h-7 text-[10px]',
    md: 'w-9 h-9 text-xs',
    lg: 'w-12 h-12 text-sm',
  };

  const colorClass = role ? roleColors[role] || 'bg-slate-700 border-slate-500 text-slate-200' : 'bg-slate-700 border-slate-500 text-slate-200';

  return (
    <div
      className={`relative inline-flex items-center justify-center rounded-xl font-bold border ${sizeStyles[size]} ${colorClass} shadow-md shrink-0 select-none`}
      title={`${name} (${role || 'User'})`}
    >
      {getInitials(name)}
    </div>
  );
};

export default Avatar;
