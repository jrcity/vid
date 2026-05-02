import React, { useEffect, useRef } from 'react';
import { useFaceRecognition } from '../hooks/useFaceRecognition';
import { MdCameraAlt, MdCheckCircle, MdSkipNext, MdVisibility } from 'react-icons/md';
import clsx from 'clsx';

// No biometric data leaves this device

interface FaceCaptureProps {
  onBiometricResult: (passed: boolean | null) => void;
}

const statusMessages: Record<string, string> = {
  loading: 'Loading facial recognition...',
  starting: 'Opening camera...',
  searching: 'Position your face in the frame',
  face_detected: 'Face detected! Get ready...',
  blink_prompt: 'Blink now!',
  blink_detected: 'Biometric verified',
  failed: 'Verification timed out',
  error: 'Camera access denied',
};

const FaceCapture: React.FC<FaceCaptureProps> = ({ onBiometricResult }) => {
  const { videoRef, canvasRef, status, biometricPassed, blinkCountdown, cleanup } =
    useFaceRecognition();
  const hasNotified = useRef(false);

  useEffect(() => {
    if (hasNotified.current) return;

    if (biometricPassed === true) {
      hasNotified.current = true;
      onBiometricResult(true);
    } else if (status === 'error' || status === 'failed') {
      hasNotified.current = true;
      onBiometricResult(null);
    }
  }, [biometricPassed, status, onBiometricResult]);

  const handleSkip = () => {
    cleanup();
    if (!hasNotified.current) {
      hasNotified.current = true;
      onBiometricResult(null);
    }
  };

  const isTerminal = status === 'blink_detected';

  return (
    <div className="native-card p-4 space-y-4 animate-in fade-in slide-in-from-bottom-4">
      <div className="flex items-center gap-2 text-brand-dark">
        <MdCameraAlt className="text-xl text-brand-accent" />
        <h3 className="font-bold text-sm uppercase tracking-wide">Face Verification</h3>
      </div>

      {/* Camera viewport */}
      <div className="relative w-full aspect-video bg-slate-900 rounded-2xl overflow-hidden shadow-inner">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover"
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full h-full pointer-events-none"
        />

        {/* Green tick overlay on success */}
        {biometricPassed === true && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-emerald-500/20 backdrop-blur-sm animate-in zoom-in-75 duration-300">
            <MdCheckCircle className="text-emerald-400 drop-shadow-lg" size={72} />
            <p className="text-emerald-300 font-bold text-sm mt-2 tracking-wide">
              Verified
            </p>
          </div>
        )}

        {/* Blink prompt overlay */}
        {status === 'blink_prompt' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/30 backdrop-blur-sm">
            <MdVisibility className="text-white/90 drop-shadow-lg animate-pulse" size={48} />
            <p className="text-white font-black text-lg mt-2 tracking-wide animate-pulse">
              Blink now!
            </p>
            <p className="text-white/70 text-xs mt-1">{blinkCountdown}s remaining</p>
          </div>
        )}

        {/* Camera denied / failed overlay */}
        {(status === 'error' || status === 'failed') && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-800/80">
            <p className="text-slate-300 text-sm text-center px-4">
              {statusMessages[status]}
            </p>
          </div>
        )}
      </div>

      {/* Status message */}
      <div className="text-center">
        <p
          className={clsx(
            'text-sm font-medium',
            status === 'error'
              ? 'text-red-500'
              : status === 'blink_detected'
                ? 'text-emerald-600 font-bold'
                : 'text-slate-600',
          )}
        >
          {statusMessages[status]}
        </p>
        {(status === 'error' || status === 'failed') && (
          <p className="text-xs text-slate-400 mt-1">
            Biometric step skipped — you can still enroll
          </p>
        )}
      </div>

      {/* Skip button (hidden when terminal) */}
      {!isTerminal && (
        <button
          type="button"
          onClick={handleSkip}
          className="w-full native-button bg-slate-100 text-slate-500 hover:bg-slate-200 flex items-center justify-center gap-2 text-sm font-semibold"
        >
          <MdSkipNext size={18} />
          Skip Biometric
        </button>
      )}
    </div>
  );
};

export default FaceCapture;
