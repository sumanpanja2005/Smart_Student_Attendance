import React from 'react';
import { TrendingUp, Calendar } from 'lucide-react';

const AttendanceTrendChart = ({ points = [], periodType = 'daily', onPeriodChange }) => {
  if (!points || points.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 text-center shadow-xs">
        <TrendingUp className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-sm font-semibold text-slate-600">No Attendance Trend Data Available</p>
        <p className="text-xs text-slate-400 mt-1">Complete attendance sessions will generate trend history here.</p>
      </div>
    );
  }

  const maxPct = 100;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            Attendance Percentage Trend
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Chronological attendance tracking across sessions</p>
        </div>

        {onPeriodChange && (
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
            {['daily', 'weekly', 'monthly'].map((type) => (
              <button
                key={type}
                onClick={() => onPeriodChange(type)}
                className={`px-3 py-1 rounded-md capitalize transition-colors ${
                  periodType === type ? 'bg-white text-indigo-600 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Visual Bar Chart */}
      <div className="space-y-3 pt-2">
        <div className="h-40 flex items-end justify-between gap-2 px-2 border-b border-slate-200 pb-2">
          {points.slice(-12).map((pt, idx) => {
            const heightPct = Math.min(100, Math.max(10, pt.attendance_percentage));
            const barColor =
              pt.attendance_percentage >= 85
                ? 'bg-emerald-500 hover:bg-emerald-600'
                : pt.attendance_percentage >= 75
                ? 'bg-indigo-500 hover:bg-indigo-600'
                : pt.attendance_percentage >= 60
                ? 'bg-amber-500 hover:bg-amber-600'
                : 'bg-rose-500 hover:bg-rose-600';

            return (
              <div key={idx} className="flex-1 flex flex-col items-center group relative">
                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 hidden group-hover:block z-10 bg-slate-900 text-white text-[11px] p-2 rounded-lg shadow-lg whitespace-nowrap">
                  <p className="font-bold">{pt.period}</p>
                  <p className="text-emerald-400">{pt.attendance_percentage}% Attended</p>
                  <p className="text-slate-300">P: {pt.present} | L: {pt.late} | A: {pt.absent}</p>
                </div>

                <span className="text-[10px] font-bold text-slate-600 mb-1 group-hover:text-indigo-600">
                  {pt.attendance_percentage}%
                </span>
                <div
                  className={`w-full max-w-[28px] rounded-t-md transition-all duration-300 ${barColor}`}
                  style={{ height: `${heightPct}%` }}
                />
              </div>
            );
          })}
        </div>

        {/* X Axis Labels */}
        <div className="flex justify-between text-[11px] text-slate-500 font-medium px-2">
          {points.slice(-12).map((pt, idx) => (
            <span key={idx} className="truncate max-w-[50px] text-center">
              {pt.period.replace(/^\d{4}-/, '')}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AttendanceTrendChart;
