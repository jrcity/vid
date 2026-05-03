import { useState, useRef, useCallback, useEffect } from 'react';
import { FaceStatus } from '../../types/vid';
import { useCamera } from './useCamera';
import { useFaceDetection } from './useFaceDetection';
import { useBlinkDetection } from './useBlinkDetection';

/**
 * Main hook that orchestrates face recognition by combining smaller hooks.
 * No biometric data leaves this device.
 */
export function useFaceRecognition() {
  const [status, setStatus] = useState<FaceStatus>('loading');
  const [isReady, setIsReady] = useState(false);
  const [biometricPassed, setBiometricPassed] = useState<boolean | null>(null);
  const [blinkCountdown, setBlinkCountdown] = useState(0);

  const statusRef = useRef<FaceStatus>('loading');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  /** Safely updates both state and ref */
  const setStatusSafe = useCallback((s: FaceStatus) => {
    statusRef.current = s;
    setStatus(s);
  }, []);

  /** Camera hook */
  const { videoRef, stopCamera } = useCamera(
    setStatus,
    setStatusSafe,
    setIsReady
  );

  /** Clear interval helper */
  const clearIntervalRef = useCallback((intervalRefCurrent: number | null) => {
    if (intervalRefCurrent) {
      clearInterval(intervalRefCurrent);
    }
  }, []);

  /** Blink detection hook */
  const {
    handleDetectionResult: blinkHandleDetectionResult,
    clearBlinkTimers,
  } = useBlinkDetection(
    statusRef,
    setStatusSafe,
    setBiometricPassed,
    setBlinkCountdown,
    () => clearIntervalRef(intervalRef.current)
  );

  /** Face detection hook */
  const { intervalRef, drawDetection } = useFaceDetection(
    videoRef,
    canvasRef,
    status,
    (faceDetected: boolean) => blinkHandleDetectionResult(faceDetected, intervalRef.current)
  );

  /** Cleanup function */
  const cleanup = useCallback(() => {
    stopCamera();
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    clearBlinkTimers();
  }, [stopCamera, clearBlinkTimers]);

  return {
    videoRef,
    canvasRef,
    status,
    isReady,
    biometricPassed,
    blinkCountdown,
    cleanup,
  };
}
