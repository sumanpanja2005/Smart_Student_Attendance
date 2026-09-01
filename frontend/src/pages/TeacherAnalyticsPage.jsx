import React, { useState, useEffect } from 'react';
import { BarChart3, Filter, AlertTriangle, Users, BookOpen, ShieldAlert, RefreshCw } from 'lucide-react';
import analyticsService from '../services/analyticsService';
import { getClasses } from '../services/classService';
import AttendanceRiskBadge from '../components/AttendanceRiskBadge';

const TeacherAnalyticsPage = () => {
  const [classesList, setClassesList] = useState([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [classData, setClassData] = useState(null);
  const [riskStudents, setRiskStudents] = useState([]);
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  const loadInitialData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const cls = await getClasses();
      setClassesList(cls);
      if (cls.length > 0) {
        const firstId = cls[0].id || cls[0]._id;
        setSelectedClass(firstId);
        await loadClassAnalytics(firstId);
      }
      await loadRiskStudents(selectedRiskFilter);
    } catch (err) {
      console.error('Failed to load teacher analytics:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to load class analytics.');
    } finally {
      setLoading(false);
    }
  };

  const loadClassAnalytics = async (classId) => {
    if (!classId) return;
    try {
      const data = await analyticsService.getClassAnalytics(classId);
      setClassData(data);
    } catch (err) {
      console.error('Error loading class data:', err);
    }
  };

  const loadRiskStudents = async (riskLvl) => {
    try {
      const list = await analyticsService.getRiskStudents(riskLvl);
      setRiskStudents(list);
    } catch (err) {
      console.error('Error loading risk students:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleClassChange = (e) => {
    const cId = e.target.value;
    setSelectedClass(cId);
    loadClassAnalytics(cId);
  };

  const handleRiskFilterChange = (e) => {
    const lvl = e.target.value;
    setSelectedRiskFilter(lvl);
    loadRiskStudents(lvl);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-indigo-600" />
          Faculty Class Analytics & Risk Dashboard
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Monitor class attendance performance, subject averages, and identify at-risk students.
        </p>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Class Selector & Overview Cards */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-indigo-600" />
            <span className="text-sm font-bold text-slate-700">Select Assigned Class:</span>
            <select
              value={selectedClass}
              onChange={handleClassChange}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {classesList.map((cls) => (
                <option key={cls.id || cls._id} value={cls.id || cls._id}>
                  {cls.name || cls.class_name} ({cls.department})
                </option>
              ))}
            </select>
          </div>

          {classData && (
            <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full border border-indigo-100">
              Department: {classData.department}
            </span>
          )}
        </div>

        {classData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-1">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <span className="text-xs font-semibold text-slate-400 uppercase">Enrolled Students</span>
              <span className="block text-2xl font-black text-slate-800 mt-1">{classData.total_students}</span>
            </div>
            <div className="bg-indigo-50/60 p-4 rounded-xl border border-indigo-100/60">
              <span className="text-xs font-semibold text-indigo-600 uppercase">Class Average</span>
              <span className="block text-2xl font-black text-indigo-700 mt-1">{classData.average_attendance_percentage}%</span>
            </div>
            <div className="bg-amber-50/60 p-4 rounded-xl border border-amber-100/60">
              <span className="text-xs font-semibold text-amber-600 uppercase">Below 75% Threshold</span>
              <span className="block text-2xl font-black text-amber-700 mt-1">{classData.students_below_threshold}</span>
            </div>
            <div className="bg-rose-50/60 p-4 rounded-xl border border-rose-100/60">
              <span className="text-xs font-semibold text-rose-600 uppercase">High / Critical Risk</span>
              <span className="block text-2xl font-black text-rose-700 mt-1">
                {(classData.risk_distribution?.HIGH || 0) + (classData.risk_distribution?.CRITICAL || 0)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Subject Averages for Selected Class */}
      {classData?.subject_averages && classData.subject_averages.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-600" />
            Subject Attendance Averages ({classData.class_name})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {classData.subject_averages.map((sub, idx) => (
              <div key={idx} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-800">{sub.subject_name}</p>
                  <p className="text-[10px] text-slate-400 font-semibold">{sub.subject_code} • {sub.total_sessions} Sessions</p>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-black ${
                    sub.average_attendance_percentage >= 75
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {sub.average_attendance_percentage}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* At-Risk Students List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs space-y-4 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            At-Risk Students Watchlist
          </h3>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Filter Risk Level:</span>
            <select
              value={selectedRiskFilter}
              onChange={handleRiskFilterChange}
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

        {riskStudents.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No students found for the selected risk filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
                <tr>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">Roll Number</th>
                  <th className="px-4 py-3">Class</th>
                  <th className="px-4 py-3">Attendance %</th>
                  <th className="px-4 py-3">Risk Level</th>
                  <th className="px-4 py-3">Primary Risk Factor</th>
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
        )}
      </div>
    </div>
  );
};

export default TeacherAnalyticsPage;
