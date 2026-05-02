import { useRef, useCallback } from 'react';
import { FaceStatus } from '../../types/vid';
import { BLINK_VERIFICATION_TIMEOUT_MS, BLINK_PROMPT_DELAY_MS, COUNTDOWN_SECONDS } from './types';

/**
 * Safely clears a timer reference
 */
const clearTimer = (ref: React.MutableRefObject<number | null>): void => {
  if (ref.current !== null) {
    clearTimeout(ref.current);
    ref.current = null;
  }
};

/**
 * Handles blink verification logic including countdown and detection.
 * No biometric data leaves this device.
 */
export function useBlinkDetection(
  statusRef: React.MutableRefObject<FaceStatus>,
  setStatusSafe: (status: FaceStatus) => void,
  setBiometricPassed: (passed: boolean | null) => void,
  setBlinkCountdown: (countdown: number) => void,
  clearIntervalRef: () => void
) {
  const countdownRef = useRef(0);
  const countdownTickTimerRef = useRef<number | null>(null);
  const blinkFailTimerRef = useRef<number | null>(null);
  const faceDetectedDelayRef = useRef<number | null>(null);

  /** Clears all blink-related timers */
  const clearBlinkTimers = useCallback(() => {
    clearTimer(faceDetectedDelayRef);
    clearTimer(countdownTickTimerRef);
    clearTimer(blinkFailTimerRef);
  }, []);

  /** Starts the blink verification countdown flow */
  const startBlinkVerification = useCallback(() => {
    setStatusSafe('blink_prompt');
    countdownRef.current = COUNTDOWN_SECONDS;
    setBlinkCountdown(COUNTDOWN_SECONDS);

    const tick = () => {
      countdownRef.current -= 1;
      setBlinkCountdown(countdownRef.current);
      if (countdownRef.current > 0) {
        countdownTickTimerRef.current = window.setTimeout(tick, 1000);
      }
    };
    countdownTickTimerRef.current = window.setTimeout(tick, 1000);

    blinkFailTimerRef.current = window.setTimeout(() => {
      if (statusRef.current === 'blink_prompt') {
        setStatusSafe('failed');
        setBiometricPassed(null);
      }
    }, BLINK_VERIFICATION_TIMEOUT_MS);
  }, [setStatusSafe, setBiometricPassed, setBlinkCountdown]);

  /**
   * Handles state transitions based on face detection results.
   * Detects blink when face disappears during blink_prompt state.
   */
  const handleDetectionResult = useCallback((faceDetected: boolean, intervalRefCurrent: number | null) => {
    const currentStatus = statusRef.current;

    if (currentStatus === 'searching' && faceDetected) {
      setStatusSafe('face_detected');
      faceDetectedDelayRef.current = window.setTimeout(() => {
        faceDetectedDelayRef.current = null;
        if (statusRef.current === 'face_detected') {
          startBlinkVerification();
        }
      }, BLINK_PROMPT_DELAY_MS);
    }

    // Blink detected: face disappears during blink prompt
    // No biometric data leaves this device
    if (currentStatus === 'blink_prompt' && !faceDetected) {
      setBiometricPassed(true);
      setStatusSafe('blink_detected');
      setBlinkCountdown(0);
      if (intervalRefCurrent) {
        clearInterval(intervalRefCurrent);
      }
      clearBlinkTimers();
    }
  }, [setStatusSafe, startBlinkVerification, setBiometricPassed, setBlinkCountdown, clearBlinkTimers]);

  return {
    startBlinkVerification,
    handleDetectionResult,
    clearBlinkTimers,
    faceDetectedDelayRef,
    countdownTickTimerRef,
    blinkFailTimerRef,
  };
}
