import { useEffect, useRef, useCallback } from 'react';
import * as faceapi from '@vladmandic/face-api';
import { FaceStatus } from '../../types/vid';
import { DETECTION_INTERVAL_MS } from './types';
import { detectFace } from './types';

/**
 * Handles face detection logic including drawing bounding boxes and running detection loop.
 * No biometric data leaves this device.
 */
export function useFaceDetection(
  videoRef: React.RefObject<HTMLVideoElement>,
  canvasRef: React.RefObject<HTMLCanvasElement>,
  status: FaceStatus,
  handleDetectionResult: (faceDetected: boolean) => void
) {
  const intervalRef = useRef<number | null>(null);

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
  }, [canvasRef]);

  /** Detection loop - runs at interval when in active states */
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
  }, [status, videoRef, drawDetection, handleDetectionResult]);

  return {
    drawDetection,
    intervalRef,
  };
}
