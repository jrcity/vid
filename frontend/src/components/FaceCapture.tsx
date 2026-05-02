import React, { useEffect, useRef, useMemo, useCallback } from 'react';
import { useFaceRecognition } from '../hooks/useFaceRecognition';
import { FaceStatus } from '../types/vid';
import { MdCameraAlt, MdCheckCircle, MdSkipNext, MdVisibility } from 'react-icons/md';
import clsx from 'clsx';

// No biometric data leaves this device

interface FaceCaptureProps {
  onBiometricResult: (passed: boolean | null) => void;
}

/** Maps face status to user-facing messages */
const STATUS_MESSAGES: Record<FaceStatus, string> = {
  loading: 'Loading facial recognition...',
  starting: 'Opening camera...',
  searching: 'Position your face in the frame',
  face_detected: 'Face detected! Get ready...',
  blink_prompt: 'Blink now!',
  blink_detected: 'Biometric verified',
  failed: 'Verification timed out',
  error: 'Camera access denied',
};

// Sub-components for camera overlays
const SuccessOverlay: React.FC = () => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-emerald-500/20 backdrop-blur-sm animate-in zoom-in-75 duration-300">
    <MdCheckCircle className="text-emerald-400 drop-shadow-lg" size={72} />
    <p className="text-emerald-300 font-bold text-sm mt-2 tracking-wide">Verified</p>
  </div>
);

const BlinkPromptOverlay: React.FC<{ countdown: number }> = ({ countdown }) => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/30 backdrop-blur-sm">
    <MdVisibility className="text-white/90 drop-shadow-lg animate-pulse" size={48} />
    <p className="text-white font-black text-lg mt-2 tracking-wide animate-pulse">Blink now!</p>
    <p className="text-white/70 text-xs mt-1">{countdown}s remaining</p>
  </div>
);

const ErrorOverlay: React.FC<{ status: FaceStatus }> = ({ status }) => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-800/80">
    <p className="text-slate-300 text-sm text-center px-4">{STATUS_MESSAGES[status]}</p>
  </div>
);

const StatusMessage: React.FC<{ status: FaceStatus }> = ({ status }) => {
  const isError = status === 'error';
  const isSuccess = status === 'blink_detected';
  const showSkipHint = status === 'error' || status === 'failed';

  return (
    <div className="text-center">
      <p
        className={clsx(
          'text-sm font-medium',
          isError && 'text-red-500',
          isSuccess && 'text-emerald-600 font-bold',
          !isError && !isSuccess && 'text-slate-600',
        )}
      >
        {STATUS_MESSAGES[status]}
      </p>
      {showSkipHint && (
        <p className="text-xs text-slate-400 mt-1">Biometric step skipped — you can still enroll</p>
      )}
    </div>
  );
};

/** Terminal states where no further action is needed */
const TERMINAL_STATUSES: Set<FaceStatus> = new Set(['blink_detected', 'error', 'failed']);

const FaceCapture: React.FC<FaceCaptureProps> = ({ onBiometricResult }) => {
  const { videoRef, canvasRef, status, biometricPassed, blinkCountdown, cleanup } =
    useFaceRecognition();
  const notifiedRef = useRef(false);

  /** Notify parent of result exactly once */
  const notifyOnce = useCallback((result: boolean | null) => {
    if (notifiedRef.current) return;
    notifiedRef.current = true;
    onBiometricResult(result);
  }, [onBiometricResult]);

  useEffect(() => {
    if (notifiedRef.current) return;

    if (biometricPassed === true) {
      notifyOnce(true);
    } else if (status === 'error' || status === 'failed') {
      notifyOnce(null);
    }
  }, [biometricPassed, status, notifyOnce]);

  const handleSkip = useCallback(() => {
    cleanup();
    notifyOnce(null);
  }, [cleanup, notifyOnce]);

  const isTerminal = TERMINAL_STATUSES.has(status);

  /** Determine which overlay to show, if any */
  const overlay = useMemo(() => {
    if (biometricPassed === true) return <SuccessOverlay />;
    if (status === 'blink_prompt') return <BlinkPromptOverlay countdown={blinkCountdown} />;
    if (status === 'error' || status === 'failed') return <ErrorOverlay status={status} />;
    return null;
  }, [biometricPassed, status, blinkCountdown]);

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
        <canvas ref={canvasRef} className="absolute top-0 left-0 w-full h-full pointer-events-none" />
        {overlay}
      </div>

      <StatusMessage status={status} />

      {/* Skip button (hidden for terminal states) */}
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
