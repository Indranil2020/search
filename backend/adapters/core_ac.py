"""
CORE Adapter

200M+ open access papers.
Free API with key.
"""

from typing import List, Optional, Dict

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int


class COREAdapter(BaseAdapter):
    """CORE open access adapter."""
    
    BASE_URL = "https://api.core.ac.uk/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        config = AdapterConfig(
            name="CORE",
            rate_limit=10.0,
            timeout=30,
            api_key=api_key
        )
        super().__init__(config)
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search CORE."""
        
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
        
        url = f"{self.BASE_URL}/search/works"
        params = {
            "q": query,
            "limit": str(limit),
            "offset": str(offset)
        }
        
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        response = self.client.get(url, headers=headers, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        results = safe_get(data, "results", [])
        
        papers = []
        for item in results:
            paper = self._parse_work(item)
            if paper:
                papers.append(paper)
        
        return Ok(papers)
    
    def _parse_work(self, data: Dict) -> Optional[Paper]:
        """Parse CORE work."""
        
        core_id = safe_get(data, "id")
        if not core_id:
            return None
        
        title = safe_get(data, "title", "Unknown")
        
        # Authors
        authors = []
        for author in safe_get(data, "authors", []):
            name = safe_get(author, "name")
            if name:
                authors.append(Author(name=name))
        
        # Year
        year = safe_int(safe_get(data, "yearPublished"))
        
        # Journal
        journal = safe_get(data, "publisher")
        
        # DOI
        doi = safe_get(data, "doi")
        
        # Abstract
        abstract = safe_get(data, "abstract")
        
        # Download URL (open access)
        download_url = safe_get(data, "downloadUrl")
        
        # Source type
        source_type = SourceType.UNKNOWN
        doc_type = safe_get(data, "documentType", "").lower()
        if "article" in doc_type or "journal" in doc_type:
            source_type = SourceType.PEER_REVIEWED
        elif "thesis" in doc_type:
            source_type = SourceType.THESIS
        elif "conference" in doc_type:
            source_type = SourceType.CONFERENCE
        
        paper = Paper(
            id=f"core_{core_id}",
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            doi=doi,
            abstract=abstract,
            source="CORE",
            source_type=source_type,
            sources_found_in=["CORE"],
            access_type=AccessType.OPEN if download_url else AccessType.UNKNOWN,
            pdf_url=download_url
        )
        
        paper.urls = {}
        if download_url:
            paper.urls["pdf"] = download_url
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
            paper.urls["scihub"] = f"https://sci-hub.se/{doi}"
        
        paper.reliability = calculate_reliability(
            paper,
            is_peer_reviewed=(source_type == SourceType.PEER_REVIEWED),
            journal_name=journal,
            citation_count=0,
            sources_found=1,
            year=year
        )
        
        return paper
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by CORE ID."""
        
        if not paper_id:
            return Err("Empty ID")
        
        core_id = paper_id.replace("core_", "").strip()
        
        url = f"{self.BASE_URL}/works/{core_id}"
        
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        response = self.client.get(url, headers=headers)
        if response.is_err:
            return Ok(None)
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        return Ok(self._parse_work(data))
