# System Architecture

## Overview

The Scientific Literature Search System is designed with three core principles:
1. **Complete Coverage** - Nothing missed, search all available sources
2. **Reliability Tracking** - Color-coded authenticity indicators
3. **Paywall Handling** - Always provide access paths

## Architecture Diagram

```
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|   React Frontend  |<--->|   Flask API       |<--->|   Search          |
|   (TypeScript)    |     |   Server          |     |   Orchestrator    |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +--------+----------+
                                                             |
                                                             v
+--------------------------------------------------------------------+
|                        Source Adapters                              |
+--------------------------------------------------------------------+
|                                                                     |
|  +----------+  +----------+  +----------+  +----------+            |
|  |  PubMed  |  | Semantic |  |  arXiv   |  | OpenAlex |            |
|  |          |  | Scholar  |  |          |  |          |            |
|  +----------+  +----------+  +----------+  +----------+            |
|                                                                     |
|  +----------+  +----------+  +----------+  +----------+            |
|  | CrossRef |  |   CORE   |  |   BASE   |  | Europe   |            |
|  |          |  |          |  |          |  | PMC      |            |
|  +----------+  +----------+  +----------+  +----------+            |
|                                                                     |
|  +----------+                                                       |
|  |Unpaywall |  (for OA discovery)                                  |
|  +----------+                                                       |
|                                                                     |
+--------------------------------------------------------------------+
```

## Components

### Frontend (TypeScript/React)

- **App.tsx** - Main application component
- **PaperCard.tsx** - Paper display with reliability colors
- **ReliabilityBadge.tsx** - Color-coded reliability indicator
- **KnowledgeGraph.tsx** - D3-based citation network visualization
- **Timeline.tsx** - Chronological paper display

### Backend (Python)

#### Core Module
- **orchestrator.py** - Coordinates searches, deduplication, ranking
- Phases:
  1. Search all sources
  2. Citation expansion
  3. Deduplication
  4. Reliability calculation
  5. Ranking

#### Adapters
Each adapter implements:
- `search(query, max_results)` - Search for papers
- `get_by_id(paper_id)` - Get single paper
- `get_citations(paper)` - Get citing papers (if supported)
- `get_references(paper)` - Get references (if supported)

#### Models
- **Paper** - Complete paper representation with:
  - Core metadata (title, authors, year)
  - Identifiers (DOI, PMID, arXiv ID)
  - Metrics (citations, references)
  - Reliability scoring
  - Access information

#### Utils
- **result.py** - Result pattern for error handling (no exceptions)
- **http.py** - HTTP client with Result types
- **rate_limiter.py** - Token bucket rate limiting

## Reliability Scoring

Multi-factor scoring algorithm:

| Factor | Weight | Description |
|--------|--------|-------------|
| Peer Review | 0.30 | Is it peer-reviewed? |
| Journal | 0.20 | Journal reputation |
| Citations | 0.20 | Citation impact |
| Verification | 0.20 | Found in multiple sources |
| Recency | 0.10 | Publication age |

### Color Coding

- **Green (0.8-1.0)** - High reliability
  - Peer-reviewed in reputable journals
  - High citation count
  - Verified across multiple databases
  
- **Yellow (0.5-0.79)** - Moderate reliability
  - Preprints not yet peer-reviewed
  - Newer papers with few citations
  - Single source verification
  
- **Red (0.0-0.49)** - Lower reliability
  - Unverified sources
  - Retracted papers
  - Grey literature

## Data Flow

1. **Query Input** - User enters search term
2. **Parallel Search** - All adapters search simultaneously
3. **Aggregation** - Results collected from all sources
4. **Deduplication** - By DOI > PMID > arXiv ID > Title
5. **Reliability Calculation** - Score each paper
6. **Ranking** - Sort by relevance + reliability
7. **Response** - Return to frontend with streaming progress

## Error Handling

No exceptions in business logic. All functions return Result types:

```python
def search(query: str) -> Result[List[Paper], str]:
    if not query:
        return Err("Empty query")
    
    papers = fetch_papers(query)
    return Ok(papers)
```

Exception handling only at boundary layers (HTTP, JSON parsing).

## Rate Limiting

Token bucket algorithm per source:

| Source | Rate Limit |
|--------|------------|
| PubMed | 10/s with key, 3/s without |
| Semantic Scholar | 100/5min |
| arXiv | 1/s |
| OpenAlex | 10/s |
| CrossRef | 50/s |
| CORE | 10/s |
| BASE | 1/s |
| Europe PMC | 10/s |

## Scalability

- Horizontal scaling via multiple API instances
- Redis for caching (optional)
- PostgreSQL for persistence (optional)
- Async search for better throughput
