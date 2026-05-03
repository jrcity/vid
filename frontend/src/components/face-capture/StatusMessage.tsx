import React, { useMemo } from 'react';
import clsx from 'clsx';
import { FaceStatus } from '../../types/vid';
import { STATUS_MESSAGES, TERMINAL_STATUSES } from './types';

/**
 * Displays the current face recognition status as a text message.
 * Shows skip hint for error/failed states.
 */
const StatusMessage: React.FC<{ status: FaceStatus }> = ({ status }) => {
  const isError = status === 'error';
  const isSuccess = status === 'blink_detected';
  const showSkipHint = TERMINAL_STATUSES.has(status) && status !== 'blink_detected';

  return (
    <div className="text-center">
      <p
        className={clsx(
          'text-sm font-medium',
          isError && 'text-red-500',
          isSuccess && 'text-emerald-600 font-bold',
          !isError && !isSuccess && 'text-slate-600',
        )}
      >
        {STATUS_MESSAGES[status]}
      </p>
      {showSkipHint && (
        <p className="text-xs text-slate-400 mt-1">Biometric step skipped — you can still enroll</p>
      )}
    </div>
  );
};

export default StatusMessage;
