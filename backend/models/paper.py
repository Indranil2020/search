"""
Paper Model with Reliability Scoring

Reliability is color-coded:
- GREEN (0.8-1.0): High reliability - peer-reviewed, high citations, verified
- YELLOW (0.5-0.79): Moderate - preprints, newer papers, single source
- RED (0.0-0.49): Lower reliability - unverified, retracted, contradicted
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ReliabilityLevel(Enum):
    """Reliability level with color."""
    HIGH = "green"      # 0.8 - 1.0
    MEDIUM = "yellow"   # 0.5 - 0.79
    LOW = "red"         # 0.0 - 0.49


class AccessType(Enum):
    """Paper access type."""
    OPEN = "open"
    PAYWALLED = "paywalled"
    UNKNOWN = "unknown"


class SourceType(Enum):
    """Source document type."""
    PEER_REVIEWED = "peer_reviewed"
    PREPRINT = "preprint"
    CONFERENCE = "conference"
    THESIS = "thesis"
    BOOK_CHAPTER = "book_chapter"
    GREY_LITERATURE = "grey_literature"
    UNKNOWN = "unknown"


@dataclass
class Author:
    """Author information."""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "affiliation": self.affiliation,
            "orcid": self.orcid
        }


@dataclass
class ReliabilityScore:
    """
    Reliability assessment with component scores.
    
    Components (total = 1.0):
    - peer_review: 0.0-0.30 (is it peer reviewed?)
    - journal: 0.0-0.20 (journal reputation)
    - citations: 0.0-0.20 (citation impact)
    - verification: 0.0-0.20 (multi-source verification)
    - recency: 0.0-0.10 (publication recency)
    """
    peer_review: float = 0.0
    journal: float = 0.0
    citations: float = 0.0
    verification: float = 0.0
    recency: float = 0.0
    is_retracted: bool = False
    contradictions: List[str] = field(default_factory=list)
    
    @property
    def total(self) -> float:
        """Calculate total score."""
        if self.is_retracted:
            return 0.0
        
        base = self.peer_review + self.journal + self.citations + self.verification + self.recency
        
        # Penalty for contradictions
        penalty = len(self.contradictions) * 0.05
        
        return max(0.0, min(1.0, base - penalty))
    
    @property
    def level(self) -> ReliabilityLevel:
        """Get reliability level."""
        score = self.total
        if score >= 0.8:
            return ReliabilityLevel.HIGH
        if score >= 0.5:
            return ReliabilityLevel.MEDIUM
        return ReliabilityLevel.LOW
    
    @property
    def color(self) -> str:
        """Get color code."""
        return self.level.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.total, 3),
            "color": self.color,
            "level": self.level.name.lower(),
            "components": {
                "peerReview": round(self.peer_review, 3),
                "journal": round(self.journal, 3),
                "citations": round(self.citations, 3),
                "verification": round(self.verification, 3),
                "recency": round(self.recency, 3)
            },
            "isRetracted": self.is_retracted,
            "contradictions": self.contradictions
        }


@dataclass
class Paper:
    """Complete paper representation."""
    
    # Core
    id: str
    title: str
    
    # Authors
    authors: List[Author] = field(default_factory=list)
    
    # Publication
    year: Optional[int] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    
    # Identifiers
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    arxiv_id: Optional[str] = None
    
    # Content
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    # Metrics
    citation_count: int = 0
    reference_count: int = 0
    
    # Access
    access_type: AccessType = AccessType.UNKNOWN
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    
    # Source tracking
    source: str = ""
    source_type: SourceType = SourceType.UNKNOWN
    sources_found_in: List[str] = field(default_factory=list)
    
    # Reliability
    reliability: ReliabilityScore = field(default_factory=ReliabilityScore)
    
    # URLs
    urls: Dict[str, str] = field(default_factory=dict)
    
    # Ranking (set during search)
    relevance_score: float = 0.0
    
    @property
    def author_names(self) -> List[str]:
        return [a.name for a in self.authors]
    
    @property
    def author_string(self) -> str:
        names = self.author_names
        if len(names) == 0:
            return "Unknown"
        if len(names) <= 3:
            return ", ".join(names)
        return f"{', '.join(names[:3])} et al."
    
    @property
    def reliability_color(self) -> str:
        return self.reliability.color
    
    @property
    def reliability_score(self) -> float:
        return self.reliability.total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": [a.to_dict() for a in self.authors],
            "authorString": self.author_string,
            "year": self.year,
            "journal": self.journal,
            "publisher": self.publisher,
            "doi": self.doi,
            "pmid": self.pmid,
            "pmcid": self.pmcid,
            "arxivId": self.arxiv_id,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "citationCount": self.citation_count,
            "referenceCount": self.reference_count,
            "accessType": self.access_type.value,
            "pdfUrl": self.pdf_url,
            "source": self.source,
            "sourceType": self.source_type.value,
            "sourcesFoundIn": self.sources_found_in,
            "reliability": self.reliability.to_dict(),
            "urls": self.urls,
            "relevanceScore": round(self.relevance_score, 3)
        }


# High impact journals for reliability scoring
HIGH_IMPACT_JOURNALS = frozenset({
    "nature", "science", "cell", "the lancet", 
    "new england journal of medicine", "jama", "bmj",
    "nature medicine", "nature genetics", "nature biotechnology",
    "nature communications", "proceedings of the national academy of sciences",
    "physical review letters", "journal of the american chemical society",
    "angewandte chemie", "chemical reviews", "chemical society reviews",
    "neuron", "immunity", "molecular cell"
})

REPUTABLE_PUBLISHERS = frozenset({
    "nature publishing group", "springer", "elsevier", "wiley",
    "cell press", "american chemical society", "royal society of chemistry",
    "ieee", "american physical society", "oxford university press",
    "cambridge university press", "plos", "frontiers", "bmc"
})


def calculate_reliability(
    paper: Paper,
    is_peer_reviewed: bool = False,
    journal_name: Optional[str] = None,
    citation_count: int = 0,
    sources_found: int = 1,
    year: Optional[int] = None,
    is_retracted: bool = False
) -> ReliabilityScore:
    """Calculate reliability score for a paper."""
    
    score = ReliabilityScore()
    
    # Retraction check
    if is_retracted:
        score.is_retracted = True
        return score
    
    # Peer review (0.0 - 0.30)
    if is_peer_reviewed:
        score.peer_review = 0.30
    elif paper.source_type == SourceType.PREPRINT:
        score.peer_review = 0.10
    elif paper.source_type == SourceType.CONFERENCE:
        score.peer_review = 0.20
    else:
        score.peer_review = 0.05
    
    # Journal reputation (0.0 - 0.20)
    if journal_name:
        journal_lower = journal_name.lower()
        if any(j in journal_lower for j in HIGH_IMPACT_JOURNALS):
            score.journal = 0.20
        elif paper.publisher and paper.publisher.lower() in REPUTABLE_PUBLISHERS:
            score.journal = 0.15
        else:
            score.journal = 0.10
    
    # Citation impact (0.0 - 0.20)
    if citation_count >= 500:
        score.citations = 0.20
    elif citation_count >= 100:
        score.citations = 0.15
    elif citation_count >= 25:
        score.citations = 0.10
    elif citation_count >= 5:
        score.citations = 0.05
    elif citation_count >= 1:
        score.citations = 0.02
    
    # Multi-source verification (0.0 - 0.20)
    if sources_found >= 5:
        score.verification = 0.20
    elif sources_found >= 3:
        score.verification = 0.15
    elif sources_found >= 2:
        score.verification = 0.10
    else:
        score.verification = 0.05
    
    # Recency (0.0 - 0.10)
    current_year = datetime.now().year
    if year:
        age = current_year - year
        if age <= 2:
            score.recency = 0.10
        elif age <= 5:
            score.recency = 0.07
        elif age <= 10:
            score.recency = 0.04
        else:
            score.recency = 0.02
    
    return score
