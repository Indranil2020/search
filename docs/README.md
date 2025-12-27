# Scientific Literature Search System

A comprehensive, open-source scientific literature discovery engine designed to leave nothing behind. This system searches 70+ academic databases, tracks reliability with color-coded indicators, builds knowledge graphs, and handles paywalled content intelligently.

## Goals

- **Complete Coverage**: Search every available source, miss nothing
- **Reliability Tracking**: Color-coded authenticity indicators (green/yellow/red)
- **Knowledge Graph**: Visualize citation networks and paper relationships
- **Timeline View**: See research evolution from earliest to latest
- **Paywall Handling**: Always provide access paths (abstracts, Sci-Hub, open access)
- **Minimalist Interface**: Clean, efficient, focused on results

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/search-system.git
cd search-system

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Configure environment
cp ../.env.example ../.env
# Edit .env with your API keys
```

### Running

```bash
# Start backend (from backend/)
python app.py

# Start frontend (from frontend/)
npm run dev
```

Access the application at http://localhost:5173

## API Keys

The system works with FREE tiers of all services. Optional API keys for higher rate limits:

| Service | Required | Free Tier | Get Key |
|---------|----------|-----------|---------|
| NCBI/PubMed | No | 3 req/s | https://www.ncbi.nlm.nih.gov/account/ |
| Semantic Scholar | No | 100/5min | https://www.semanticscholar.org/product/api |
| OpenAlex | No | 10 req/s | Email-based polite pool |
| CrossRef | No | 50 req/s | Polite pool with email |

## Features

### Reliability Color Coding

Papers are color-coded based on reliability assessment:

- **Green (0.8-1.0)**: High reliability - peer-reviewed, highly cited, verified
- **Yellow (0.5-0.79)**: Moderate - preprints, newer papers, single source
- **Red (0.0-0.49)**: Lower reliability - unverified, retracted, contradicted

### Data Sources (70+)

See [SOURCES.md](./SOURCES.md) for complete list including:
- Academic databases (PubMed, Semantic Scholar, OpenAlex, etc.)
- Citation databases (OpenCitations, Dimensions)
- Publishers (Springer, Elsevier, Wiley, IEEE, etc.)
- Preprint servers (arXiv, bioRxiv, medRxiv, etc.)
- Open access repositories (CORE, BASE, DOAJ, etc.)

### Knowledge Graph

Interactive visualization showing:
- Citation relationships between papers
- Author collaboration networks  
- Topic clustering
- Research evolution paths

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## License

MIT License - see LICENSE file
