import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Clock, XCircle, AlertCircle, BookOpen, Award } from 'lucide-react';
import { attendanceService } from '../services/attendanceService';

const MyAttendancePage = () => {
  const [summary, setSummary] = useState(null);
  const [subjectSummaries, setSubjectSummaries] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchStudentData = async () => {
    setLoading(true);
    try {
      const [sumData, subData, histData] = await Promise.all([
        attendanceService.getMyAttendanceSummary(),
        attendanceService.getMySubjectSummaries(),
        attendanceService.getMyAttendanceHistory(),
      ]);
      setSummary(sumData);
      setSubjectSummaries(subData);
      setHistory(histData);
    } catch (err) {
      console.error('Failed to load student attendance:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudentData();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 text-sm">Loading attendance record summary...</div>;
  }

  const pct = summary ? summary.attendance_percentage : 0.0;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">My Attendance Portal</h1>
        <p className="text-slate-500 text-sm mt-1">
          Review your overall attendance percentage, subject-wise progress, and detailed attendance log.
        </p>
      </div>

      {/* Main Overall Percentage Card & Status Counts */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* Main Metric Percentage Badge */}
        <div className="md:col-span-2 bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
              Overall Academic Attendance
            </span>
            <div className="text-4xl font-extrabold mt-2 flex items-baseline gap-2">
              <span>{pct.toFixed(1)}%</span>
              <span className="text-xs font-normal text-slate-300">
                ({summary ? summary.present + summary.late : 0}/{summary ? summary.eligible_sessions : 0} eligible sessions)
              </span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-indigo-800/60 flex items-center justify-between text-xs">
            <span className="text-slate-300">Attendance Threshold Status:</span>
            <span
              className={`px-2.5 py-0.5 rounded-full font-bold uppercase ${
                pct >= 75
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : pct >= 65
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              }`}
            >
              {pct >= 75 ? 'Good Standing' : pct >= 65 ? 'Warning (<75%)' : 'Critical Shortage'}
            </span>
          </div>
        </div>

        {/* Status Count Cards */}
        <div className="md:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between text-emerald-600">
              <span className="text-xs font-semibold">Present</span>
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <span className="text-2xl font-bold text-slate-800 mt-2">{summary ? summary.present : 0}</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between text-amber-600">
              <span className="text-xs font-semibold">Late</span>
              <Clock className="w-4 h-4" />
            </div>
            <span className="text-2xl font-bold text-slate-800 mt-2">{summary ? summary.late : 0}</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between text-rose-600">
              <span className="text-xs font-semibold">Absent</span>
              <XCircle className="w-4 h-4" />
            </div>
            <span className="text-2xl font-bold text-slate-800 mt-2">{summary ? summary.absent : 0}</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between text-indigo-600">
              <span className="text-xs font-semibold">Excused</span>
              <Award className="w-4 h-4" />
            </div>
            <span className="text-2xl font-bold text-slate-800 mt-2">{summary ? summary.excused : 0}</span>
          </div>
        </div>
      </div>

      {/* Subject-Wise Attendance Progress Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-600" />
          Subject-Wise Attendance Breakdown
        </h2>

        {subjectSummaries.length === 0 ? (
          <p className="text-slate-500 text-sm">No closed class sessions found for your subjects yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {subjectSummaries.map((sub) => (
              <div key={sub.subject_id} className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-xs font-bold text-indigo-600">{sub.subject_code}</span>
                    <h3 className="font-semibold text-slate-800 text-sm">{sub.subject_name}</h3>
                  </div>
                  <span
                    className={`text-base font-extrabold ${
                      sub.attendance_percentage >= 75
                        ? 'text-emerald-600'
                        : sub.attendance_percentage >= 65
                        ? 'text-amber-600'
                        : 'text-rose-600'
                    }`}
                  >
                    {sub.attendance_percentage.toFixed(1)}%
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden mb-2">
                  <div
                    className={`h-full transition-all duration-300 ${
                      sub.attendance_percentage >= 75
                        ? 'bg-emerald-500'
                        : sub.attendance_percentage >= 65
                        ? 'bg-amber-500'
                        : 'bg-rose-500'
                    }`}
                    style={{ width: `${Math.min(100, sub.attendance_percentage)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>
                    Present: {sub.present} | Late: {sub.late} | Absent: {sub.absent}
                  </span>
                  <span>{sub.total_sessions} Sessions Total</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Attendance History Log */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-indigo-600" />
            Attendance Activity History Log
          </h2>
        </div>

        {history.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No attendance records found yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
                <tr>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Method</th>
                  <th className="px-5 py-3">Marked Time</th>
                  <th className="px-5 py-3">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-slate-800">{rec.attendance_date}</td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                          rec.status === 'PRESENT'
                            ? 'bg-emerald-100 text-emerald-800'
                            : rec.status === 'LATE'
                            ? 'bg-amber-100 text-amber-800'
                            : rec.status === 'EXCUSED'
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {rec.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-xs">
                      {rec.marking_method === 'FACE' ? (
                        <span className="text-indigo-600 font-semibold">
                          FACE ({(rec.similarity * 100).toFixed(0)}%)
                        </span>
                      ) : (
                        <span className="text-slate-600 font-medium">MANUAL</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">
                      {new Date(rec.marked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">{rec.remarks || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyAttendancePage;
