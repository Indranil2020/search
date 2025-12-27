/**
 * Stats Component
 * 
 * Displays search statistics overview.
 */

import React from 'react';
import type { SearchResult } from '../types/paper';

interface StatsProps {
  result: SearchResult;
}

export const Stats: React.FC<StatsProps> = ({ result }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
      <StatCard
        label="Total Papers"
        value={result.totalFound}
        color="blue"
      />
      <StatCard
        label="High Reliability"
        value={result.reliability.high}
        color="green"
      />
      <StatCard
        label="Moderate"
        value={result.reliability.medium}
        color="yellow"
      />
      <StatCard
        label="Lower"
        value={result.reliability.low}
        color="red"
      />
      <StatCard
        label="Open Access"
        value={result.access.open}
        color="emerald"
      />
      <StatCard
        label="Search Time"
        value={`${result.searchTimeSeconds}s`}
        color="gray"
      />
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: number | string;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, color }) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    gray: 'bg-gray-50 border-gray-200 text-gray-700'
  };

  return (
    <div className={`rounded-lg border p-3 ${colorClasses[color]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs opacity-75">{label}</div>
    </div>
  );
};

export default Stats;
