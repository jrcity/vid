import * as faceapi from '@vladmandic/face-api';
import { useState, useEffect, useRef, useCallback } from 'react';

// No biometric data leaves this device

type FaceStatus =
  | 'loading'
  | 'starting'
  | 'searching'
  | 'face_detected'
  | 'blink_prompt'
  | 'blink_detected'
  | 'failed'
  | 'error';

const MODEL_URL = 'https://vladmandic.github.io/face-api/model';
const MODEL_LOAD_TIMEOUT = 10000; // 10s timeout for CDN model load

let modelLoadPromise: Promise<void> | null = null;

function loadModelOnce(): Promise<void> {
  if (modelLoadPromise) return modelLoadPromise;
  modelLoadPromise = new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      modelLoadPromise = null; // Allow retry
      reject(new Error('Model load timed out after 10 seconds'));
    }, MODEL_LOAD_TIMEOUT);

    faceapi.nets.tinyFaceDetector
      .loadFromUri(MODEL_URL)
      .then(() => {
        clearTimeout(timeoutId);
        resolve();
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        modelLoadPromise = null; // Allow retry
        reject(err);
      });
  });
  return modelLoadPromise;
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

export function useFaceRecognition(): UseFaceRecognitionReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [status, setStatus] = useState<FaceStatus>('loading');
  const [isReady, setIsReady] = useState(false);
  const [biometricPassed, setBiometricPassed] = useState<boolean | null>(null);
  const [blinkCountdown, setBlinkCountdown] = useState(0);

  const statusRef = useRef<FaceStatus>('loading');
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number | null>(null);
  const faceDetectedTimerRef = useRef<number | null>(null);
  const countdownTickTimerRef = useRef<number | null>(null);
  const blinkFailTimerRef = useRef<number | null>(null);
  const countdownRef = useRef<number>(0);
  const faceDetectedDelayRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (faceDetectedTimerRef.current) {
      clearTimeout(faceDetectedTimerRef.current);
      faceDetectedTimerRef.current = null;
    }
    if (countdownTickTimerRef.current) {
      clearTimeout(countdownTickTimerRef.current);
      countdownTickTimerRef.current = null;
    }
    if (blinkFailTimerRef.current) {
      clearTimeout(blinkFailTimerRef.current);
      blinkFailTimerRef.current = null;
    }
    if (faceDetectedDelayRef.current) {
      clearTimeout(faceDetectedDelayRef.current);
      faceDetectedDelayRef.current = null;
    }
  }, []);

  const setStatusSafe = useCallback((s: FaceStatus) => {
    statusRef.current = s;
    setStatus(s);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        await loadModelOnce();
        if (cancelled) return;

        setStatusSafe('starting');

        const stream = await Promise.race([
          navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          }),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Camera access timed out after 10 seconds')), 10000)
          ),
        ]) as MediaStream;

        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = stream;

        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play();
        }

        setStatusSafe('searching');
        setIsReady(true);
      } catch (err) {
        if (cancelled) return;
        console.error('Face recognition init failed:', err);
        setStatusSafe('error');
      }
    }

    init();
    return () => { cancelled = true; cleanup(); };
  }, [cleanup, setStatusSafe]);

  useEffect(() => {
    if (status !== 'searching' && status !== 'face_detected' && status !== 'blink_prompt') return;

    intervalRef.current = window.setInterval(async () => {
      const video = videoRef.current;
      if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) return;

      try {
        const detection = await faceapi.detectSingleFace(
          video,
          new faceapi.TinyFaceDetectorOptions({ inputSize: 320 }),
        );

        const faceDetected = !!detection;
        const currentStatus = statusRef.current;

        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            if (detection) {
              const { x, y, width, height } = detection.box;
              ctx.strokeStyle = '#10b981';
              ctx.lineWidth = 3;
              ctx.strokeRect(x, y, width, height);
            }
          }
        }

        if (currentStatus === 'searching' && faceDetected) {
          setStatusSafe('face_detected');
          faceDetectedDelayRef.current = window.setTimeout(() => {
            faceDetectedDelayRef.current = null;
            if (statusRef.current === 'face_detected') {
              setStatusSafe('blink_prompt');
              setBlinkCountdown(5);
              countdownRef.current = 5;

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
              }, 5000);
            }
          }, 800);
        }

        // Blink detection: face disappears during blink prompt = eyes closed
        // No biometric data leaves this device
        if (currentStatus === 'blink_prompt' && !faceDetected) {
          setBiometricPassed(true);
          setStatusSafe('blink_detected');
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          if (blinkFailTimerRef.current) {
            clearTimeout(blinkFailTimerRef.current);
            blinkFailTimerRef.current = null;
          }
        }
      } catch (err) {
        console.error('Face detection error:', err);
      }
    }, 200);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status, setStatusSafe]);

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
