import { FaceStatus } from '../../types/vid';

/** Props for the main FaceCapture component */
export interface FaceCaptureProps {
  onBiometricResult: (passed: boolean | null) => void;
}

/** Props for SuccessOverlay component */
export interface SuccessOverlayProps {
  // No props needed - pure presentational
}

/** Props for BlinkPromptOverlay component */
export interface BlinkPromptOverlayProps {
  countdown: number;
}

/** Props for ErrorOverlay component */
export interface ErrorOverlayProps {
  status: FaceStatus;
}

/** Props for StatusMessage component */
export interface StatusMessageProps {
  status: FaceStatus;
}

/** User-facing status messages mapping */
export const STATUS_MESSAGES: Record<FaceStatus, string> = {
  loading: 'Loading facial recognition...',
  starting: 'Opening camera...',
  searching: 'Position your face in the frame',
  face_detected: 'Face detected! Get ready...',
  blink_prompt: 'Blink now!',
  blink_detected: 'Biometric verified',
  failed: 'Verification timed out',
  error: 'Camera access denied',
};

/** Terminal states where no further action is needed */
export const TERMINAL_STATUSES: Set<FaceStatus> = new Set(['blink_detected', 'error', 'failed']);
