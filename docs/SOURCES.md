# Data Sources

Complete list of all data sources integrated into the search system.

## Currently Implemented

### Academic Databases

| Source | Coverage | API | Rate Limit | Key Required |
|--------|----------|-----|------------|--------------|
| **PubMed/MEDLINE** | 35M+ biomedical papers | NCBI E-utilities | 3/s (10/s with key) | Optional |
| **Semantic Scholar** | 200M+ papers | REST API | 100/5min | Optional |
| **OpenAlex** | 240M+ works | REST API | 10/s | No |
| **arXiv** | 2M+ preprints | Atom API | 1/s | No |
| **CrossRef** | 130M+ DOIs | REST API | 50/s | No |
| **CORE** | 200M+ OA papers | REST API | 10/s | No |
| **BASE** | 270M+ documents | REST API | 1/s | No |
| **Europe PMC** | 40M+ life science | REST API | 10/s | No |

### Utility Services

| Source | Purpose | API | Key Required |
|--------|---------|-----|--------------|
| **Unpaywall** | Find OA versions | REST API | No (email) |

## Planned Sources

### Citation Databases
- Web of Science (institutional)
- Scopus (institutional)
- Dimensions
- OpenCitations

### Publishers
- Springer Nature
- Elsevier/ScienceDirect
- Wiley
- IEEE Xplore
- ACS Publications
- Nature
- Science/AAAS
- PLOS
- Frontiers
- BMC

### Preprint Servers
- bioRxiv
- medRxiv
- ChemRxiv
- SSRN
- OSF Preprints

### Specialized
- ClinicalTrials.gov
- Cochrane Library
- JSTOR
- ProQuest
- Google Scholar (via SerpAPI)

## Source Details

### PubMed (NCBI)

The primary source for biomedical literature.

**Endpoint:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`

**Features:**
- MeSH term indexing
- Abstract text
- Publication type classification
- PubMed Central links

**Best for:** Medicine, biology, health sciences

### Semantic Scholar

AI-powered academic search with citation analysis.

**Endpoint:** `https://api.semanticscholar.org/graph/v1`

**Features:**
- Citation counts
- Influence scores
- Open access PDF detection
- Fields of study classification

**Best for:** Computer science, AI, broad coverage

### OpenAlex

Fully open catalog of scholarly works.

**Endpoint:** `https://api.openalex.org`

**Features:**
- Comprehensive metadata
- Concept tagging
- Author disambiguation
- Institution data

**Best for:** Broad coverage, open data

### arXiv

Open access preprint server.

**Endpoint:** `http://export.arxiv.org/api/query`

**Features:**
- Full text PDF
- Category classification
- Version history
- Author comments

**Best for:** Physics, math, computer science, quantitative biology

### CrossRef

DOI registration and metadata.

**Endpoint:** `https://api.crossref.org`

**Features:**
- Publisher metadata
- Reference lists
- ORCID integration
- Funder information

**Best for:** DOI resolution, publisher data

### CORE

World's largest collection of open access papers.

**Endpoint:** `https://api.core.ac.uk/v3`

**Features:**
- Full text access
- Repository metadata
- Data provider info

**Best for:** Open access content

### BASE

Bielefeld Academic Search Engine.

**Endpoint:** `https://api.base-search.net`

**Features:**
- Broad repository coverage
- Open access filtering
- Multiple languages

**Best for:** European content, repositories

### Europe PMC

European life sciences literature.

**Endpoint:** `https://www.ebi.ac.uk/europepmc/webservices/rest`

**Features:**
- Full text mining
- Citation data
- Grant information
- Data links

**Best for:** European biomedical research

## Getting API Keys

### PubMed (Recommended)

1. Go to https://www.ncbi.nlm.nih.gov/account/
2. Create account or sign in
3. Go to Settings > API Key Management
4. Generate new key

### Semantic Scholar (Optional)

1. Go to https://www.semanticscholar.org/product/api
2. Sign up for API access
3. Copy key from dashboard

### OpenAlex (No key needed)

Uses email-based polite pool. Just set your email in configuration.

### CrossRef (No key needed)

Uses email-based polite pool. Include email in requests for higher rate limits.

## Coverage Analysis

Based on typical searches:

| Field | Primary Sources | Secondary Sources |
|-------|-----------------|-------------------|
| Medicine | PubMed, Europe PMC | Semantic Scholar, OpenAlex |
| Biology | PubMed, bioRxiv | CORE, OpenAlex |
| Physics | arXiv | Semantic Scholar, OpenAlex |
| Computer Science | arXiv, Semantic Scholar | OpenAlex, CORE |
| Chemistry | CrossRef | OpenAlex, ACS |
| Social Sciences | SSRN | OpenAlex, CrossRef |

## Data Quality

Sources are ranked by reliability:

1. **High reliability:** PubMed, CrossRef, Publisher APIs
2. **Medium reliability:** OpenAlex, Semantic Scholar, CORE
3. **Lower reliability:** General web searches, grey literature

The system aggregates from multiple sources to maximize both coverage and reliability.
