/**
 * Reliability Color Utilities
 * 
 * Maps reliability scores to colors:
 * - green: High reliability (0.8-1.0)
 * - yellow: Moderate reliability (0.5-0.79)
 * - red: Lower reliability (0.0-0.49)
 */

import type { ReliabilityColor } from '../types/paper';

export const RELIABILITY_COLORS = {
  green: {
    bg: 'bg-green-100',
    border: 'border-green-400',
    text: 'text-green-800',
    dot: 'bg-green-500',
    label: 'High Reliability'
  },
  yellow: {
    bg: 'bg-yellow-100',
    border: 'border-yellow-400',
    text: 'text-yellow-800',
    dot: 'bg-yellow-500',
    label: 'Moderate Reliability'
  },
  red: {
    bg: 'bg-red-100',
    border: 'border-red-400',
    text: 'text-red-800',
    dot: 'bg-red-500',
    label: 'Lower Reliability'
  }
} as const;

export function getReliabilityColor(score: number): ReliabilityColor {
  if (score >= 0.8) return 'green';
  if (score >= 0.5) return 'yellow';
  return 'red';
}

export function getReliabilityLabel(color: ReliabilityColor): string {
  return RELIABILITY_COLORS[color].label;
}

export function getReliabilityClasses(color: ReliabilityColor) {
  return RELIABILITY_COLORS[color];
}
