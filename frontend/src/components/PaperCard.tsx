/**
 * Paper Card Component
 * 
 * Displays a paper with reliability color coding.
 * Left border indicates reliability level.
 */

import React, { useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp, FileText, BookOpen } from 'lucide-react';
import type { Paper } from '../types/paper';
import { ReliabilityBadge } from './ReliabilityBadge';
import { getReliabilityClasses } from '../utils/colors';

interface PaperCardProps {
  paper: Paper;
}

export const PaperCard: React.FC<PaperCardProps> = ({ paper }) => {
  const [expanded, setExpanded] = useState(false);
  const colors = getReliabilityClasses(paper.reliability.color);

  return (
    <div 
      className={`bg-white rounded-lg shadow-sm border-l-4 ${colors.border} hover:shadow-md transition-shadow`}
    >
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Title */}
            <h3 className="font-semibold text-gray-900 leading-tight">
              {paper.title}
            </h3>
            
            {/* Authors */}
            <p className="text-sm text-gray-600 mt-1">
              {paper.authorString}
            </p>
            
            {/* Meta */}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs text-gray-500">
              {paper.journal && (
                <span className="flex items-center gap-1">
                  <BookOpen className="w-3 h-3" />
                  {paper.journal}
                </span>
              )}
              {paper.year && <span>{paper.year}</span>}
              {paper.citationCount > 0 && (
                <span>{paper.citationCount} citations</span>
              )}
              <span className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600">
                {paper.source}
              </span>
            </div>
          </div>
          
          {/* Reliability + Expand */}
          <div className="flex flex-col items-end gap-2">
            <ReliabilityBadge reliability={paper.reliability} />
            
            <div className={`px-2 py-0.5 rounded text-xs ${
              paper.accessType === 'open' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-orange-100 text-orange-700'
            }`}>
              {paper.accessType === 'open' ? 'Open Access' : 'Paywalled'}
            </div>
            
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          {/* Abstract */}
          {paper.abstract && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">
                Abstract
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {paper.abstract}
              </p>
            </div>
          )}
          
          {/* Keywords */}
          {paper.keywords.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">
                Keywords
              </h4>
              <div className="flex flex-wrap gap-1">
                {paper.keywords.map((kw, i) => (
                  <span 
                    key={i}
                    className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Sources Found In */}
          {paper.sourcesFoundIn.length > 1 && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">
                Verified In
              </h4>
              <div className="flex flex-wrap gap-1">
                {paper.sourcesFoundIn.map((src, i) => (
                  <span 
                    key={i}
                    className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Reliability Details */}
          <div className="mt-3">
            <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">
              Reliability Breakdown
            </h4>
            <ReliabilityBadge reliability={paper.reliability} showDetails />
          </div>
          
          {/* Links */}
          <div className="mt-4 flex flex-wrap gap-2">
            {paper.urls.doi && (
              <a
                href={paper.urls.doi}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
              >
                <ExternalLink className="w-3 h-3" />
                DOI
              </a>
            )}
            
            {paper.pdfUrl && (
              <a
                href={paper.pdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700"
              >
                <FileText className="w-3 h-3" />
                PDF
              </a>
            )}
            
            {paper.urls.scihub && (
              <a
                href={paper.urls.scihub}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-orange-600 text-white text-xs rounded hover:bg-orange-700"
              >
                <ExternalLink className="w-3 h-3" />
                Sci-Hub
              </a>
            )}
            
            {paper.urls.pubmed && (
              <a
                href={paper.urls.pubmed}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-600 text-white text-xs rounded hover:bg-gray-700"
              >
                <ExternalLink className="w-3 h-3" />
                PubMed
              </a>
            )}
            
            {paper.urls.arxiv && (
              <a
                href={paper.urls.arxiv}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white text-xs rounded hover:bg-red-700"
              >
                <ExternalLink className="w-3 h-3" />
                arXiv
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PaperCard;
