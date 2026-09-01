import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Info } from 'lucide-react';

export const SecurityEventBadge = ({ severity = 'INFO' }) => {
  const styles = {
    INFO: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    WARNING: 'bg-amber-50 text-amber-800 border-amber-200',
    ERROR: 'bg-orange-50 text-orange-800 border-orange-200',
    CRITICAL: 'bg-rose-100 text-rose-800 border-rose-300 font-extrabold animate-pulse',
  };

  const getIcon = () => {
    switch (severity) {
      case 'CRITICAL':
        return <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />;
      case 'ERROR':
      case 'WARNING':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
      default:
        return <Info className="w-3.5 h-3.5 text-indigo-600" />;
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider ${
        styles[severity] || styles.INFO
      }`}
    >
      {getIcon()}
      {severity}
    </span>
  );
};

export default SecurityEventBadge;
