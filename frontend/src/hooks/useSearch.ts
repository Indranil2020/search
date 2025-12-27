/**
 * useSearch Hook
 * 
 * Custom hook for managing search state and API calls.
 */

import { useState, useCallback } from 'react';
import type { SearchResult, StreamEvent, ProgressUpdate } from '../types/paper';
import { searchWithProgress, SearchOptions } from '../utils/api';

interface UseSearchReturn {
  query: string;
  setQuery: (query: string) => void;
  isSearching: boolean;
  result: SearchResult | null;
  progress: ProgressUpdate[];
  error: string | null;
  search: () => Promise<void>;
  reset: () => void;
}

export function useSearch(defaultOptions: SearchOptions = {}): UseSearchReturn {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate[]>([]);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async () => {
    if (!query.trim() || isSearching) return;

    setIsSearching(true);
    setResult(null);
    setProgress([]);
    setError(null);

    const onProgress = (event: StreamEvent) => {
      if (event.type === 'progress') {
        setProgress(prev => [...prev.slice(-19), {
          type: 'progress',
          phase: event.phase,
          source: event.source,
          status: event.status,
          count: event.count,
          message: event.message
        }]);
      } else if (event.type === 'error') {
        setError(event.error);
      }
    };

    const searchResult = await searchWithProgress(
      query,
      {
        maxPerSource: defaultOptions.maxPerSource ?? 100,
        expandCitations: defaultOptions.expandCitations ?? true,
        includePreprints: defaultOptions.includePreprints ?? true,
        minReliability: defaultOptions.minReliability ?? 0,
        yearStart: defaultOptions.yearStart,
        yearEnd: defaultOptions.yearEnd
      },
      onProgress
    );

    if (searchResult) {
      setResult(searchResult);
    }

    setIsSearching(false);
  }, [query, isSearching, defaultOptions]);

  const reset = useCallback(() => {
    setQuery('');
    setResult(null);
    setProgress([]);
    setError(null);
  }, []);

  return {
    query,
    setQuery,
    isSearching,
    result,
    progress,
    error,
    search,
    reset
  };
}

export default useSearch;
