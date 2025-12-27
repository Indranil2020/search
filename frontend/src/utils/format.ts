/**
 * Formatting Utilities
 */

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Format date for display
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString();
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Format author list
 */
export function formatAuthors(authors: string[], maxShow: number = 3): string {
  if (authors.length === 0) return 'Unknown';
  if (authors.length <= maxShow) return authors.join(', ');
  return `${authors.slice(0, maxShow).join(', ')} et al.`;
}

/**
 * Format citation count
 */
export function formatCitations(count: number): string {
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`;
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
}

/**
 * Generate DOI URL
 */
export function doiUrl(doi: string): string {
  return `https://doi.org/${doi}`;
}

/**
 * Generate Sci-Hub URL
 */
export function scihubUrl(doi: string): string {
  return `https://sci-hub.se/${doi}`;
}

/**
 * Generate PubMed URL
 */
export function pubmedUrl(pmid: string): string {
  return `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`;
}

/**
 * Generate arXiv URL
 */
export function arxivUrl(arxivId: string): string {
  return `https://arxiv.org/abs/${arxivId}`;
}
