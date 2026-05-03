import React from 'react';
import { MdCheckCircle } from 'react-icons/md';

/**
 * Overlay displayed when biometric verification succeeds.
 * Shows a checkmark icon and "Verified" text with a green backdrop.
 */
const SuccessOverlay: React.FC = () => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-emerald-500/20 backdrop-blur-sm animate-in zoom-in-75 duration-300">
    <MdCheckCircle className="text-emerald-400 drop-shadow-lg" size={72} />
    <p className="text-emerald-300 font-bold text-sm mt-2 tracking-wide">Verified</p>
  </div>
);

export default SuccessOverlay;
