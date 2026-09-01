import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Filter, Clock, Eye, AlertCircle } from 'lucide-react';
import { attendanceService } from '../services/attendanceService';
import { getClasses } from '../services/classService';
import { getSubjects } from '../services/subjectService';

const AdminAttendancePage = () => {
  const navigate = useNavigate();

  const [sessions, setSessions] = useState([]);
  const [classesList, setClassesList] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [sessionDate, setSessionDate] = useState('');

  const fetchSessionsAndMetadata = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedClass) params.class_id = selectedClass;
      if (selectedSubject) params.subject_id = selectedSubject;
      if (selectedStatus) params.status = selectedStatus;
      if (sessionDate) params.session_date = sessionDate;

      const [sessData, clsData, subData] = await Promise.all([
        attendanceService.getSessions(params),
        getClasses(),
        getSubjects(),
      ]);
      setSessions(sessData);
      setClassesList(clsData);
      setSubjectsList(subData);
    } catch (err) {
      console.error('Failed to load admin attendance data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionsAndMetadata();
  }, [selectedClass, selectedSubject, selectedStatus, sessionDate]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Admin Attendance Overview</h1>
        <p className="text-slate-500 text-sm mt-1">
          Monitor all system-wide attendance sessions, inspect rosters, and review attendance records.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 text-slate-700 font-semibold text-sm">
          <Filter className="w-4 h-4 text-indigo-600" />
          Filter Sessions:
        </div>

        <select
          value={selectedClass}
          onChange={(e) => setSelectedClass(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Classes</option>
          {classesList.map((cls) => (
            <option key={cls.id || cls._id} value={cls.id || cls._id}>
              {cls.name || cls.class_name}
            </option>
          ))}
        </select>

        <select
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Subjects</option>
          {subjectsList.map((sub) => (
            <option key={sub.id || sub._id} value={sub.id || sub._id}>
              {sub.subject_code} - {sub.subject_name}
            </option>
          ))}
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">OPEN</option>
          <option value="CLOSED">CLOSED</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>

        <input
          type="date"
          value={sessionDate}
          onChange={(e) => setSessionDate(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Sessions Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600" />
            System Attendance Sessions
          </h2>
          <span className="text-xs font-medium bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
            {sessions.length} Sessions Found
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-sm">Loading attendance sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No attendance sessions match the selected filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
                <tr>
                  <th className="px-5 py-3">Date / Time</th>
                  <th className="px-5 py-3">Class</th>
                  <th className="px-5 py-3">Subject</th>
                  <th className="px-5 py-3">Teacher</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Attendance Breakdown</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sessions.map((sess) => (
                  <tr key={sess.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-slate-800">
                      {sess.session_date}
                      <span className="block text-xs text-slate-400 font-normal">{sess.start_time}</span>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-800">{sess.class_name}</td>
                    <td className="px-5 py-3.5">{sess.subject_name}</td>
                    <td className="px-5 py-3.5 text-xs text-slate-600">{sess.teacher_name}</td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                          sess.status === 'OPEN'
                            ? 'bg-emerald-100 text-emerald-800'
                            : sess.status === 'CLOSED'
                            ? 'bg-slate-100 text-slate-700'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {sess.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-emerald-600">{sess.present_count} P</span>
                        <span>•</span>
                        <span className="font-semibold text-amber-600">{sess.late_count} L</span>
                        <span>•</span>
                        <span className="font-semibold text-rose-600">{sess.absent_count} A</span>
                        <span>•</span>
                        <span className="text-slate-400">Total {sess.total_students}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => navigate(`/admin/attendance/${sess.id}`)}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ml-auto"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Roster
                      </button>
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

export default AdminAttendancePage;
