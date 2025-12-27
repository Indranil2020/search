"""
Search Orchestrator

Coordinates searches across all sources.
Deduplicates, calculates reliability, ranks papers.
Goal: Nothing left behind - complete coverage.
"""

from typing import List, Dict, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
import hashlib

from backend.models.paper import (
    Paper, AccessType, SourceType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err
from backend.adapters.base import BaseAdapter
from backend.adapters.pubmed import PubMedAdapter
from backend.adapters.semantic_scholar import SemanticScholarAdapter
from backend.adapters.arxiv import ArXivAdapter
from backend.adapters.openalex import OpenAlexAdapter
from backend.adapters.crossref import CrossRefAdapter
from backend.adapters.core_ac import COREAdapter
from backend.adapters.base_search import BASEAdapter
from backend.adapters.europe_pmc import EuropePMCAdapter
from backend.adapters.unpaywall import UnpaywallAdapter


@dataclass
class SearchConfig:
    """Search configuration."""
    max_per_source: int = 100
    expand_citations: bool = True
    citation_depth: int = 1
    include_preprints: bool = True
    min_reliability: float = 0.0
    year_start: Optional[int] = None
    year_end: Optional[int] = None


@dataclass
class ProgressUpdate:
    """Progress update for UI."""
    phase: str
    source: str
    status: str  # running, complete, error
    count: int = 0
    message: str = ""


@dataclass
class SearchResult:
    """Complete search result."""
    query: str
    papers: List[Paper] = field(default_factory=list)
    total_found: int = 0
    sources_searched: List[str] = field(default_factory=list)
    duplicates_removed: int = 0
    search_time_seconds: float = 0.0
    
    # Reliability breakdown
    high_reliability: int = 0
    medium_reliability: int = 0
    low_reliability: int = 0
    
    # Access breakdown
    open_access: int = 0
    paywalled: int = 0
    
    # Timeline
    earliest_year: Optional[int] = None
    latest_year: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "papers": [p.to_dict() for p in self.papers],
            "totalFound": self.total_found,
            "sourcesSearched": self.sources_searched,
            "duplicatesRemoved": self.duplicates_removed,
            "searchTimeSeconds": round(self.search_time_seconds, 2),
            "reliability": {
                "high": self.high_reliability,
                "medium": self.medium_reliability,
                "low": self.low_reliability
            },
            "access": {
                "open": self.open_access,
                "paywalled": self.paywalled
            },
            "timeline": {
                "earliest": self.earliest_year,
                "latest": self.latest_year
            }
        }


class SearchOrchestrator:
    """
    Main search orchestrator.
    
    Searches all sources, deduplicates, calculates reliability, ranks results.
    """
    
    def __init__(
        self,
        pubmed_key: Optional[str] = None,
        semantic_scholar_key: Optional[str] = None,
        email: str = "user@example.com"
    ):
        self.adapters: Dict[str, BaseAdapter] = {
            # Priority 1: Major academic databases
            "pubmed": PubMedAdapter(api_key=pubmed_key, email=email),
            "semantic_scholar": SemanticScholarAdapter(api_key=semantic_scholar_key),
            "openalex": OpenAlexAdapter(email=email),
            
            # Priority 2: Preprint servers
            "arxiv": ArXivAdapter(),
            
            # Priority 3: DOI/metadata databases
            "crossref": CrossRefAdapter(email=email),
            
            # Priority 4: Open access repositories
            "core": COREAdapter(),
            "base": BASEAdapter(),
            "europe_pmc": EuropePMCAdapter()
        }
        self.unpaywall = UnpaywallAdapter(email=email)
        self.progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    
    def set_progress_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """Set progress callback."""
        self.progress_callback = callback
    
    def _notify(self, phase: str, source: str, status: str, count: int = 0, message: str = "") -> None:
        """Send progress notification."""
        if self.progress_callback:
            self.progress_callback(ProgressUpdate(phase, source, status, count, message))
    
    def search(self, query: str, config: Optional[SearchConfig] = None) -> Result[SearchResult, str]:
        """Execute comprehensive search."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        config = config or SearchConfig()
        start_time = datetime.now()
        
        all_papers: List[Paper] = []
        sources_searched: List[str] = []
        
        # Phase 1: Search all sources
        self._notify("Search", "", "running", message="Searching all databases")
        
        for name, adapter in self.adapters.items():
            self._notify("Search", adapter.name, "running")
            
            result = adapter.search(query, config.max_per_source)
            
            if result.is_ok:
                papers = result.unwrap()
                all_papers.extend(papers)
                sources_searched.append(adapter.name)
                self._notify("Search", adapter.name, "complete", count=len(papers))
            else:
                self._notify("Search", adapter.name, "error", message=result.error)
        
        # Phase 2: Citation expansion
        if config.expand_citations and all_papers:
            self._notify("Citations", "", "running", message="Expanding citation network")
            
            top_papers = sorted(
                [p for p in all_papers if p.citation_count > 0],
                key=lambda p: p.citation_count,
                reverse=True
            )[:20]
            
            citation_papers = []
            ss_adapter = self.adapters.get("semantic_scholar")
            
            if ss_adapter:
                for paper in top_papers:
                    # Get citing papers
                    cites = ss_adapter.get_citations(paper)
                    if cites.is_ok:
                        citation_papers.extend(cites.unwrap()[:5])
                    
                    # Get references
                    refs = ss_adapter.get_references(paper)
                    if refs.is_ok:
                        citation_papers.extend(refs.unwrap()[:5])
            
            all_papers.extend(citation_papers)
            self._notify("Citations", "", "complete", count=len(citation_papers))
        
        # Phase 3: Deduplication
        self._notify("Process", "", "running", message="Deduplicating")
        
        original_count = len(all_papers)
        unique_papers = self._deduplicate(all_papers)
        duplicates_removed = original_count - len(unique_papers)
        
        self._notify("Process", "Dedup", "complete", count=duplicates_removed)
        
        # Phase 4: Update reliability
        self._notify("Process", "", "running", message="Calculating reliability")
        
        unique_papers = self._update_reliability(unique_papers)
        
        # Phase 5: Rank
        self._notify("Process", "", "running", message="Ranking results")
        
        ranked_papers = self._rank_papers(unique_papers, query)
        
        # Apply filters
        if config.min_reliability > 0:
            ranked_papers = [p for p in ranked_papers if p.reliability_score >= config.min_reliability]
        
        if config.year_start:
            ranked_papers = [p for p in ranked_papers if p.year and p.year >= config.year_start]
        
        if config.year_end:
            ranked_papers = [p for p in ranked_papers if p.year and p.year <= config.year_end]
        
        if not config.include_preprints:
            ranked_papers = [p for p in ranked_papers if p.source_type != SourceType.PREPRINT]
        
        # Build result
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = SearchResult(
            query=query,
            papers=ranked_papers,
            total_found=len(ranked_papers),
            sources_searched=sources_searched,
            duplicates_removed=duplicates_removed,
            search_time_seconds=duration
        )
        
        # Stats
        result.high_reliability = sum(1 for p in ranked_papers if p.reliability_score >= 0.8)
        result.medium_reliability = sum(1 for p in ranked_papers if 0.5 <= p.reliability_score < 0.8)
        result.low_reliability = sum(1 for p in ranked_papers if p.reliability_score < 0.5)
        
        result.open_access = sum(1 for p in ranked_papers if p.access_type == AccessType.OPEN)
        result.paywalled = sum(1 for p in ranked_papers if p.access_type == AccessType.PAYWALLED)
        
        years = [p.year for p in ranked_papers if p.year]
        if years:
            result.earliest_year = min(years)
            result.latest_year = max(years)
        
        self._notify("Complete", "", "complete", count=len(ranked_papers))
        
        return Ok(result)
    
    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """Deduplicate papers."""
        
        by_doi: Dict[str, Paper] = {}
        by_pmid: Dict[str, Paper] = {}
        by_arxiv: Dict[str, Paper] = {}
        by_title: Dict[str, Paper] = {}
        
        unique: List[Paper] = []
        
        for paper in papers:
            merged = False
            
            # Check DOI
            if paper.doi:
                key = paper.doi.lower().strip()
                if key in by_doi:
                    self._merge(by_doi[key], paper)
                    merged = True
                else:
                    by_doi[key] = paper
            
            # Check PMID
            if not merged and paper.pmid:
                key = paper.pmid.strip()
                if key in by_pmid:
                    self._merge(by_pmid[key], paper)
                    merged = True
                else:
                    by_pmid[key] = paper
            
            # Check arXiv
            if not merged and paper.arxiv_id:
                key = paper.arxiv_id.lower().strip()
                if key in by_arxiv:
                    self._merge(by_arxiv[key], paper)
                    merged = True
                else:
                    by_arxiv[key] = paper
            
            # Check title
            if not merged:
                key = self._normalize_title(paper.title)
                if key in by_title:
                    self._merge(by_title[key], paper)
                    merged = True
                else:
                    by_title[key] = paper
            
            if not merged:
                unique.append(paper)
        
        return unique
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        if not title:
            return ""
        
        title = title.lower()
        title = re.sub(r'[^\w\s]', '', title)
        title = ' '.join(title.split())
        
        stopwords = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'for', 'to', 'with'}
        words = [w for w in title.split() if w not in stopwords]
        
        return ' '.join(words)
    
    def _merge(self, target: Paper, source: Paper) -> None:
        """Merge source into target."""
        
        for src in source.sources_found_in:
            if src not in target.sources_found_in:
                target.sources_found_in.append(src)
        
        if source.citation_count > target.citation_count:
            target.citation_count = source.citation_count
        
        if not target.doi and source.doi:
            target.doi = source.doi
        if not target.pmid and source.pmid:
            target.pmid = source.pmid
        if not target.arxiv_id and source.arxiv_id:
            target.arxiv_id = source.arxiv_id
        if not target.abstract and source.abstract:
            target.abstract = source.abstract
        
        for kw in source.keywords:
            if kw not in target.keywords:
                target.keywords.append(kw)
        
        target.urls.update(source.urls)
        
        if source.access_type == AccessType.OPEN:
            target.access_type = AccessType.OPEN
            if source.pdf_url:
                target.pdf_url = source.pdf_url
    
    def _update_reliability(self, papers: List[Paper]) -> List[Paper]:
        """Update reliability with cross-source verification."""
        
        for paper in papers:
            sources_count = len(paper.sources_found_in)
            
            paper.reliability = calculate_reliability(
                paper,
                is_peer_reviewed=(paper.source_type == SourceType.PEER_REVIEWED),
                journal_name=paper.journal,
                citation_count=paper.citation_count,
                sources_found=sources_count,
                year=paper.year
            )
        
        return papers
    
    def _rank_papers(self, papers: List[Paper], query: str) -> List[Paper]:
        """Rank papers by relevance and reliability."""
        
        query_terms = set(self._normalize_title(query).split())
        
        for paper in papers:
            score = 0.0
            
            # Title match (0-30)
            if paper.title:
                title_terms = set(self._normalize_title(paper.title).split())
                overlap = len(query_terms & title_terms)
                score += (overlap / max(len(query_terms), 1)) * 30
            
            # Abstract match (0-15)
            if paper.abstract:
                abstract_terms = set(self._normalize_title(paper.abstract).split())
                overlap = len(query_terms & abstract_terms)
                score += min(15, overlap * 3)
            
            # Citations (0-20)
            if paper.citation_count > 0:
                import math
                score += min(20, math.log10(paper.citation_count + 1) * 5)
            
            # Reliability (0-20)
            score += paper.reliability_score * 20
            
            # Recency (0-10)
            current_year = datetime.now().year
            if paper.year:
                age = current_year - paper.year
                if age <= 2:
                    score += 10
                elif age <= 5:
                    score += 7
                elif age <= 10:
                    score += 4
                else:
                    score += 1
            
            # Open access (0-5)
            if paper.access_type == AccessType.OPEN:
                score += 5
            
            paper.relevance_score = score
        
        papers.sort(key=lambda p: p.relevance_score, reverse=True)
        return papers


def create_orchestrator(
    pubmed_key: Optional[str] = None,
    semantic_scholar_key: Optional[str] = None,
    email: str = "user@example.com"
) -> SearchOrchestrator:
    """Create configured orchestrator."""
    return SearchOrchestrator(pubmed_key, semantic_scholar_key, email)
