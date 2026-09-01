import React, { useState, useEffect } from 'react';
import { BarChart3, Users, ShieldAlert, Layers, AlertCircle, RefreshCw } from 'lucide-react';
import analyticsService from '../services/analyticsService';
import { getClasses } from '../services/classService';

const AdminAnalyticsPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [riskStudents, setRiskStudents] = useState([]);
  const [classSummaries, setClassSummaries] = useState([]);
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  const loadData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const [dash, riskList, classesList] = await Promise.all([
        analyticsService.getAnalyticsDashboard(),
        analyticsService.getRiskStudents(selectedRiskFilter),
        getClasses(),
      ]);

      setDashboardData(dash);
      setRiskStudents(riskList);

      // Load class analytics summaries
      const cSummaries = await Promise.all(
        classesList.map(async (cls) => {
          try {
            return await analyticsService.getClassAnalytics(cls.id || cls._id);
          } catch {
            return null;
          }
        })
      );
      setClassSummaries(cSummaries.filter(Boolean));
    } catch (err) {
      console.error('Failed to load admin analytics:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to load system analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedRiskFilter]);

  if (loading && !dashboardData) {
    return (
      <div className="p-12 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
        <RefreshCw className="w-5 h-5 animate-spin text-indigo-600" />
        Loading system-wide attendance analytics...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-600" />
            System-Wide Attendance Analytics Overview
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Global attendance performance, class comparisons, and predictive risk distribution.
          </p>
        </div>

        <button
          onClick={loadData}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors flex items-center gap-2 self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Global Stats
        </button>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Top Metrics Row */}
      {dashboardData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">Total Students</span>
              <span className="block text-3xl font-black text-slate-800 mt-1">{dashboardData.total_students}</span>
            </div>
            <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-600">
              <Users className="w-6 h-6" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">System Average</span>
              <span className="block text-3xl font-black text-emerald-600 mt-1">{dashboardData.overall_average_percentage}%</span>
            </div>
            <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-emerald-600">
              <BarChart3 className="w-6 h-6" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">High / Critical Risk</span>
              <span className="block text-3xl font-black text-rose-600 mt-1">
                {(dashboardData.risk_counts?.HIGH || 0) + (dashboardData.risk_counts?.CRITICAL || 0)}
              </span>
            </div>
            <div className="p-3 bg-rose-50 border border-rose-100 rounded-xl text-rose-600">
              <ShieldAlert className="w-6 h-6" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">Total Sessions</span>
              <span className="block text-3xl font-black text-indigo-600 mt-1">{dashboardData.recent_sessions_count}</span>
            </div>
            <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-600">
              <Layers className="w-6 h-6" />
            </div>
          </div>
        </div>
      )}

      {/* Class Attendance Comparison Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            Class Attendance Comparison
          </h2>
          <span className="text-xs font-semibold bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
            {classSummaries.length} Active Classes
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
              <tr>
                <th className="px-5 py-3">Class Name</th>
                <th className="px-5 py-3">Department</th>
                <th className="px-5 py-3">Total Students</th>
                <th className="px-5 py-3">Average Attendance %</th>
                <th className="px-5 py-3">Below 75% Threshold</th>
                <th className="px-5 py-3">Risk Distribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {classSummaries.map((cls) => (
                <tr key={cls.class_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3.5 font-bold text-slate-800">{cls.class_name}</td>
                  <td className="px-5 py-3.5 text-xs text-slate-600">{cls.department}</td>
                  <td className="px-5 py-3.5 text-xs font-semibold text-slate-700">{cls.total_students}</td>
                  <td className="px-5 py-3.5 font-extrabold text-indigo-600">{cls.average_attendance_percentage}%</td>
                  <td className="px-5 py-3.5 text-xs font-semibold text-amber-600">{cls.students_below_threshold} Students</td>
                  <td className="px-5 py-3.5 text-xs">
                    <div className="flex items-center gap-2 font-semibold">
                      <span className="text-emerald-600">{cls.risk_distribution?.LOW || 0} Low</span>
                      <span>•</span>
                      <span className="text-amber-600">{cls.risk_distribution?.MEDIUM || 0} Med</span>
                      <span>•</span>
                      <span className="text-rose-600">
                        {(cls.risk_distribution?.HIGH || 0) + (cls.risk_distribution?.CRITICAL || 0)} High/Crit
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Global At-Risk Student Watchlist */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            Global At-Risk Students Watchlist
          </h2>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Filter Risk Level:</span>
            <select
              value={selectedRiskFilter}
              onChange={(e) => setSelectedRiskFilter(e.target.value)}
              className="px-3 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-slate-700"
            >
              <option value="">All Levels</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
              <tr>
                <th className="px-4 py-3">Student Name</th>
                <th className="px-4 py-3">Roll Number</th>
                <th className="px-4 py-3">Class</th>
                <th className="px-4 py-3">Attendance %</th>
                <th className="px-4 py-3">Risk Level</th>
                <th className="px-4 py-3">Contributing Factors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {riskStudents.map((st) => (
                <tr key={st.student_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3 font-semibold text-slate-800">{st.student_name}</td>
                  <td className="px-4 py-3 text-xs">{st.roll_number}</td>
                  <td className="px-4 py-3 text-xs">{st.class_name}</td>
                  <td className="px-4 py-3 font-bold text-slate-800">{st.attendance_percentage}%</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-black ${
                        st.risk_level === 'CRITICAL'
                          ? 'bg-rose-100 text-rose-800'
                          : st.risk_level === 'HIGH'
                          ? 'bg-orange-100 text-orange-800'
                          : st.risk_level === 'MEDIUM'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {st.risk_level} ({st.risk_score})
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">
                    {st.risk_factors?.[0] || 'No specific factor'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminAnalyticsPage;
