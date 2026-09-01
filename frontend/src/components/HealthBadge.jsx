import React from 'react';
import { Server, Database, RefreshCw, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { useSystem } from '../context/SystemContext';

export const HealthBadge = () => {
  const { isBackendConnected, dbStatus, loading, refreshHealth } = useSystem();

  // Backend Badge Styling
  const backendColor = isBackendConnected
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : 'bg-rose-50 text-rose-700 border-rose-200';

  // Database Badge Styling
  let dbColor = 'bg-rose-50 text-rose-700 border-rose-200';
  let dbText = 'Disconnected';
  let DbIcon = XCircle;

  if (dbStatus === 'connected') {
    dbColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    dbText = 'Connected';
    DbIcon = CheckCircle2;
  } else if (dbStatus === 'not_configured') {
    dbColor = 'bg-amber-50 text-amber-700 border-amber-200';
    dbText = 'Not Configured';
    DbIcon = AlertTriangle;
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs font-medium">
      {/* Backend Status Pill */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${backendColor}`}>
        <Server className="w-3.5 h-3.5" />
        <span>Backend:</span>
        <span className="font-semibold">
          {isBackendConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Database Status Pill */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${dbColor}`}>
        <Database className="w-3.5 h-3.5" />
        <span>Database:</span>
        <span className="font-semibold">{dbText}</span>
      </div>

      {/* Refresh Button */}
      <button
        onClick={refreshHealth}
        disabled={loading}
        title="Check status again"
        className="p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
};

export default HealthBadge;
