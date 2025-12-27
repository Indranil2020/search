# API Documentation

## Base URL

```
http://localhost:5000/api
```

## Endpoints

### Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "ok"
}
```

---

### Search Papers

```
POST /api/search
```

Search across all databases for papers matching the query.

**Request Body:**
```json
{
  "query": "CRISPR gene editing",
  "maxPerSource": 100,
  "expandCitations": true,
  "includePreprints": true,
  "minReliability": 0.0,
  "yearStart": 2015,
  "yearEnd": 2024
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| query | string | required | Search query |
| maxPerSource | int | 100 | Max papers per source |
| expandCitations | bool | true | Expand citation network |
| includePreprints | bool | true | Include preprints |
| minReliability | float | 0.0 | Minimum reliability score |
| yearStart | int | null | Filter by start year |
| yearEnd | int | null | Filter by end year |

**Response:**
```json
{
  "query": "CRISPR gene editing",
  "papers": [...],
  "totalFound": 523,
  "sourcesSearched": ["PubMed", "Semantic Scholar", "arXiv", ...],
  "duplicatesRemoved": 156,
  "searchTimeSeconds": 12.5,
  "reliability": {
    "high": 189,
    "medium": 234,
    "low": 100
  },
  "access": {
    "open": 312,
    "paywalled": 211
  },
  "timeline": {
    "earliest": 2012,
    "latest": 2024
  }
}
```

---

### Search with Streaming Progress

```
POST /api/search/stream
```

Same as `/api/search` but returns Server-Sent Events for real-time progress.

**Request Body:** Same as `/api/search`

**Response:** Server-Sent Events stream

**Event Types:**

Progress event:
```json
{
  "type": "progress",
  "phase": "Search",
  "source": "PubMed",
  "status": "running",
  "count": 0,
  "message": ""
}
```

Result event:
```json
{
  "type": "result",
  "data": { ... }
}
```

Error event:
```json
{
  "type": "error",
  "error": "Error message"
}
```

**Example JavaScript client:**
```javascript
const response = await fetch('/api/search/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'machine learning' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      console.log(event);
    }
  }
}
```

---

### Get Paper by ID

```
GET /api/paper/{paper_id}
```

Retrieve a single paper by its ID.

**Path Parameters:**
| Parameter | Description |
|-----------|-------------|
| paper_id | Paper ID (e.g., pubmed_12345, s2_abc123, arxiv_2301.00001) |

**Response:**
```json
{
  "id": "pubmed_12345678",
  "title": "Example Paper Title",
  "authors": [
    {
      "name": "John Smith",
      "affiliation": "MIT",
      "orcid": "0000-0001-2345-6789"
    }
  ],
  "authorString": "John Smith, Jane Doe et al.",
  "year": 2023,
  "journal": "Nature",
  "publisher": "Nature Publishing Group",
  "doi": "10.1038/example",
  "pmid": "12345678",
  "pmcid": "PMC1234567",
  "arxivId": null,
  "abstract": "This paper describes...",
  "keywords": ["genetics", "CRISPR", "gene editing"],
  "citationCount": 150,
  "referenceCount": 45,
  "accessType": "open",
  "pdfUrl": "https://...",
  "source": "PubMed",
  "sourceType": "peer_reviewed",
  "sourcesFoundIn": ["PubMed", "Semantic Scholar", "OpenAlex"],
  "reliability": {
    "score": 0.85,
    "color": "green",
    "level": "high",
    "components": {
      "peerReview": 0.30,
      "journal": 0.20,
      "citations": 0.15,
      "verification": 0.15,
      "recency": 0.05
    },
    "isRetracted": false,
    "contradictions": []
  },
  "urls": {
    "pubmed": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
    "doi": "https://doi.org/10.1038/example",
    "scihub": "https://sci-hub.se/10.1038/example",
    "pdf": "https://..."
  },
  "relevanceScore": 85.5
}
```

---

## Data Types

### Paper Object

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier |
| title | string | Paper title |
| authors | Author[] | List of authors |
| authorString | string | Formatted author string |
| year | int | Publication year |
| journal | string | Journal name |
| publisher | string | Publisher name |
| doi | string | DOI |
| pmid | string | PubMed ID |
| pmcid | string | PubMed Central ID |
| arxivId | string | arXiv ID |
| abstract | string | Abstract text |
| keywords | string[] | Keywords/MeSH terms |
| citationCount | int | Number of citations |
| referenceCount | int | Number of references |
| accessType | string | "open", "paywalled", "unknown" |
| pdfUrl | string | PDF URL if available |
| source | string | Primary source name |
| sourceType | string | Type of publication |
| sourcesFoundIn | string[] | All sources found in |
| reliability | Reliability | Reliability assessment |
| urls | object | Collection of URLs |
| relevanceScore | float | Search relevance score |

### Author Object

| Field | Type | Description |
|-------|------|-------------|
| name | string | Full name |
| affiliation | string | Institution |
| orcid | string | ORCID identifier |

### Reliability Object

| Field | Type | Description |
|-------|------|-------------|
| score | float | Total score (0.0-1.0) |
| color | string | "green", "yellow", "red" |
| level | string | "high", "medium", "low" |
| components | object | Component scores |
| isRetracted | bool | Retraction flag |
| contradictions | string[] | Contradiction notes |

### Source Type Values

- `peer_reviewed` - Peer-reviewed journal article
- `preprint` - Preprint (not peer-reviewed)
- `conference` - Conference paper
- `thesis` - Dissertation/thesis
- `book_chapter` - Book chapter
- `grey_literature` - Grey literature
- `unknown` - Unknown type

---

## Error Responses

```json
{
  "error": "Error message"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad request (missing/invalid parameters) |
| 404 | Paper not found |
| 500 | Internal server error |

---

## Rate Limiting

The API itself does not implement rate limiting. However, individual data sources have their own rate limits which are handled internally.

---

## CORS

CORS is enabled for all origins. For production, configure allowed origins in the server settings.
