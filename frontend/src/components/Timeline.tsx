/**
 * Timeline Component
 * 
 * Displays papers chronologically from earliest to latest.
 * Shows research evolution over time.
 */

import React, { useMemo } from 'react';
import type { Paper } from '../types/paper';
import { getReliabilityClasses } from '../utils/colors';

interface TimelineProps {
  papers: Paper[];
  onPaperSelect?: (paper: Paper) => void;
}

interface YearGroup {
  year: number;
  papers: Paper[];
}

export const Timeline: React.FC<TimelineProps> = ({ papers, onPaperSelect }) => {
  const yearGroups = useMemo(() => {
    const groups: Map<number, Paper[]> = new Map();
    
    papers.forEach(paper => {
      if (paper.year) {
        const existing = groups.get(paper.year) || [];
        existing.push(paper);
        groups.set(paper.year, existing);
      }
    });
    
    const sorted: YearGroup[] = Array.from(groups.entries())
      .map(([year, papers]) => ({ year, papers }))
      .sort((a, b) => a.year - b.year);
    
    return sorted;
  }, [papers]);

  if (yearGroups.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No papers with year information available.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Research Timeline</h3>
        <p className="text-xs text-gray-500 mt-1">
          {yearGroups[0]?.year} - {yearGroups[yearGroups.length - 1]?.year} 
          ({papers.filter(p => p.year).length} papers)
        </p>
      </div>
      
      <div className="p-4 max-h-96 overflow-y-auto">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
          
          {yearGroups.map((group, groupIndex) => (
            <div key={group.year} className="relative pl-10 pb-6">
              {/* Year marker */}
              <div className="absolute left-2 w-5 h-5 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center font-bold">
                {group.papers.length}
              </div>
              
              {/* Year label */}
              <div className="font-bold text-gray-900 mb-2">{group.year}</div>
              
              {/* Papers */}
              <div className="space-y-2">
                {group.papers.slice(0, 5).map(paper => {
                  const colors = getReliabilityClasses(paper.reliability.color);
                  
                  return (
                    <div
                      key={paper.id}
                      className={`p-2 rounded border-l-2 ${colors.border} bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors`}
                      onClick={() => onPaperSelect?.(paper)}
                    >
                      <div className="text-sm font-medium text-gray-800 line-clamp-2">
                        {paper.title}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {paper.authorString}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`w-2 h-2 rounded-full ${colors.dot}`} />
                        <span className="text-xs text-gray-400">
                          {paper.citationCount} citations
                        </span>
                      </div>
                    </div>
                  );
                })}
                
                {group.papers.length > 5 && (
                  <div className="text-xs text-gray-400 pl-2">
                    +{group.papers.length - 5} more papers
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Timeline;
