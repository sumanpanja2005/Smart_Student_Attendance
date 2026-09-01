import React, { useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/Card';
import { Button } from '../components/Button';
import { CameraCapture } from '../components/CameraCapture';
import { ErrorMessage } from '../components/ErrorMessage';
import { recognizeFace } from '../services/faceService';
import { UserCheck, UserX, ShieldCheck, RefreshCw, Award, AlertTriangle } from 'lucide-react';

export const FaceRecognitionPage = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCaptureFrame = async (imageBlob) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await recognizeFace(imageBlob);
      setResult(res);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Face recognition query failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="AI Face Recognition Verification"
        subtitle="Real-time biometric student identification using InsightFace embeddings & cosine similarity"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Camera Feed */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Camera Recognition Frame</CardTitle>
            <CardDescription>Capture a clear camera frame to test student recognition</CardDescription>
          </CardHeader>
          <CardContent>
            <CameraCapture onCapture={handleCaptureFrame} isProcessing={loading} />
          </CardContent>
        </Card>

        {/* Right: Recognition Output */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recognition Result</CardTitle>
            <CardDescription>Biometric match evaluation output</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && <ErrorMessage title="Recognition Error" message={error} />}

            {!result && !error && !loading && (
              <div className="p-8 text-center text-gray-400 space-y-2 border-2 border-dashed rounded-xl">
                <UserCheck className="w-12 h-12 mx-auto text-gray-300" />
                <p className="text-xs">Capture a frame from the camera to test student face identification.</p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {result.recognized ? (
                  /* Recognized Student Card */
                  <div className="p-5 bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-300 rounded-2xl space-y-3 shadow-sm">
                    <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                      <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
                      <span>✓ Student Recognized Successfully</span>
                    </div>

                    <div className="space-y-1.5 pt-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-500 font-medium">Student ID:</span>
                        <span className="font-mono font-bold text-emerald-900">{result.student?.student_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 font-medium">Full Name:</span>
                        <span className="font-bold text-gray-900">
                          {result.student?.first_name} {result.student?.last_name}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 font-medium">Roll Number:</span>
                        <span className="font-semibold text-gray-800">{result.student?.roll_number}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 font-medium">Department:</span>
                        <span className="font-semibold text-gray-800">{result.student?.department}</span>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-emerald-200 flex items-center justify-between">
                      <span className="text-xs text-gray-600 font-medium">Cosine Similarity Match:</span>
                      <span className="font-mono font-bold text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full text-xs">
                        {(result.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  /* Unknown Face Card */
                  <div className="p-5 bg-rose-50/70 border-2 border-rose-200 rounded-2xl space-y-3">
                    <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
                      <UserX className="w-5 h-5 text-rose-600 shrink-0" />
                      <span>⚠ Unknown Face</span>
                    </div>
                    <p className="text-xs text-rose-700">{result.message}</p>
                    <div className="pt-2 border-t border-rose-200 flex items-center justify-between text-xs">
                      <span className="text-gray-600 font-medium">Highest Match Similarity:</span>
                      <span className="font-mono font-bold text-rose-800 bg-rose-100 px-2 py-0.5 rounded-md">
                        {(result.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FaceRecognitionPage;
