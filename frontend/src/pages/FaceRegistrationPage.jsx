import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/Card';
import { Button } from '../components/Button';
import { CameraCapture } from '../components/CameraCapture';
import { Loader } from '../components/Loader';
import { ErrorMessage } from '../components/ErrorMessage';
import { getStudents, getMyStudentProfile } from '../services/studentService';
import { registerFace, getFaceStatus, deleteFace } from '../services/faceService';
import { useAuth } from '../context/AuthContext';
import { UserCheck, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw, Trash2, ArrowLeft } from 'lucide-react';

export const FaceRegistrationPage = () => {
  const { studentId: paramStudentId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [targetStudentId, setTargetStudentId] = useState(paramStudentId || '');
  
  const [faceStatus, setFaceStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Required sample count target
  const TARGET_SAMPLES = 3;

  // Load student list (for Admin) or own profile (for Student)
  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      if (user?.role === 'ADMIN') {
        const list = await getStudents();
        setStudents(list);

        let activeId = paramStudentId;
        if (!activeId && list.length > 0) {
          activeId = list[0].id;
        }
        setTargetStudentId(activeId);

        const found = list.find((s) => s.id === activeId);
        setSelectedStudent(found || null);
      } else if (user?.role === 'STUDENT') {
        const selfProfile = await getMyStudentProfile();
        setSelectedStudent(selfProfile);
        setTargetStudentId(selfProfile.id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load student profiles.');
    } finally {
      setLoading(false);
    }
  }, [user, paramStudentId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Fetch face registration status for target student
  const fetchStatus = useCallback(async () => {
    if (!targetStudentId) return;
    try {
      const status = await getFaceStatus(targetStudentId);
      setFaceStatus(status);
    } catch (err) {
      console.error('Failed to load face status:', err);
    }
  }, [targetStudentId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleStudentSelect = (e) => {
    const id = e.target.value;
    setTargetStudentId(id);
    const found = students.find((s) => s.id === id);
    setSelectedStudent(found || null);
    setSuccessMessage('');
    setError('');
  };

  const handleCaptureFrame = async (imageBlob) => {
    if (!targetStudentId) {
      setError('Please select a student profile before registering a face.');
      return;
    }

    setSubmitting(true);
    setError('');
    setSuccessMessage('');

    try {
      const res = await registerFace(targetStudentId, imageBlob);
      setSuccessMessage(`Sample ${res.samples_registered} registered successfully!`);
      await fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Face registration failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivateFace = async () => {
    if (!window.confirm('Are you sure you want to deactivate this student face profile?')) return;
    try {
      await deleteFace(targetStudentId);
      setSuccessMessage('Student face profile deactivated.');
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to deactivate face profile.');
    }
  };

  const sampleCount = faceStatus?.sample_count || 0;
  const isRegistered = sampleCount >= TARGET_SAMPLES;

  if (loading) {
    return <Loader message="Loading face registration portal..." />;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Biometric Face Registration"
        subtitle="Capture multiple high-quality face samples to register student AI biometric embeddings"
        actions={
          <Button variant="outline" size="sm" icon={ArrowLeft} onClick={() => navigate(-1)}>
            Back
          </Button>
        }
      />

      {/* Student Selection Card (Admin Only) */}
      {user?.role === 'ADMIN' && (
        <Card className="p-4">
          <label className="block text-xs font-bold text-gray-700 mb-2">Select Student Profile *</label>
          <select
            value={targetStudentId}
            onChange={handleStudentSelect}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            <option value="">-- Select Student --</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>
                {s.student_id} - {s.user?.first_name} {s.user?.last_name} (Roll: {s.roll_number})
              </option>
            ))}
          </select>
        </Card>
      )}

      {/* Target Student Info Card */}
      {selectedStudent && (
        <Card className="bg-slate-50 border-slate-200">
          <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div>
              <span className="text-gray-500 block font-medium">Student Name:</span>
              <span className="text-sm font-bold text-gray-900">
                {selectedStudent.user?.first_name} {selectedStudent.user?.last_name}
              </span>
            </div>
            <div>
              <span className="text-gray-500 block font-medium">Student ID:</span>
              <span className="font-mono font-semibold text-indigo-700">{selectedStudent.student_id}</span>
            </div>
            <div>
              <span className="text-gray-500 block font-medium">Roll Number:</span>
              <span className="font-semibold text-gray-800">{selectedStudent.roll_number}</span>
            </div>
            <div>
              <span className="text-gray-500 block font-medium">Biometric Status:</span>
              <span
                className={`inline-flex items-center gap-1 font-bold px-2.5 py-0.5 rounded-full text-[11px] ${
                  isRegistered
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-amber-100 text-amber-800 border border-amber-300'
                }`}
              >
                {isRegistered ? '✓ Face Registered' : `⚠ Pending (${sampleCount}/${TARGET_SAMPLES} Samples)`}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Registration Area */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Camera Feed */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Camera Frame Capture</CardTitle>
            <CardDescription>Position your face centered with adequate lighting</CardDescription>
          </CardHeader>
          <CardContent>
            <CameraCapture onCapture={handleCaptureFrame} isProcessing={submitting} />
          </CardContent>
        </Card>

        {/* Right: Registration Progress & Guidelines */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sample Quality & Guidance</CardTitle>
            <CardDescription>Collect {TARGET_SAMPLES} samples from slightly different angles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && <ErrorMessage title="Registration Feedback" message={error} />}
            {successMessage && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{successMessage}</span>
              </div>
            )}

            {/* Progress Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-gray-700">
                <span>Registration Progress</span>
                <span>{sampleCount} / {TARGET_SAMPLES} Samples</span>
              </div>
              <div className="w-full h-2.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all duration-300"
                  style={{ width: `${Math.min(100, (sampleCount / TARGET_SAMPLES) * 100)}%` }}
                />
              </div>
            </div>

            {/* Instructions */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs text-gray-600">
              <h4 className="font-bold text-gray-900 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-indigo-600" /> Guidelines for High Match Accuracy:
              </h4>
              <ul className="list-disc list-inside space-y-1 leading-relaxed">
                <li>Sample 1: Look directly straight at the camera.</li>
                <li>Sample 2: Turn your head slightly to the left.</li>
                <li>Sample 3: Turn your head slightly to the right.</li>
                <li>Ensure only ONE face is present in the video frame.</li>
                <li>Avoid extreme darkness, bright backlighting, or severe blur.</li>
              </ul>
            </div>

            {/* Deactivation for Admin */}
            {user?.role === 'ADMIN' && sampleCount > 0 && (
              <div className="pt-4 border-t flex justify-end">
                <Button variant="ghost" size="sm" className="text-rose-600 hover:bg-rose-50" icon={Trash2} onClick={handleDeactivateFace}>
                  Deactivate Face Profile
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FaceRegistrationPage;
