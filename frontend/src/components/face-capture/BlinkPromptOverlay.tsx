import React from 'react';
import { MdVisibility } from 'react-icons/md';

/**
 * Overlay displayed during blink verification prompt.
 * Shows an eye icon with pulsing animation and countdown timer.
 */
const BlinkPromptOverlay: React.FC<{ countdown: number }> = ({ countdown }) => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/30 backdrop-blur-sm">
    <MdVisibility className="text-white/90 drop-shadow-lg animate-pulse" size={48} />
    <p className="text-white font-black text-lg mt-2 tracking-wide animate-pulse">Blink now!</p>
    <p className="text-white/70 text-xs mt-1">{countdown}s remaining</p>
  </div>
);

export default BlinkPromptOverlay;
