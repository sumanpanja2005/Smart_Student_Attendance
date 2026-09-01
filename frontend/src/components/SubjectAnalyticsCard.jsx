import React from 'react';
import { BookOpen, CheckCircle2, Clock, XCircle } from 'lucide-react';

const SubjectAnalyticsCard = ({ subject }) => {
  const pct = subject?.attendance_percentage ?? 0.0;
  const isGood = pct >= 75.0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3 hover:border-slate-300 transition-all">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 border border-indigo-100 rounded-lg text-indigo-600">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">{subject?.subject_name}</h4>
            <span className="text-xs font-semibold text-slate-400 uppercase">{subject?.subject_code}</span>
          </div>
        </div>

        <span
          className={`px-2.5 py-1 rounded-full text-xs font-extrabold ${
            isGood ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
          }`}
        >
          {pct}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${isGood ? 'bg-emerald-500' : 'bg-rose-500'}`}
            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          />
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-2 pt-1 text-center text-xs">
        <div className="bg-slate-50 p-1.5 rounded-lg border border-slate-100">
          <span className="block text-[10px] text-slate-400 font-semibold uppercase">Sessions</span>
          <span className="font-bold text-slate-700">{subject?.total_sessions ?? 0}</span>
        </div>
        <div className="bg-emerald-50/60 p-1.5 rounded-lg border border-emerald-100/60">
          <span className="block text-[10px] text-emerald-600 font-semibold uppercase">Present</span>
          <span className="font-bold text-emerald-700">{subject?.present ?? 0}</span>
        </div>
        <div className="bg-amber-50/60 p-1.5 rounded-lg border border-amber-100/60">
          <span className="block text-[10px] text-amber-600 font-semibold uppercase">Late</span>
          <span className="font-bold text-amber-700">{subject?.late ?? 0}</span>
        </div>
        <div className="bg-rose-50/60 p-1.5 rounded-lg border border-rose-100/60">
          <span className="block text-[10px] text-rose-600 font-semibold uppercase">Absent</span>
          <span className="font-bold text-rose-700">{subject?.absent ?? 0}</span>
        </div>
      </div>
    </div>
  );
};

export default SubjectAnalyticsCard;
