import React, { useState } from 'react';

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children }) => {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-slate-950 text-slate-200 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-slate-800 shadow-xl whitespace-nowrap z-50 pointer-events-none animate-fadeIn">
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
