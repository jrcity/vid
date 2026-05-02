import React from 'react';
import { FaceStatus } from '../../types/vid';
import { STATUS_MESSAGES } from './types';

/**
 * Overlay displayed when face recognition encounters an error or times out.
 * Shows the appropriate status message based on the current state.
 */
const ErrorOverlay: React.FC<{ status: FaceStatus }> = ({ status }) => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-800/80">
    <p className="text-slate-300 text-sm text-center px-4">{STATUS_MESSAGES[status]}</p>
  </div>
);

export default ErrorOverlay;
