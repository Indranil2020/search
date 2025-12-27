/**
 * Reliability Badge Component
 * 
 * Displays color-coded reliability indicator:
 * - Green: High reliability (peer-reviewed, highly cited, verified)
 * - Yellow: Moderate reliability (preprints, newer papers)
 * - Red: Lower reliability (unverified, retracted)
 */

import React from 'react';
import type { ReliabilityScore } from '../types/paper';
import { getReliabilityClasses } from '../utils/colors';

interface ReliabilityBadgeProps {
  reliability: ReliabilityScore;
  showDetails?: boolean;
}

export const ReliabilityBadge: React.FC<ReliabilityBadgeProps> = ({ 
  reliability, 
  showDetails = false 
}) => {
  const colors = getReliabilityClasses(reliability.color);
  const percentage = Math.round(reliability.score * 100);

  return (
    <div className="inline-flex flex-col items-end">
      <div className={`flex items-center gap-1.5 px-2 py-1 rounded ${colors.bg} ${colors.text}`}>
        <span className={`w-2 h-2 rounded-full ${colors.dot}`} />
        <span className="text-xs font-medium">{percentage}%</span>
      </div>
      
      {showDetails && (
        <div className="mt-1 text-xs text-gray-500">
          <div>Peer Review: {Math.round(reliability.components.peerReview * 100)}%</div>
          <div>Journal: {Math.round(reliability.components.journal * 100)}%</div>
          <div>Citations: {Math.round(reliability.components.citations * 100)}%</div>
          <div>Verified: {Math.round(reliability.components.verification * 100)}%</div>
          {reliability.isRetracted && (
            <div className="text-red-600 font-bold">RETRACTED</div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReliabilityBadge;
