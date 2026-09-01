import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Lock,
  Ban,
  UserCheck,
  Save,
  RefreshCw,
} from 'lucide-react';
import { attendanceService } from '../services/attendanceService';
import AttendanceCamera from '../components/AttendanceCamera';

const AttendanceSessionPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Face attendance state
  const [isProcessingFace, setIsProcessingFace] = useState(false);
  const [lastFaceResult, setLastFaceResult] = useState(null);

  // Manual status edits buffer
  const [manualStatusBuffer, setManualStatusBuffer] = useState({});
  const [isSavingBulk, setIsSavingBulk] = useState(false);

  const fetchSessionAndRecords = async () => {
    try {
      const [sessData, recsData] = await Promise.all([
        attendanceService.getSession(sessionId),
        attendanceService.getSessionRecords(sessionId),
      ]);
      setSession(sessData);
      setRecords(recsData);
    } catch (err) {
      console.error('Fetch session error:', err);
      setErrorMsg('Failed to load session details or attendance records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionAndRecords();
  }, [sessionId]);

  // Handle camera capture frame
  const handleFaceCaptureFrame = async (imageBlob) => {
    if (!session || session.status !== 'OPEN') return;

    setIsProcessingFace(true);
    setLastFaceResult(null);
    try {
      const result = await attendanceService.markFaceAttendance(sessionId, imageBlob);
      setLastFaceResult(result);
      if (result.success && result.attendance_marked) {
        // Refresh records on new attendance
        fetchSessionAndRecords();
      }
    } catch (err) {
      console.error('Face attendance error:', err);
      setLastFaceResult({
        success: false,
        attendance_marked: false,
        message: err.response?.data?.detail || 'Face recognition attendance error.',
      });
    } finally {
      setIsProcessingFace(false);
    }
  };

  // Single manual marking toggle
  const handleSingleManualMark = async (studentId, statusVal) => {
    try {
      await attendanceService.markManualAttendance(sessionId, {
        student_id: studentId,
        status: statusVal,
      });
      fetchSessionAndRecords();
    } catch (err) {
      console.error('Manual mark error:', err);
      alert(err.response?.data?.detail || 'Failed to mark manual attendance.');
    }
  };

  // Single record correction
  const handleCorrection = async (recordId, newStatus) => {
    try {
      await attendanceService.updateAttendanceRecord(recordId, { status: newStatus });
      fetchSessionAndRecords();
    } catch (err) {
      console.error('Record correction error:', err);
      alert(err.response?.data?.detail || 'Failed to correct attendance record.');
    }
  };

  // Close session
  const handleCloseSession = async () => {
    if (!window.confirm('Are you sure you want to CLOSE this attendance session? Normal attendance marking will stop.')) {
      return;
    }
    try {
      await attendanceService.closeSession(sessionId);
      fetchSessionAndRecords();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to close session.');
    }
  };

  // Cancel session
  const handleCancelSession = async () => {
    if (!window.confirm('Are you sure you want to CANCEL this session? Cancelled sessions are excluded from attendance statistics.')) {
      return;
    }
    try {
      await attendanceService.cancelSession(sessionId);
      fetchSessionAndRecords();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel session.');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 text-sm">Loading attendance session workspace...</div>;
  }

  if (!session) {
    return (
      <div className="p-8 text-center text-slate-500 text-sm">
        Session not found. <button onClick={() => navigate('/teacher/attendance')} className="text-indigo-600 underline">Return to Attendance Manager</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/teacher/attendance')}
          className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium transition-colors flex items-center gap-1.5"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Sessions
        </button>

        <div className="flex items-center gap-3">
          {session.status === 'OPEN' && (
            <>
              <button
                onClick={handleCloseSession}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
              >
                <Lock className="w-3.5 h-3.5" />
                Close Session
              </button>
              <button
                onClick={handleCancelSession}
                className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <Ban className="w-3.5 h-3.5" />
                Cancel Session
              </button>
            </>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-500 flex-shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Session Information Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">{session.class_name}</h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${
                session.status === 'OPEN'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : session.status === 'CLOSED'
                  ? 'bg-slate-100 text-slate-700'
                  : 'bg-rose-100 text-rose-800'
              }`}
            >
              STATUS: {session.status}
            </span>
          </div>
          <p className="text-slate-600 font-medium text-sm mt-1">
            Subject: {session.subject_name} • Date: {session.session_date} ({session.start_time})
          </p>
        </div>

        {/* Stats Badges */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-50 border border-slate-200 px-4 py-2 rounded-xl text-center">
            <span className="block text-xs font-medium text-slate-500">Enrolled</span>
            <span className="text-lg font-bold text-slate-800">{session.total_students}</span>
          </div>
          <div className="bg-emerald-50 border border-emerald-200 px-4 py-2 rounded-xl text-center">
            <span className="block text-xs font-medium text-emerald-600">Present</span>
            <span className="text-lg font-bold text-emerald-700">{session.present_count}</span>
          </div>
          <div className="bg-amber-50 border border-amber-200 px-4 py-2 rounded-xl text-center">
            <span className="block text-xs font-medium text-amber-600">Late</span>
            <span className="text-lg font-bold text-amber-700">{session.late_count}</span>
          </div>
          <div className="bg-rose-50 border border-rose-200 px-4 py-2 rounded-xl text-center">
            <span className="block text-xs font-medium text-rose-600">Absent</span>
            <span className="text-lg font-bold text-rose-700">{session.absent_count}</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Face Recognition Camera Feed (Only when OPEN) */}
        {session.status === 'OPEN' && (
          <div className="lg:col-span-1">
            <AttendanceCamera
              onCaptureFrame={handleFaceCaptureFrame}
              isProcessing={isProcessingFace}
              lastResult={lastFaceResult}
            />
          </div>
        )}

        {/* Right Column: Attendance Records & Class Roster Table */}
        <div className={session.status === 'OPEN' ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-indigo-600" />
                Class Attendance Roster ({records.length} Students)
              </h2>
              <button
                onClick={fetchSessionAndRecords}
                className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors"
                title="Refresh Attendance Roster"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-semibold">
                  <tr>
                    <th className="px-4 py-3">Roll No</th>
                    <th className="px-4 py-3">Student Name</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Method</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.map((rec) => {
                    const isDerived = rec.marking_method === 'DERIVED';
                    const isRecordCreated = !rec.id.startsWith('unmarked_');

                    return (
                      <tr key={rec.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3 font-semibold text-slate-800">{rec.roll_number || 'N/A'}</td>
                        <td className="px-4 py-3 font-medium text-slate-800">{rec.student_name}</td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                              rec.status === 'PRESENT'
                                ? 'bg-emerald-100 text-emerald-800'
                                : rec.status === 'LATE'
                                ? 'bg-amber-100 text-amber-800'
                                : rec.status === 'EXCUSED'
                                ? 'bg-indigo-100 text-indigo-800'
                                : rec.status === 'ABSENT'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-slate-100 text-slate-500'
                            }`}
                          >
                            {rec.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {rec.marking_method === 'FACE' ? (
                            <span className="text-indigo-600 font-semibold flex items-center gap-1">
                              FACE ({(rec.similarity * 100).toFixed(0)}%)
                            </span>
                          ) : rec.marking_method === 'MANUAL' ? (
                            <span className="text-slate-600 font-medium">MANUAL</span>
                          ) : (
                            <span className="text-slate-400 italic">NOT MARKED</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right space-x-1">
                          {session.status === 'OPEN' && !isRecordCreated ? (
                            <>
                              <button
                                onClick={() => handleSingleManualMark(rec.student_id, 'PRESENT')}
                                className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-xs font-medium transition-colors"
                              >
                                Present
                              </button>
                              <button
                                onClick={() => handleSingleManualMark(rec.student_id, 'LATE')}
                                className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 rounded-lg text-xs font-medium transition-colors"
                              >
                                Late
                              </button>
                              <button
                                onClick={() => handleSingleManualMark(rec.student_id, 'ABSENT')}
                                className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-medium transition-colors"
                              >
                                Absent
                              </button>
                            </>
                          ) : isRecordCreated ? (
                            <div className="inline-flex items-center gap-1">
                              <select
                                value={rec.status}
                                onChange={(e) => handleCorrection(rec.id, e.target.value)}
                                className="px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                              >
                                <option value="PRESENT">PRESENT</option>
                                <option value="LATE">LATE</option>
                                <option value="ABSENT">ABSENT</option>
                                <option value="EXCUSED">EXCUSED</option>
                              </select>
                            </div>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttendanceSessionPage;
