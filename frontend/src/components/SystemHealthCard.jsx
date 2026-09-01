import React from 'react';
import { Activity, Database, Clock, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';

export const SystemHealthCard = ({ health = null }) => {
  if (!health) return null;

  const isHealthy = health.status === 'ok' && health.database === 'connected';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-600" />
          System Operational Health & Metrics
        </h3>
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${
            isHealthy ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
          }`}
        >
          {isHealthy ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
          {isHealthy ? 'OPERATIONAL' : 'DEGRADED'}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-indigo-600" />
            DB Latency
          </span>
          <p className="text-base font-black text-slate-800">{health.database_latency_ms || 0} ms</p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-indigo-600" />
            Uptime
          </span>
          <p className="text-base font-black text-slate-800">
            {Math.floor((health.uptime_seconds || 0) / 60)} min
          </p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5 text-indigo-600" />
            Face Model
          </span>
          <p className="text-xs font-bold text-slate-800 capitalize mt-1">
            {health.face_model || 'ready'}
          </p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-indigo-600" />
            Database
          </span>
          <p className="text-xs font-bold text-emerald-700 capitalize mt-1">
            {health.database || 'connected'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthCard;
