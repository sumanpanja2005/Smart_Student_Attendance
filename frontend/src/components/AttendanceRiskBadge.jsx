import React from 'react';
import { AlertTriangle, CheckCircle, ShieldAlert, AlertOctagon } from 'lucide-react';

const AttendanceRiskBadge = ({ riskLevel, riskScore, riskFactors = [], showFactors = true }) => {
  const getBadgeStyle = (level) => {
    switch (level?.toUpperCase()) {
      case 'LOW':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          icon: CheckCircle,
          color: 'text-emerald-600',
          barBg: 'bg-emerald-500',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          icon: AlertTriangle,
          color: 'text-amber-600',
          barBg: 'bg-amber-500',
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-50 text-orange-800 border-orange-200',
          icon: ShieldAlert,
          color: 'text-orange-600',
          barBg: 'bg-orange-500',
        };
      case 'CRITICAL':
        return {
          bg: 'bg-rose-50 text-rose-800 border-rose-200',
          icon: AlertOctagon,
          color: 'text-rose-600',
          barBg: 'bg-rose-500',
        };
      default:
        return {
          bg: 'bg-slate-50 text-slate-700 border-slate-200',
          icon: CheckCircle,
          color: 'text-slate-600',
          barBg: 'bg-slate-400',
        };
    }
  };

  const style = getBadgeStyle(riskLevel);
  const Icon = style.icon;

  return (
    <div className="space-y-3">
      <div className={`p-4 rounded-xl border ${style.bg} flex items-center justify-between shadow-xs`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white/80 border border-current/10 ${style.color}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider">Attendance Risk Status</span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-extrabold uppercase bg-white border border-current/20">
                {riskLevel || 'LOW'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Deterministic risk score: <span className="font-semibold">{riskScore ?? 0.0} / 100</span>
            </p>
          </div>
        </div>

        {/* Risk meter bar */}
        <div className="hidden sm:block w-28">
          <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${style.barBg} transition-all duration-500`}
              style={{ width: `${Math.min(100, Math.max(0, riskScore ?? 0))}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] font-semibold text-slate-400 mt-1">
            <span>0</span>
            <span>Risk Score</span>
            <span>100</span>
          </div>
        </div>
      </div>

      {showFactors && riskFactors && riskFactors.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-indigo-600" />
            Contributing Risk Factors
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-600">
            {riskFactors.map((factor, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AttendanceRiskBadge;
