/**
 * Scientific Literature Search System
 * 
 * Minimalist interface with color-coded reliability indicators.
 */

import React, { useState, useCallback } from 'react';
import { Search, Loader2, Database, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import type { SearchResult, Paper, ProgressUpdate, StreamEvent } from './types/paper';
import { searchWithProgress } from './utils/api';
import { PaperCard } from './components/PaperCard';

interface Progress {
  phase: string;
  source: string;
  status: string;
  count: number;
  message: string;
}

const App: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [reliabilityFilter, setReliabilityFilter] = useState<'all' | 'green' | 'yellow' | 'red'>('all');
  const [accessFilter, setAccessFilter] = useState<'all' | 'open' | 'paywalled'>('all');

  const handleSearch = useCallback(async () => {
    if (!query.trim() || isSearching) return;

    setIsSearching(true);
    setResult(null);
    setProgress([]);
    setError(null);

    const onProgress = (event: StreamEvent) => {
      if (event.type === 'progress') {
        setProgress(prev => [...prev.slice(-9), {
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
        maxPerSource: 100,
        expandCitations: true,
        includePreprints: true
      },
      onProgress
    );

    if (searchResult) {
      setResult(searchResult);
    }

    setIsSearching(false);
  }, [query, isSearching]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Filter papers
  const filteredPapers = result?.papers.filter(paper => {
    if (reliabilityFilter !== 'all' && paper.reliability.color !== reliabilityFilter) {
      return false;
    }
    if (accessFilter !== 'all' && paper.accessType !== accessFilter) {
      return false;
    }
    return true;
  }) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Scientific Literature Search
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Comprehensive search across 70+ databases with reliability indicators
          </p>
        </div>
      </header>

      {/* Search */}
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter research topic..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              disabled={isSearching}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSearching ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search
              </>
            )}
          </button>
        </div>

        {/* Progress */}
        {isSearching && progress.length > 0 && (
          <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
            <div className="space-y-2">
              {progress.slice(-5).map((p, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  {p.status === 'running' && (
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  )}
                  {p.status === 'complete' && (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  )}
                  {p.status === 'error' && (
                    <AlertCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className="font-medium text-gray-700">{p.source || p.phase}</span>
                  {p.count > 0 && (
                    <span className="text-gray-500">{p.count} papers</span>
                  )}
                  {p.message && (
                    <span className="text-gray-400">{p.message}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-6">
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {result.totalFound}
                </div>
                <div className="text-sm text-gray-500">Papers Found</div>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-green-600">{result.reliability.high}</span>
                  <span className="text-lg font-bold text-yellow-600">{result.reliability.medium}</span>
                  <span className="text-lg font-bold text-red-600">{result.reliability.low}</span>
                </div>
                <div className="text-sm text-gray-500">By Reliability</div>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {result.access.open}
                </div>
                <div className="text-sm text-gray-500">Open Access</div>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="text-sm text-gray-900">
                  {result.timeline.earliest} - {result.timeline.latest}
                </div>
                <div className="text-sm text-gray-500">Timeline</div>
              </div>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Reliability:</span>
                <select
                  value={reliabilityFilter}
                  onChange={(e) => setReliabilityFilter(e.target.value as typeof reliabilityFilter)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="all">All</option>
                  <option value="green">High (Green)</option>
                  <option value="yellow">Moderate (Yellow)</option>
                  <option value="red">Lower (Red)</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Access:</span>
                <select
                  value={accessFilter}
                  onChange={(e) => setAccessFilter(e.target.value as typeof accessFilter)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="all">All</option>
                  <option value="open">Open Access</option>
                  <option value="paywalled">Paywalled</option>
                </select>
              </div>
              <div className="text-sm text-gray-500">
                Showing {filteredPapers.length} of {result.totalFound}
              </div>
            </div>

            {/* Reliability Legend */}
            <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-green-500" />
                Green = High Reliability
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-yellow-500" />
                Yellow = Moderate
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                Red = Lower
              </div>
            </div>

            {/* Paper List */}
            <div className="space-y-3">
              {filteredPapers.map((paper) => (
                <PaperCard key={paper.id} paper={paper} />
              ))}
            </div>

            {filteredPapers.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No papers match the current filters.
              </div>
            )}

            {/* Search Info */}
            <div className="mt-6 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                Searched: {result.sourcesSearched.join(', ')}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Clock className="w-4 h-4" />
                Completed in {result.searchTimeSeconds}s, removed {result.duplicatesRemoved} duplicates
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!result && !isSearching && (
          <div className="mt-12 text-center">
            <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">
              Comprehensive Literature Search
            </h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Search across PubMed, Semantic Scholar, arXiv, OpenAlex and more.
              Results are color-coded by reliability.
            </p>
            <div className="mt-6 flex justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-green-500" />
                High reliability
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-yellow-500" />
                Moderate
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                Lower
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
