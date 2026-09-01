import React from 'react';
import { Percent, CheckCircle2, XCircle, Clock, CalendarCheck, ShieldAlert } from 'lucide-react';

const AnalyticsSummaryCards = ({
  attendancePercentage = 0.0,
  present = 0,
  absent = 0,
  late = 0,
  eligibleSessions = 0,
  riskLevel = 'LOW',
}) => {
  const cards = [
    {
      title: 'Attendance Percentage',
      value: `${attendancePercentage}%`,
      sub: 'Authoritative Step 4 Formula',
      icon: Percent,
      color: attendancePercentage >= 75 ? 'text-emerald-600 bg-emerald-50 border-emerald-100' : 'text-rose-600 bg-rose-50 border-rose-100',
    },
    {
      title: 'Present Sessions',
      value: present,
      sub: 'Full Attended',
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    },
    {
      title: 'Late Arrivals',
      value: late,
      sub: 'Counts as Attended',
      icon: Clock,
      color: 'text-amber-600 bg-amber-50 border-amber-100',
    },
    {
      title: 'Absences Recorded',
      value: absent,
      sub: 'Counts in Denominator',
      icon: XCircle,
      color: 'text-rose-600 bg-rose-50 border-rose-100',
    },
    {
      title: 'Eligible Sessions',
      value: eligibleSessions,
      sub: 'Excludes Excused/Cancelled',
      icon: CalendarCheck,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
    },
    {
      title: 'Risk Level',
      value: riskLevel,
      sub: 'Deterministic Risk Score',
      icon: ShieldAlert,
      color:
        riskLevel === 'CRITICAL' || riskLevel === 'HIGH'
          ? 'text-rose-600 bg-rose-50 border-rose-100'
          : riskLevel === 'MEDIUM'
          ? 'text-amber-600 bg-amber-50 border-amber-100'
          : 'text-emerald-600 bg-emerald-50 border-emerald-100',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{c.title}</span>
              <div className={`p-1.5 rounded-lg border ${c.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div>
              <span className="text-xl font-black text-slate-800 tracking-tight">{c.value}</span>
              <span className="block text-[10px] text-slate-400 font-medium truncate mt-0.5">{c.sub}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AnalyticsSummaryCards;
