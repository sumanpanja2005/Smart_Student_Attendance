import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, BookOpen, Users, Plus, Play, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { getClasses } from '../services/classService';
import { getSubjects } from '../services/subjectService';
import { attendanceService } from '../services/attendanceService';

const TeacherAttendancePage = () => {
  const navigate = useNavigate();

  const [classesList, setClassesList] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [sessionDate, setSessionDate] = useState(new Date().toISOString().split('T')[0]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [clsData, subData, sessData] = await Promise.all([
        getClasses(),
        getSubjects(),
        attendanceService.getSessions(),
      ]);
      setClassesList(clsData);
      setSubjectsList(subData);
      setSessions(sessData);
    } catch (err) {
      console.error('Failed to load attendance teacher data:', err);
      setErrorMsg('Failed to load classes or subjects.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!selectedClass || !selectedSubject) {
      setErrorMsg('Please select both a class and a subject.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    try {
      const newSession = await attendanceService.createSession({
        class_id: selectedClass,
        subject_id: selectedSubject,
        session_date: sessionDate,
      });
      navigate(`/teacher/attendance/${newSession.id}`);
    } catch (err) {
      console.error('Create session error:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to create attendance session.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Attendance Session Manager</h1>
        <p className="text-slate-500 text-sm mt-1">
          Launch live AI face-recognition attendance sessions or manage manual class attendance.
        </p>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* New Session Launcher Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-indigo-600" />
          Create New Attendance Session
        </h2>

        <form onSubmit={handleCreateSession} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
              Class / Section
            </label>
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="">Select Class...</option>
              {classesList.map((cls) => (
                <option key={cls.id || cls._id} value={cls.id || cls._id}>
                  {cls.name || cls.class_name} ({cls.department})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
              Subject
            </label>
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="">Select Subject...</option>
              {subjectsList.map((sub) => (
                <option key={sub.id || sub._id} value={sub.id || sub._id}>
                  {sub.subject_code} - {sub.subject_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
              Session Date
            </label>
            <input
              type="date"
              value={sessionDate}
              onChange={(e) => setSessionDate(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-medium text-sm transition-colors flex items-center justify-center gap-2 shadow-xs"
            >
              <Play className="w-4 h-4 fill-white" />
              {isSubmitting ? 'Launching...' : 'Start Session'}
            </button>
          </div>
        </form>
      </div>

      {/* Sessions List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600" />
            Attendance Sessions History
          </h2>
          <span className="text-xs font-medium bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
            {sessions.length} Total Sessions
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-sm">Loading attendance sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No attendance sessions created yet. Select a class and subject above to start one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
                <tr>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3">Class</th>
                  <th className="px-5 py-3">Subject</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Attendance Stats</th>
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
                    <td className="px-5 py-3.5 text-xs text-slate-600">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-emerald-600">{sess.present_count} Present</span>
                        <span>•</span>
                        <span className="text-slate-500">{sess.absent_count} Absent</span>
                        <span>•</span>
                        <span className="text-slate-400">Total: {sess.total_students}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => navigate(`/teacher/attendance/${sess.id}`)}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 rounded-lg text-xs font-medium transition-colors"
                      >
                        {sess.status === 'OPEN' ? 'Enter Session' : 'View Records'}
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

export default TeacherAttendancePage;
