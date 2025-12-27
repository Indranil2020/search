"""
CrossRef Adapter

130M+ DOIs from scholarly works.
Free: 50 requests/second in polite pool (with email).
"""

from typing import List, Optional, Dict

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int, safe_first


class CrossRefAdapter(BaseAdapter):
    """CrossRef DOI resolver and search adapter."""
    
    BASE_URL = "https://api.crossref.org"
    
    def __init__(self, email: str = "user@example.com"):
        config = AdapterConfig(
            name="CrossRef",
            rate_limit=50.0,  # Polite pool
            timeout=30
        )
        super().__init__(config)
        self.email = email
        self.client.user_agent = f"SearchSystem/1.0 (mailto:{email})"
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search CrossRef."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        papers = []
        offset = 0
        rows = min(100, max_results)
        
        while len(papers) < max_results:
            batch = self._search_batch(query, rows, offset)
            if batch.is_err:
                if papers:
                    return Ok(papers)
                return batch
            
            results = batch.unwrap()
            if not results:
                break
            
            papers.extend(results)
            offset += rows
            
            if len(results) < rows:
                break
        
        return Ok(papers[:max_results])
    
    def _search_batch(self, query: str, rows: int, offset: int) -> Result[List[Paper], str]:
        """Search batch."""
        
        url = f"{self.BASE_URL}/works"
        params = {
            "query": query,
            "rows": str(rows),
            "offset": str(offset),
            "select": "DOI,title,author,published,abstract,container-title,is-referenced-by-count,publisher,type,ISSN,link"
        }
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        items = safe_get(safe_get(data, "message", {}), "items", [])
        
        papers = []
        for item in items:
            paper = self._parse_work(item)
            if paper:
                papers.append(paper)
        
        return Ok(papers)
    
    def _parse_work(self, data: Dict) -> Optional[Paper]:
        """Parse CrossRef work."""
        
        doi = safe_get(data, "DOI")
        if not doi:
            return None
        
        # Title
        title_list = safe_get(data, "title", [])
        title = safe_first(title_list, "Unknown")
        
        # Authors
        authors = []
        for author in safe_get(data, "author", []):
            given = safe_get(author, "given", "")
            family = safe_get(author, "family", "")
            name = f"{given} {family}".strip()
            if name:
                orcid = safe_get(author, "ORCID")
                if orcid:
                    orcid = orcid.replace("http://orcid.org/", "").replace("https://orcid.org/", "")
                authors.append(Author(name=name, orcid=orcid))
        
        # Year
        year = None
        published = safe_get(data, "published")
        if published:
            date_parts = safe_get(published, "date-parts", [[]])
            if date_parts and date_parts[0]:
                year = safe_int(date_parts[0][0])
        
        # Journal
        container = safe_get(data, "container-title", [])
        journal = safe_first(container)
        
        # Publisher
        publisher = safe_get(data, "publisher")
        
        # Citations
        citation_count = safe_int(safe_get(data, "is-referenced-by-count", 0))
        
        # Abstract
        abstract = safe_get(data, "abstract")
        if abstract:
            # Remove JATS XML tags
            import re
            abstract = re.sub(r'<[^>]+>', '', abstract)
        
        # Type
        work_type = safe_get(data, "type", "")
        source_type = self._map_type(work_type)
        
        # Links
        pdf_url = None
        links = safe_get(data, "link", [])
        for link in links:
            if safe_get(link, "content-type") == "application/pdf":
                pdf_url = safe_get(link, "URL")
                break
        
        paper = Paper(
            id=f"crossref_{doi.replace('/', '_')}",
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            publisher=publisher,
            doi=doi,
            abstract=abstract,
            citation_count=citation_count,
            source="CrossRef",
            source_type=source_type,
            sources_found_in=["CrossRef"],
            access_type=AccessType.OPEN if pdf_url else AccessType.PAYWALLED,
            pdf_url=pdf_url
        )
        
        paper.urls = {
            "doi": f"https://doi.org/{doi}",
            "scihub": f"https://sci-hub.se/{doi}"
        }
        if pdf_url:
            paper.urls["pdf"] = pdf_url
        
        paper.reliability = calculate_reliability(
            paper,
            is_peer_reviewed=(source_type == SourceType.PEER_REVIEWED),
            journal_name=journal,
            citation_count=citation_count,
            sources_found=1,
            year=year
        )
        
        return paper
    
    def _map_type(self, work_type: str) -> SourceType:
        """Map CrossRef type to SourceType."""
        mapping = {
            "journal-article": SourceType.PEER_REVIEWED,
            "proceedings-article": SourceType.CONFERENCE,
            "book-chapter": SourceType.BOOK_CHAPTER,
            "dissertation": SourceType.THESIS,
            "posted-content": SourceType.PREPRINT
        }
        return mapping.get(work_type, SourceType.UNKNOWN)
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by DOI."""
        
        if not paper_id:
            return Err("Empty ID")
        
        # Extract DOI
        if paper_id.startswith("crossref_"):
            doi = paper_id.replace("crossref_", "").replace("_", "/")
        elif paper_id.startswith("10."):
            doi = paper_id
        else:
            return Err("Invalid DOI format")
        
        url = f"{self.BASE_URL}/works/{doi}"
        
        response = self.client.get(url)
        if response.is_err:
            return Ok(None)
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        message = safe_get(data, "message", {})
        
        return Ok(self._parse_work(message))
    
    def search_by_publisher(self, query: str, publisher: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search filtered by publisher."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        url = f"{self.BASE_URL}/works"
        params = {
            "query": query,
            "filter": f"publisher-name:{publisher}",
            "rows": str(min(100, max_results)),
            "select": "DOI,title,author,published,abstract,container-title,is-referenced-by-count,publisher,type"
        }
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        items = safe_get(safe_get(data, "message", {}), "items", [])
        
        papers = []
        for item in items:
            paper = self._parse_work(item)
            if paper:
                papers.append(paper)
        
        return Ok(papers)
