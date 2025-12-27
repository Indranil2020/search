"""
Source Adapters

All adapters for external data sources.
"""

from .base import BaseAdapter, AdapterConfig
from .pubmed import PubMedAdapter
from .semantic_scholar import SemanticScholarAdapter
from .arxiv import ArXivAdapter
from .openalex import OpenAlexAdapter
from .crossref import CrossRefAdapter
from .core_ac import COREAdapter
from .base_search import BASEAdapter
from .europe_pmc import EuropePMCAdapter
from .unpaywall import UnpaywallAdapter

__all__ = [
    "BaseAdapter",
    "AdapterConfig",
    "PubMedAdapter",
    "SemanticScholarAdapter",
    "ArXivAdapter",
    "OpenAlexAdapter",
    "CrossRefAdapter",
    "COREAdapter",
    "BASEAdapter",
    "EuropePMCAdapter",
    "UnpaywallAdapter"
]
