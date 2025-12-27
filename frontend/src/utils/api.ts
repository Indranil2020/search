/**
 * API Client
 */

import type { SearchResult, StreamEvent, Paper } from '../types/paper';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface SearchOptions {
  maxPerSource?: number;
  expandCitations?: boolean;
  includePreprints?: boolean;
  minReliability?: number;
  yearStart?: number | null;
  yearEnd?: number | null;
}

/**
 * Search with streaming progress
 */
export async function searchWithProgress(
  query: string,
  options: SearchOptions,
  onProgress: (event: StreamEvent) => void
): Promise<SearchResult | null> {
  const response = await fetch(`${API_BASE}/api/search/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      maxPerSource: options.maxPerSource ?? 100,
      expandCitations: options.expandCitations ?? true,
      includePreprints: options.includePreprints ?? true,
      minReliability: options.minReliability ?? 0,
      yearStart: options.yearStart,
      yearEnd: options.yearEnd
    })
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let result: SearchResult | null = null;

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data) {
          const event = JSON.parse(data) as StreamEvent;
          onProgress(event);
          
          if (event.type === 'result') {
            result = event.data;
          }
        }
      }
    }
  }

  return result;
}

/**
 * Simple search without streaming
 */
export async function search(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const response = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      maxPerSource: options.maxPerSource ?? 100,
      expandCitations: options.expandCitations ?? true,
      includePreprints: options.includePreprints ?? true,
      minReliability: options.minReliability ?? 0,
      yearStart: options.yearStart,
      yearEnd: options.yearEnd
    })
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get paper by ID
 */
export async function getPaper(paperId: string): Promise<Paper | null> {
  const response = await fetch(`${API_BASE}/api/paper/${encodeURIComponent(paperId)}`);
  
  if (response.status === 404) {
    return null;
  }
  
  if (!response.ok) {
    throw new Error(`Failed to get paper: ${response.statusText}`);
  }

  return response.json();
}
