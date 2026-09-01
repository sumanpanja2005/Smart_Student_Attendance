import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Button } from './Button';
import { Camera, CameraOff, RefreshCw, AlertTriangle } from 'lucide-react';

export const CameraCapture = ({ onCapture, isProcessing = false, title = 'Webcam Stream' }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [snapshotUrl, setSnapshotUrl] = useState(null);

  // Stop camera stream & release hardware tracks
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  }, []);

  // Start camera stream
  const startCamera = async () => {
    setCameraError('');
    setSnapshotUrl(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access is not supported by your browser environment.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (err) {
      console.error('Camera initialization error:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError('Camera permission denied. Please allow camera access in your browser settings.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraError('No webcam hardware found on your device.');
      } else {
        setCameraError(err.message || 'Failed to start camera.');
      }
      stopCamera();
    }
  };

  // Ensure camera hardware tracks are stopped when navigating away or component unmounts
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  const captureSnapshot = () => {
    if (!videoRef.current || !canvasRef.current || !isCameraActive) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const previewUrl = URL.createObjectURL(blob);
          setSnapshotUrl(previewUrl);
          if (onCapture) {
            onCapture(blob);
          }
        }
      },
      'image/jpeg',
      0.9
    );
  };

  const retakeSnapshot = () => {
    if (snapshotUrl) {
      URL.revokeObjectURL(snapshotUrl);
    }
    setSnapshotUrl(null);
  };

  return (
    <div className="space-y-4">
      {/* Video / Snapshot Viewport */}
      <div className="relative aspect-video w-full max-w-md mx-auto bg-slate-900 rounded-2xl overflow-hidden shadow-inner border border-slate-800 flex items-center justify-center">
        {cameraError ? (
          <div className="p-6 text-center text-rose-400 space-y-2">
            <AlertTriangle className="w-10 h-10 mx-auto text-rose-500" />
            <p className="text-xs font-semibold">{cameraError}</p>
            <Button variant="outline" size="sm" onClick={startCamera}>
              Retry Camera Connection
            </Button>
          </div>
        ) : snapshotUrl ? (
          <img src={snapshotUrl} alt="Captured face snapshot" className="w-full h-full object-cover" />
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover ${!isCameraActive ? 'hidden' : ''}`}
          />
        )}

        {!isCameraActive && !cameraError && !snapshotUrl && (
          <div className="text-center p-6 space-y-3 text-slate-400">
            <Camera className="w-12 h-12 mx-auto text-slate-600" />
            <p className="text-xs">Click Start Camera to initialize video stream</p>
          </div>
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm flex flex-col items-center justify-center space-y-2 text-white text-xs font-medium">
            <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
            <span>Analyzing Face Frame...</span>
          </div>
        )}
      </div>

      {/* Hidden Canvas for Frame Capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {!isCameraActive ? (
          <Button variant="primary" size="sm" icon={Camera} onClick={startCamera}>
            Start Camera
          </Button>
        ) : snapshotUrl ? (
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={retakeSnapshot} disabled={isProcessing}>
            Retake Frame
          </Button>
        ) : (
          <>
            <Button variant="primary" size="sm" icon={Camera} onClick={captureSnapshot} isLoading={isProcessing}>
              Capture Frame
            </Button>
            <Button variant="ghost" size="sm" icon={CameraOff} onClick={stopCamera} disabled={isProcessing}>
              Stop Camera
            </Button>
          </>
        )}
      </div>
    </div>
  );
};

export default CameraCapture;
