import * as faceapi from '@vladmandic/face-api';
import { useState, useEffect, useRef, useCallback } from 'react';
import { FaceStatus } from '../types/vid';

// No biometric data leaves this device

/** Configuration constants for face recognition */
const MODEL_URL = 'https://vladmandic.github.io/face-api/model';
const MODEL_LOAD_TIMEOUT_MS = 10000;
const DETECTION_INTERVAL_MS = 200;
const BLINK_PROMPT_DELAY_MS = 800;
const BLINK_VERIFICATION_TIMEOUT_MS = 5000;
const COUNTDOWN_SECONDS = 5;

/** Cached model load promise to avoid reloading */
let modelLoadPromise: Promise<void> | null = null;

/**
 * Loads face-api models once and caches the promise.
 * Subsequent calls return the same promise.
 */
function loadModelOnce(): Promise<void> {
  if (modelLoadPromise) return modelLoadPromise;

  modelLoadPromise = new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      modelLoadPromise = null;
      reject(new Error('Model load timed out after 10 seconds'));
    }, MODEL_LOAD_TIMEOUT_MS);

    faceapi.nets.tinyFaceDetector
      .loadFromUri(MODEL_URL)
      .then(() => {
        clearTimeout(timeoutId);
        resolve();
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        modelLoadPromise = null;
        reject(err);
      });
  });

  return modelLoadPromise;
}

/**
 * Detects a single face in the video stream.
 * Returns null if no face is detected or an error occurs.
 */
async function detectFace(video: HTMLVideoElement): Promise<faceapi.FaceDetection | null> {
  if (video.readyState !== video.HAVE_ENOUGH_DATA) return null;

  try {
    const detection = await faceapi.detectSingleFace(
      video,
      new faceapi.TinyFaceDetectorOptions({ inputSize: 320 }),
    );
    return detection ?? null;
  } catch (err) {
    console.error('[FaceDetection] Error:', err);
    return null;
  }
}

export interface UseFaceRecognitionReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  status: FaceStatus;
  isReady: boolean;
  biometricPassed: boolean | null;
  blinkCountdown: number;
  cleanup: () => void;
}

/** Safely clears a timer reference */
const clearTimer = (ref: React.MutableRefObject<number | null>): void => {
  if (ref.current !== null) {
    clearTimeout(ref.current);
    ref.current = null;
  }
};

export function useFaceRecognition(): UseFaceRecognitionReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [status, setStatus] = useState<FaceStatus>('loading');
  const [isReady, setIsReady] = useState(false);
  const [biometricPassed, setBiometricPassed] = useState<boolean | null>(null);
  const [blinkCountdown, setBlinkCountdown] = useState(0);

  // Refs for stable access in callbacks
  const statusRef = useRef<FaceStatus>('loading');
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number | null>(null);
  const faceDetectedDelayRef = useRef<number | null>(null);
  const countdownTickTimerRef = useRef<number | null>(null);
  const blinkFailTimerRef = useRef<number | null>(null);
  const countdownRef = useRef(0);

  /** Safely updates both state and ref */
  const setStatusSafe = useCallback((s: FaceStatus) => {
    statusRef.current = s;
    setStatus(s);
  }, []);

  /** Stops all active media streams and timers */
  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    clearTimer(faceDetectedDelayRef);
    clearTimer(countdownTickTimerRef);
    clearTimer(blinkFailTimerRef);
  }, []);

  /** Draws face bounding box on canvas overlay */
  const drawDetection = useCallback((video: HTMLVideoElement, detection: faceapi.FaceDetection | null) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (detection) {
      const { x, y, width, height } = detection.box;
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, width, height);
    }
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
  }, [setStatusSafe]);

  /** Handles state transitions based on face detection results */
  const handleDetectionResult = useCallback((faceDetected: boolean) => {
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
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      clearTimer(blinkFailTimerRef);
      clearTimer(countdownTickTimerRef);
    }
  }, [setStatusSafe, startBlinkVerification]);

  // Initialize: load models and start camera
  useEffect(() => {
    let cancelled = false;

    async function init() {
      let stream: MediaStream | null = null;
      try {
        await loadModelOnce();
        if (cancelled) return;

        setStatusSafe('starting');

        stream = await Promise.race([
          navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          }),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Camera access timed out')), 10000)
          ),
        ]) as MediaStream;

        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play();
        }

        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        // Only assign to ref after play() succeeds
        streamRef.current = stream;

        setStatusSafe('searching');
        setIsReady(true);
      } catch (err) {
        if (cancelled) return;
        console.error('[FaceRecognition] Init failed:', err);
        // Stop stream tracks if acquired but play failed or other error occurred
        if (stream) {
          stream.getTracks().forEach((t) => t.stop());
        }
        setStatusSafe('error');
      }
    }

    init();
    return () => { cancelled = true; cleanup(); };
  }, [cleanup, setStatusSafe]);

  // Detection loop
  useEffect(() => {
    if (status !== 'searching' && status !== 'face_detected' && status !== 'blink_prompt') return;

    intervalRef.current = window.setInterval(async () => {
      const video = videoRef.current;
      if (!video) return;

      const detection = await detectFace(video);
      drawDetection(video, detection);
      handleDetectionResult(!!detection);
    }, DETECTION_INTERVAL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status, drawDetection, handleDetectionResult]);

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
