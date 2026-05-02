import React, { useEffect, useRef, useMemo, useCallback } from 'react';
import { useFaceRecognition } from '../../hooks/face-recognition';
import { FaceStatus } from '../../types/vid';
import { MdCameraAlt, MdSkipNext } from 'react-icons/md';
import clsx from 'clsx';
import SuccessOverlay from './SuccessOverlay';
import BlinkPromptOverlay from './BlinkPromptOverlay';
import ErrorOverlay from './ErrorOverlay';
import StatusMessage from './StatusMessage';
import { TERMINAL_STATUSES } from './types';

/**
 * FaceCapture component handles face verification with camera feed and blink detection.
 * Displays camera viewport, status messages, and overlays for different verification states.
 */
const FaceCapture: React.FC<{ onBiometricResult: (passed: boolean | null) => void }> = ({ onBiometricResult }) => {
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
