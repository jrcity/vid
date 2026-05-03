import { useState, useEffect, useRef, useCallback } from 'react';
import { FaceStatus } from '../../types/vid';
import { loadModelOnce } from './types';

/**
 * Manages camera stream initialization, lifecycle, and cleanup.
 * Handles face-api model loading and media stream acquisition.
 * No biometric data leaves this device.
 */
export function useCamera(
  setStatus: (status: FaceStatus) => void,
  setStatusSafe: (status: FaceStatus) => void,
  setIsReady: (ready: boolean) => void
) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  /** Stops all active media streams */
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  /** Initialize: load models and start camera */
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
    return () => { cancelled = true; stopCamera(); };
  }, [setStatusSafe, setIsReady, stopCamera]);

  return {
    videoRef,
    streamRef,
    stopCamera,
  };
}
