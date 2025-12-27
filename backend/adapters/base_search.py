"""
BASE (Bielefeld Academic Search Engine) Adapter

270M+ documents from 10,000+ sources.
Free API, no key required.
"""

from typing import List, Optional

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int, safe_list


class BASEAdapter(BaseAdapter):
    """BASE search adapter."""
    
    BASE_URL = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
    
    def __init__(self):
        config = AdapterConfig(
            name="BASE",
            rate_limit=1.0,
            timeout=30
        )
        super().__init__(config)
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search BASE."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        params = {
            "func": "PerformSearch",
            "query": query,
            "hits": str(min(max_results, 125)),
            "format": "json"
        }
        
        response = self.client.get(self.BASE_URL, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        docs = safe_get(safe_get(data, "response", {}), "docs", [])
        
        papers = []
        for doc in docs:
            paper = self._parse_doc(doc)
            if paper:
                papers.append(paper)
        
        return Ok(papers[:max_results])
    
    def _parse_doc(self, data: dict) -> Optional[Paper]:
        """Parse BASE document."""
        
        doc_id = safe_get(data, "dcdocid")
        if not doc_id:
            return None
        
        title = safe_get(data, "dctitle", "Unknown")
        if isinstance(title, list):
            title = title[0] if title else "Unknown"
        
        # Authors
        authors = []
        author_data = safe_get(data, "dcauthor", [])
        if isinstance(author_data, str):
            author_data = [author_data]
        for name in author_data:
            if name:
                authors.append(Author(name=name))
        
        # Year
        year = safe_int(safe_get(data, "dcyear"))
        
        # Abstract
        abstract = safe_get(data, "dcdescription")
        if isinstance(abstract, list):
            abstract = " ".join(abstract) if abstract else None
        
        # DOI
        doi = None
        identifier = safe_get(data, "dcidentifier")
        if identifier:
            if isinstance(identifier, list):
                for ident in identifier:
                    if ident and "10." in str(ident):
                        doi = self._extract_doi(str(ident))
                        break
            elif "10." in str(identifier):
                doi = self._extract_doi(str(identifier))
        
        # Link
        link = safe_get(data, "dclink")
        if isinstance(link, list):
            link = link[0] if link else None
        
        # Source
        source_name = safe_get(data, "dcsource")
        if isinstance(source_name, list):
            source_name = source_name[0] if source_name else None
        
        # Open access
        is_oa = safe_get(data, "dcoa") == "1"
        
        paper = Paper(
            id=f"base_{doc_id}",
            title=title,
            authors=authors,
            year=year,
            journal=source_name,
            doi=doi,
            abstract=abstract,
            source="BASE",
            source_type=SourceType.UNKNOWN,
            sources_found_in=["BASE"],
            access_type=AccessType.OPEN if is_oa else AccessType.UNKNOWN
        )
        
        paper.urls = {}
        if link:
            paper.urls["link"] = link
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
            paper.urls["scihub"] = f"https://sci-hub.se/{doi}"
        
        paper.reliability = calculate_reliability(
            paper,
            is_peer_reviewed=False,
            journal_name=source_name,
            citation_count=0,
            sources_found=1,
            year=year
        )
        
        return paper
    
    def _extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI from text."""
        import re
        match = re.search(r'10\.\d{4,9}/[^\s]+', text)
        return match.group(0) if match else None
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by ID (not supported by BASE)."""
        return Ok(None)
