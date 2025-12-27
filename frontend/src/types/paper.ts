/**
 * Paper Types
 * 
 * Reliability color coding:
 * - green (0.8-1.0): High reliability
 * - yellow (0.5-0.79): Moderate reliability  
 * - red (0.0-0.49): Lower reliability
 */

export type ReliabilityColor = 'green' | 'yellow' | 'red';
export type ReliabilityLevel = 'high' | 'medium' | 'low';
export type AccessType = 'open' | 'paywalled' | 'unknown';
export type SourceType = 'peer_reviewed' | 'preprint' | 'conference' | 'thesis' | 'book_chapter' | 'grey_literature' | 'unknown';

export interface Author {
  name: string;
  affiliation?: string;
  orcid?: string;
}

export interface ReliabilityScore {
  score: number;
  color: ReliabilityColor;
  level: ReliabilityLevel;
  components: {
    peerReview: number;
    journal: number;
    citations: number;
    verification: number;
    recency: number;
  };
  isRetracted: boolean;
  contradictions: string[];
}

export interface Paper {
  id: string;
  title: string;
  authors: Author[];
  authorString: string;
  year: number | null;
  journal: string | null;
  publisher: string | null;
  doi: string | null;
  pmid: string | null;
  pmcid: string | null;
  arxivId: string | null;
  abstract: string | null;
  keywords: string[];
  citationCount: number;
  referenceCount: number;
  accessType: AccessType;
  pdfUrl: string | null;
  source: string;
  sourceType: SourceType;
  sourcesFoundIn: string[];
  reliability: ReliabilityScore;
  urls: Record<string, string>;
  relevanceScore: number;
}

export interface SearchResult {
  query: string;
  papers: Paper[];
  totalFound: number;
  sourcesSearched: string[];
  duplicatesRemoved: number;
  searchTimeSeconds: number;
  reliability: {
    high: number;
    medium: number;
    low: number;
  };
  access: {
    open: number;
    paywalled: number;
  };
  timeline: {
    earliest: number | null;
    latest: number | null;
  };
}

export interface ProgressUpdate {
  type: 'progress';
  phase: string;
  source: string;
  status: 'running' | 'complete' | 'error';
  count: number;
  message: string;
}

export interface SearchResponse {
  type: 'result';
  data: SearchResult;
}

export interface ErrorResponse {
  type: 'error';
  error: string;
}

export type StreamEvent = ProgressUpdate | SearchResponse | ErrorResponse;
