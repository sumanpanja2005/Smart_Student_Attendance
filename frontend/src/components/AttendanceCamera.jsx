import React, { useRef, useState, useEffect } from 'react';
import { Camera, RefreshCw, AlertCircle, CheckCircle, UserCheck } from 'lucide-react';

const AttendanceCamera = ({ onCaptureFrame, isProcessing = false, lastResult = null }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [autoScan, setAutoScan] = useState(false);

  // Initialize webcam
  const startCamera = async () => {
    setErrorMsg('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsStreaming(true);
    } catch (err) {
      console.error('Webcam access error:', err);
      setErrorMsg('Unable to access camera. Please allow camera permissions.');
      setIsStreaming(false);
    }
  };

  // Stop webcam and release tracks
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
  };

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  // Auto scan interval
  useEffect(() => {
    let intervalId = null;
    if (autoScan && isStreaming && !isProcessing) {
      intervalId = setInterval(() => {
        captureAndSend();
      }, 2500);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [autoScan, isStreaming, isProcessing]);

  const captureAndSend = () => {
    if (!videoRef.current || !canvasRef.current || !isStreaming || isProcessing) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob && onCaptureFrame) {
          onCaptureFrame(blob);
        }
      },
      'image/jpeg',
      0.9
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Camera className="w-5 h-5 text-indigo-600" />
          Face Attendance Recognition Camera
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoScan(!autoScan)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              autoScan
                ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {autoScan ? 'Auto-Scan Active' : 'Enable Auto-Scan'}
          </button>
          <button
            onClick={isStreaming ? stopCamera : startCamera}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {isStreaming ? 'Stop Camera' : 'Start Camera'}
          </button>
        </div>
      </div>

      {errorMsg ? (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-500" />
          {errorMsg}
        </div>
      ) : (
        <div className="relative bg-slate-900 rounded-xl overflow-hidden aspect-video flex items-center justify-center border border-slate-800">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover ${isStreaming ? 'block' : 'hidden'}`}
          />
          <canvas ref={canvasRef} className="hidden" />

          {!isStreaming && (
            <div className="text-center p-6 text-slate-400">
              <Camera className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Camera is currently stopped.</p>
            </div>
          )}

          {/* Scanner Overlay Box */}
          {isStreaming && (
            <div className="absolute inset-0 border-2 border-indigo-500/30 pointer-events-none flex items-center justify-center">
              <div className="w-64 h-64 border-2 border-dashed border-indigo-400/70 rounded-full animate-pulse flex items-center justify-center">
                <span className="text-xs font-medium text-indigo-200 bg-slate-900/60 px-2 py-1 rounded">
                  Center Face Here
                </span>
              </div>
            </div>
          )}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="absolute inset-0 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center">
              <div className="bg-white rounded-xl p-4 flex items-center gap-3 shadow-lg">
                <RefreshCw className="w-5 h-5 text-indigo-600 animate-spin" />
                <span className="text-sm font-medium text-slate-800">Matching face...</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Trigger & Feedback Banner */}
      <div className="mt-4 space-y-3">
        <button
          onClick={captureAndSend}
          disabled={!isStreaming || isProcessing}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-medium text-sm transition-colors flex items-center justify-center gap-2 shadow-xs"
        >
          <UserCheck className="w-4 h-4" />
          Capture & Mark Attendance Now
        </button>

        {lastResult && (
          <div
            className={`p-4 rounded-xl border flex items-start gap-3 text-sm transition-all ${
              lastResult.success && lastResult.attendance_marked
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : lastResult.already_marked
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {lastResult.success && lastResult.attendance_marked ? (
              <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-500 mt-0.5" />
            )}
            <div className="flex-1">
              <div className="font-semibold text-base">{lastResult.message}</div>
              {lastResult.student_id && (
                <div className="mt-1 text-xs space-y-0.5 opacity-90">
                  <p>
                    <span className="font-medium">Student ID:</span> {lastResult.student_id}
                  </p>
                  {lastResult.similarity !== undefined && lastResult.similarity !== null && (
                    <p>
                      <span className="font-medium">Face Match Similarity:</span>{' '}
                      {(lastResult.similarity * 100).toFixed(1)}%
                    </p>
                  )}
                  {lastResult.status && (
                    <p>
                      <span className="font-medium">Attendance Status:</span> {lastResult.status}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AttendanceCamera;
