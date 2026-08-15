import React from 'react';

export interface ProgressBarProps {
  progress: number; // 0 to 100
  label?: string;
  sublabel?: string;
  color?: 'blue' | 'emerald' | 'amber' | 'red' | 'purple';
  height?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  sublabel,
  color = 'blue',
  height = 'md',
}) => {
  const boundedProgress = Math.min(100, Math.max(0, progress));

  const colorStyles = {
    blue: 'bg-blue-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
  };

  const heightStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className="w-full space-y-1.5">
      {(label || sublabel) && (
        <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
          {label && <span>{label}</span>}
          {sublabel && <span className="text-slate-400 font-mono">{sublabel}</span>}
        </div>
      )}

      <div className={`w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/80 p-0.5 ${heightStyles[height]}`}>
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorStyles[color]}`}
          style={{ width: `${boundedProgress}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
