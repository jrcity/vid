import { FaceStatus } from '../../types/vid';
import * as faceapi from '@vladmandic/face-api';

/** Configuration constants for face recognition */
export const MODEL_URL = 'https://vladmandic.github.io/face-api/model';
export const MODEL_LOAD_TIMEOUT_MS = 10000;
export const DETECTION_INTERVAL_MS = 200;
export const BLINK_PROMPT_DELAY_MS = 800;
export const BLINK_VERIFICATION_TIMEOUT_MS = 5000;
export const COUNTDOWN_SECONDS = 5;

/** Return type for the main useFaceRecognition hook */
export interface UseFaceRecognitionReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  status: FaceStatus;
  isReady: boolean;
  biometricPassed: boolean | null;
  blinkCountdown: number;
  cleanup: () => void;
}

export type { FaceStatus } from '../../types/vid';

/** Cached model load promise to avoid reloading */
let modelLoadPromise: Promise<void> | null = null;

/**
 * Loads face-api models once and caches the promise.
 * Subsequent calls return the same promise.
 * No biometric data leaves this device.
 */
export function loadModelOnce(): Promise<void> {
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
 * No biometric data leaves this device.
 */
export async function detectFace(video: HTMLVideoElement): Promise<faceapi.FaceDetection | null> {
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
