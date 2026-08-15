import React from 'react';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'card' | 'avatar' | 'rect';
}

export const Skeleton: React.FC<SkeletonProps> = ({ variant = 'rect', className = '', ...props }) => {
  const variantStyles = {
    text: 'h-4 w-3/4 rounded-md',
    card: 'h-40 w-full rounded-2xl',
    avatar: 'h-10 w-10 rounded-xl',
    rect: 'h-12 w-full rounded-xl',
  };

  return (
    <div
      className={`bg-slate-800/60 animate-pulse ${variantStyles[variant]} ${className}`}
      {...props}
    />
  );
};

export default Skeleton;
