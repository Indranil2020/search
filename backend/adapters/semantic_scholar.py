"""
Semantic Scholar Adapter

200M+ papers with citation data.
Free: 100 requests per 5 minutes.
"""

from typing import List, Optional, Dict

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int


class SemanticScholarAdapter(BaseAdapter):
    """Semantic Scholar adapter."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    FIELDS = ",".join([
        "paperId", "title", "abstract", "year", "citationCount",
        "authors", "journal", "venue", "publicationVenue",
        "externalIds", "openAccessPdf", "fieldsOfStudy",
        "publicationTypes", "referenceCount", "isOpenAccess"
    ])
    
    def __init__(self, api_key: Optional[str] = None):
        rate = 1.0 if api_key else 0.33  # 100 per 5 min
        config = AdapterConfig(
            name="Semantic Scholar",
            rate_limit=rate,
            timeout=30,
            api_key=api_key
        )
        super().__init__(config)
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search Semantic Scholar."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        papers = []
        offset = 0
        limit = min(100, max_results)
        
        while len(papers) < max_results:
            batch = self._search_batch(query, limit, offset)
            if batch.is_err:
                if papers:
                    return Ok(papers)
                return batch
            
            results = batch.unwrap()
            if not results:
                break
            
            papers.extend(results)
            offset += limit
            
            if len(results) < limit:
                break
        
        return Ok(papers[:max_results])
    
    def _search_batch(self, query: str, limit: int, offset: int) -> Result[List[Paper], str]:
        """Search batch."""
        
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": str(limit),
            "offset": str(offset),
            "fields": self.FIELDS
        }
        
        headers = {}
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        
        response = self.client.get(url, headers=headers, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        results = safe_get(data, "data", [])
        
        papers = []
        for item in results:
            paper = self._parse_paper(item)
            if paper:
                papers.append(paper)
        
        return Ok(papers)
    
    def _parse_paper(self, data: Dict) -> Optional[Paper]:
        """Parse paper from API response."""
        
        paper_id = safe_get(data, "paperId")
        if not paper_id:
            return None
        
        title = safe_get(data, "title", "Unknown")
        
        # Authors
        authors = []
        for author in safe_get(data, "authors", []):
            name = safe_get(author, "name")
            if name:
                authors.append(Author(name=name))
        
        # Year
        year = safe_int(safe_get(data, "year"))
        
        # Journal
        journal = None
        venue = safe_get(data, "venue")
        pub_venue = safe_get(data, "publicationVenue")
        if pub_venue:
            journal = safe_get(pub_venue, "name")
        elif venue:
            journal = venue
        
        # External IDs
        ext_ids = safe_get(data, "externalIds", {})
        doi = safe_get(ext_ids, "DOI")
        pmid = safe_get(ext_ids, "PubMed")
        arxiv_id = safe_get(ext_ids, "ArXiv")
        
        # Metrics
        citation_count = safe_int(safe_get(data, "citationCount", 0))
        reference_count = safe_int(safe_get(data, "referenceCount", 0))
        
        # Access
        is_oa = safe_get(data, "isOpenAccess", False)
        oa_pdf = safe_get(data, "openAccessPdf", {})
        pdf_url = safe_get(oa_pdf, "url") if oa_pdf else None
        
        # Source type
        pub_types = safe_get(data, "publicationTypes", [])
        source_type = SourceType.PEER_REVIEWED
        if "Preprint" in pub_types or arxiv_id:
            source_type = SourceType.PREPRINT
        elif "Conference" in pub_types:
            source_type = SourceType.CONFERENCE
        
        # Keywords
        keywords = safe_get(data, "fieldsOfStudy", [])
        
        paper = Paper(
            id=f"s2_{paper_id}",
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            doi=doi,
            pmid=pmid,
            arxiv_id=arxiv_id,
            abstract=safe_get(data, "abstract"),
            keywords=keywords[:10],
            citation_count=citation_count,
            reference_count=reference_count,
            source="Semantic Scholar",
            source_type=source_type,
            sources_found_in=["Semantic Scholar"],
            access_type=AccessType.OPEN if is_oa else AccessType.PAYWALLED,
            pdf_url=pdf_url
        )
        
        # URLs
        paper.urls = {
            "semanticscholar": f"https://www.semanticscholar.org/paper/{paper_id}"
        }
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
            paper.urls["scihub"] = f"https://sci-hub.se/{doi}"
        if arxiv_id:
            paper.urls["arxiv"] = f"https://arxiv.org/abs/{arxiv_id}"
            paper.urls["arxiv_pdf"] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        if pdf_url:
            paper.urls["pdf"] = pdf_url
        
        # Reliability
        paper.reliability = calculate_reliability(
            paper,
            is_peer_reviewed=(source_type == SourceType.PEER_REVIEWED),
            journal_name=journal,
            citation_count=citation_count,
            sources_found=1,
            year=year
        )
        
        return paper
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by ID."""
        
        if not paper_id:
            return Err("Empty ID")
        
        if paper_id.startswith("s2_"):
            s2_id = paper_id.replace("s2_", "")
        elif paper_id.startswith("10."):
            s2_id = paper_id
        else:
            s2_id = paper_id
        
        url = f"{self.BASE_URL}/paper/{s2_id}"
        params = {"fields": self.FIELDS}
        
        headers = {}
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        
        response = self.client.get(url, headers=headers, params=params)
        if response.is_err:
            return Ok(None)
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        return Ok(self._parse_paper(data))
    
    def get_citations(self, paper: Paper) -> Result[List[Paper], str]:
        """Get citing papers."""
        
        s2_id = None
        if paper.id.startswith("s2_"):
            s2_id = paper.id.replace("s2_", "")
        elif paper.doi:
            s2_id = paper.doi
        
        if not s2_id:
            return Ok([])
        
        url = f"{self.BASE_URL}/paper/{s2_id}/citations"
        params = {"fields": self.FIELDS, "limit": "100"}
        
        headers = {}
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        
        response = self.client.get(url, headers=headers, params=params)
        if response.is_err:
            return Err(f"Failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        
        papers = []
        for item in safe_get(data, "data", []):
            citing = safe_get(item, "citingPaper", {})
            p = self._parse_paper(citing)
            if p:
                papers.append(p)
        
        return Ok(papers)
    
    def get_references(self, paper: Paper) -> Result[List[Paper], str]:
        """Get referenced papers."""
        
        s2_id = None
        if paper.id.startswith("s2_"):
            s2_id = paper.id.replace("s2_", "")
        elif paper.doi:
            s2_id = paper.doi
        
        if not s2_id:
            return Ok([])
        
        url = f"{self.BASE_URL}/paper/{s2_id}/references"
        params = {"fields": self.FIELDS, "limit": "100"}
        
        headers = {}
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        
        response = self.client.get(url, headers=headers, params=params)
        if response.is_err:
            return Err(f"Failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        
        papers = []
        for item in safe_get(data, "data", []):
            cited = safe_get(item, "citedPaper", {})
            p = self._parse_paper(cited)
            if p:
                papers.append(p)
        
        return Ok(papers)
