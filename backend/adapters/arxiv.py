"""
arXiv Adapter

2M+ preprints in physics, math, CS, biology.
Free API: 1 request per second.
"""

from typing import List, Optional
import xml.etree.ElementTree as ET
import re

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_int


class ArXivAdapter(BaseAdapter):
    """arXiv preprint adapter."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    NS = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
    
    def __init__(self):
        config = AdapterConfig(
            name="arXiv",
            rate_limit=1.0,
            timeout=30
        )
        super().__init__(config)
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search arXiv."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        papers = []
        start = 0
        batch_size = min(100, max_results)
        
        while len(papers) < max_results:
            batch = self._search_batch(query, start, batch_size)
            if batch.is_err:
                if papers:
                    return Ok(papers)
                return batch
            
            results = batch.unwrap()
            if not results:
                break
            
            papers.extend(results)
            start += batch_size
            
            if len(results) < batch_size:
                break
        
        return Ok(papers[:max_results])
    
    def _search_batch(self, query: str, start: int, max_results: int) -> Result[List[Paper], str]:
        """Search batch."""
        
        params = {
            "search_query": f"all:{query}",
            "start": str(start),
            "max_results": str(max_results),
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = self.client.get(self.BASE_URL, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        xml_result = response.unwrap().xml()
        if xml_result.is_err:
            return Err(f"Invalid XML: {xml_result.error}")
        
        root = xml_result.unwrap()
        
        papers = []
        for entry in root.findall('atom:entry', self.NS):
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)
        
        return Ok(papers)
    
    def _parse_entry(self, entry: ET.Element) -> Optional[Paper]:
        """Parse arXiv entry."""
        
        id_el = entry.find('atom:id', self.NS)
        if id_el is None or not id_el.text:
            return None
        
        arxiv_id = self._extract_id(id_el.text)
        if not arxiv_id:
            return None
        
        # Title
        title_el = entry.find('atom:title', self.NS)
        title = title_el.text.strip() if title_el is not None and title_el.text else "Unknown"
        title = ' '.join(title.split())
        
        # Authors
        authors = []
        for author_el in entry.findall('atom:author', self.NS):
            name_el = author_el.find('atom:name', self.NS)
            if name_el is not None and name_el.text:
                authors.append(Author(name=name_el.text.strip()))
        
        # Year
        published_el = entry.find('atom:published', self.NS)
        year = None
        if published_el is not None and published_el.text:
            year = safe_int(published_el.text[:4])
        
        # Abstract
        abstract_el = entry.find('atom:summary', self.NS)
        abstract = None
        if abstract_el is not None and abstract_el.text:
            abstract = ' '.join(abstract_el.text.strip().split())
        
        # Categories
        keywords = []
        for cat in entry.findall('atom:category', self.NS):
            term = cat.get('term')
            if term:
                keywords.append(term)
        
        # DOI
        doi_el = entry.find('arxiv:doi', self.NS)
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else None
        
        # Journal ref
        journal_el = entry.find('arxiv:journal_ref', self.NS)
        journal = journal_el.text.strip() if journal_el is not None and journal_el.text else None
        
        # Primary category
        primary_el = entry.find('arxiv:primary_category', self.NS)
        primary = primary_el.get('term') if primary_el is not None else None
        
        paper = Paper(
            id=f"arxiv_{arxiv_id}",
            title=title,
            authors=authors,
            year=year,
            journal=journal or f"arXiv:{primary}" if primary else "arXiv",
            doi=doi,
            arxiv_id=arxiv_id,
            abstract=abstract,
            keywords=keywords[:10],
            source="arXiv",
            source_type=SourceType.PREPRINT,
            sources_found_in=["arXiv"],
            access_type=AccessType.OPEN,
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        )
        
        paper.urls = {
            "arxiv": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf": f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        }
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
        
        paper.reliability = calculate_reliability(
            paper,
            is_peer_reviewed=False,
            journal_name=None,
            citation_count=0,
            sources_found=1,
            year=year
        )
        
        return paper
    
    def _extract_id(self, url_or_id: str) -> Optional[str]:
        """Extract arXiv ID from URL."""
        
        if not url_or_id:
            return None
        
        # New style: YYMM.NNNNN
        match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', url_or_id)
        if match:
            return match.group(1)
        
        # Old style: category/YYMMNNN
        match = re.search(r'([a-z-]+/\d{7})(v\d+)?', url_or_id)
        if match:
            return match.group(1)
        
        return None
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by arXiv ID."""
        
        if not paper_id:
            return Err("Empty ID")
        
        arxiv_id = paper_id.replace("arxiv_", "").strip()
        arxiv_id = self._extract_id(arxiv_id) or arxiv_id
        
        params = {"id_list": arxiv_id, "max_results": "1"}
        
        response = self.client.get(self.BASE_URL, params=params)
        if response.is_err:
            return Err(f"Failed: {response.error.message}")
        
        xml_result = response.unwrap().xml()
        if xml_result.is_err:
            return Err(f"Invalid XML: {xml_result.error}")
        
        root = xml_result.unwrap()
        entries = root.findall('atom:entry', self.NS)
        
        if entries:
            return Ok(self._parse_entry(entries[0]))
        
        return Ok(None)
