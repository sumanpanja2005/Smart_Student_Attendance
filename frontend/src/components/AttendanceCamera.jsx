import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, RefreshCw, AlertCircle, CheckCircle, UserCheck, Sun, Zap, Sparkles } from 'lucide-react';

const AttendanceCamera = ({ onCaptureFrame, isProcessing = false, lastResult = null }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const isBusyRef = useRef(false);

  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [autoScan, setAutoScan] = useState(true);
  const [scanStats, setScanStats] = useState({ count: 0, lastScannedAt: null });

  // Sync isBusy ref with isProcessing prop
  useEffect(() => {
    isBusyRef.current = isProcessing;
  }, [isProcessing]);

  // Initialize webcam
  const startCamera = async () => {
    setErrorMsg('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsStreaming(true);
    } catch (err) {
      console.error('Webcam access error:', err);
      setErrorMsg('Unable to access camera. Please allow camera permissions in your browser.');
      setIsStreaming(false);
    }
  };

  // Stop webcam and release tracks
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  const captureAndSend = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isStreaming || isBusyRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob && onCaptureFrame && !isBusyRef.current) {
          setScanStats((prev) => ({ count: prev.count + 1, lastScannedAt: new Date().toLocaleTimeString() }));
          onCaptureFrame(blob);
        }
      },
      'image/jpeg',
      0.92
    );
  }, [isStreaming, onCaptureFrame]);

  // Fast, intelligent auto-scan interval with responsive polling
  useEffect(() => {
    if (!autoScan || !isStreaming) return;

    const intervalId = setInterval(() => {
      if (!isBusyRef.current) {
        captureAndSend();
      }
    }, 1200);

    return () => clearInterval(intervalId);
  }, [autoScan, isStreaming, captureAndSend]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
          <Camera className="w-5 h-5 text-indigo-600" />
          Live Attendance Scanner
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoScan(!autoScan)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              autoScan
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Zap className={`w-3.5 h-3.5 ${autoScan ? 'text-amber-300 fill-amber-300' : ''}`} />
            {autoScan ? 'Auto-Scan ON' : 'Enable Auto-Scan'}
          </button>
          <button
            onClick={isStreaming ? stopCamera : startCamera}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {isStreaming ? 'Stop' : 'Start'}
          </button>
        </div>
      </div>

      {errorMsg ? (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-500" />
          {errorMsg}
        </div>
      ) : (
        <div className="relative bg-slate-950 rounded-xl overflow-hidden aspect-video flex items-center justify-center border border-slate-800 shadow-inner">
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
              <Camera className="w-12 h-12 mx-auto mb-2 opacity-40" />
              <p className="text-xs">Camera is currently paused.</p>
              <button
                onClick={startCamera}
                className="mt-3 px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700"
              >
                Turn On Camera
              </button>
            </div>
          )}

          {/* Scanner Overlay Box & Laser Animation */}
          {isStreaming && (
            <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center">
              <div className="relative w-56 h-56 border-2 border-dashed border-indigo-400/80 rounded-2xl flex items-center justify-center shadow-lg">
                {/* Corner accents */}
                <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-indigo-400"></div>
                <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-indigo-400"></div>
                <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-indigo-400"></div>
                <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-indigo-400"></div>

                {/* Laser scanline */}
                {autoScan && (
                  <div className="absolute left-1 right-1 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-bounce opacity-80" />
                )}

                <span className="text-[11px] font-semibold text-indigo-100 bg-slate-900/80 px-2.5 py-1 rounded-full backdrop-blur-xs border border-indigo-500/30">
                  Align Face in Box
                </span>
              </div>

              {/* Low-light smart boost indicator */}
              <div className="absolute bottom-2 left-2 flex items-center gap-1.5 bg-slate-900/70 text-slate-300 text-[10px] px-2 py-0.5 rounded-md border border-slate-700">
                <Sun className="w-3 h-3 text-amber-400" />
                <span>Smart Auto-Illumination Active</span>
              </div>
            </div>
          )}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center transition-all">
              <div className="bg-white/95 rounded-xl px-4 py-3 flex items-center gap-3 shadow-xl border border-slate-200">
                <RefreshCw className="w-4 h-4 text-indigo-600 animate-spin" />
                <span className="text-xs font-bold text-slate-800 tracking-wide">Recognizing Face...</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Trigger & Live Feedback Result */}
      <div className="mt-4 space-y-3">
        <button
          onClick={captureAndSend}
          disabled={!isStreaming || isProcessing}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-xs"
        >
          <UserCheck className="w-4 h-4" />
          Mark Attendance (Manual Capture)
        </button>

        {lastResult && (
          <div
            className={`p-3.5 rounded-xl border flex items-start gap-3 text-xs transition-all animate-fadeIn ${
              lastResult.success && lastResult.attendance_marked
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : lastResult.already_marked
                ? 'bg-amber-50 border-amber-300 text-amber-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}
          >
            {lastResult.success && lastResult.attendance_marked ? (
              <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
            ) : lastResult.already_marked ? (
              <Sparkles className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-500 mt-0.5" />
            )}
            <div className="flex-1 space-y-0.5">
              <div className="font-bold text-sm leading-snug">{lastResult.message}</div>
              {lastResult.student_id && (
                <div className="pt-1 text-[11px] grid grid-cols-2 gap-x-2 gap-y-0.5 opacity-90 font-medium">
                  <div>
                    <span className="text-slate-500">Student:</span> {lastResult.student_id}
                  </div>
                  {lastResult.similarity !== undefined && lastResult.similarity !== null && (
                    <div>
                      <span className="text-slate-500">Match:</span>{' '}
                      <span className="font-bold">{(lastResult.similarity * 100).toFixed(1)}%</span>
                    </div>
                  )}
                  {lastResult.status && (
                    <div className="col-span-2">
                      <span className="text-slate-500">Status:</span>{' '}
                      <span className="font-bold uppercase">{lastResult.status}</span>
                    </div>
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

