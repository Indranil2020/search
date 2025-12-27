"""
OpenAlex Adapter

240M+ works, completely free and open.
10 requests/second without key.
"""

from typing import List, Optional, Dict

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int


class OpenAlexAdapter(BaseAdapter):
    """OpenAlex adapter."""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self, email: Optional[str] = None):
        config = AdapterConfig(
            name="OpenAlex",
            rate_limit=10.0,
            timeout=30
        )
        super().__init__(config)
        self.email = email or "user@example.com"
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search OpenAlex."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        papers = []
        page = 1
        per_page = min(200, max_results)
        
        while len(papers) < max_results:
            batch = self._search_batch(query, page, per_page)
            if batch.is_err:
                if papers:
                    return Ok(papers)
                return batch
            
            results = batch.unwrap()
            if not results:
                break
            
            papers.extend(results)
            page += 1
            
            if len(results) < per_page:
                break
        
        return Ok(papers[:max_results])
    
    def _search_batch(self, query: str, page: int, per_page: int) -> Result[List[Paper], str]:
        """Search batch."""
        
        url = f"{self.BASE_URL}/works"
        params = {
            "search": query,
            "page": str(page),
            "per_page": str(per_page),
            "mailto": self.email
        }
        
        response = self.client.get(url, params=params)
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
        """Parse OpenAlex work."""
        
        oa_id = safe_get(data, "id", "")
        if not oa_id:
            return None
        
        short_id = oa_id.replace("https://openalex.org/", "")
        title = safe_get(data, "title", "Unknown")
        
        # DOI
        doi = safe_get(data, "doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        
        # Authors
        authors = []
        for authorship in safe_get(data, "authorships", []):
            author = safe_get(authorship, "author", {})
            name = safe_get(author, "display_name")
            if name:
                orcid = safe_get(author, "orcid")
                if orcid:
                    orcid = orcid.replace("https://orcid.org/", "")
                authors.append(Author(name=name, orcid=orcid))
        
        # Year
        year = safe_int(safe_get(data, "publication_year"))
        
        # Journal
        journal = None
        publisher = None
        source = safe_get(data, "primary_location", {})
        source_info = safe_get(source, "source", {})
        if source_info:
            journal = safe_get(source_info, "display_name")
            publisher = safe_get(source_info, "host_organization_name")
        
        # Abstract
        abstract = None
        abstract_inv = safe_get(data, "abstract_inverted_index", {})
        if abstract_inv:
            abstract = self._reconstruct_abstract(abstract_inv)
        
        # Metrics
        citation_count = safe_int(safe_get(data, "cited_by_count", 0))
        
        # Type
        work_type = safe_get(data, "type", "")
        source_type = self._map_type(work_type)
        
        # Open access
        oa_info = safe_get(data, "open_access", {})
        is_oa = safe_get(oa_info, "is_oa", False)
        oa_url = safe_get(oa_info, "oa_url")
        
        # IDs
        ids = safe_get(data, "ids", {})
        pmid = safe_get(ids, "pmid")
        if pmid:
            pmid = pmid.replace("https://pubmed.ncbi.nlm.nih.gov/", "")
        pmcid = safe_get(ids, "pmcid")
        
        # Keywords
        keywords = []
        for concept in safe_get(data, "concepts", [])[:10]:
            name = safe_get(concept, "display_name")
            if name:
                keywords.append(name)
        
        paper = Paper(
            id=f"openalex_{short_id}",
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            publisher=publisher,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            abstract=abstract,
            keywords=keywords,
            citation_count=citation_count,
            source="OpenAlex",
            source_type=source_type,
            sources_found_in=["OpenAlex"],
            access_type=AccessType.OPEN if is_oa else AccessType.PAYWALLED,
            pdf_url=oa_url
        )
        
        paper.urls = {"openalex": oa_id}
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
            paper.urls["scihub"] = f"https://sci-hub.se/{doi}"
        if oa_url:
            paper.urls["pdf"] = oa_url
        
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
        """Map OpenAlex type."""
        mapping = {
            "article": SourceType.PEER_REVIEWED,
            "book-chapter": SourceType.BOOK_CHAPTER,
            "dissertation": SourceType.THESIS,
            "preprint": SourceType.PREPRINT,
            "proceedings-article": SourceType.CONFERENCE
        }
        return mapping.get(work_type, SourceType.UNKNOWN)
    
    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """Reconstruct abstract from inverted index."""
        if not inverted_index:
            return ""
        
        positions = {}
        for word, indices in inverted_index.items():
            for idx in indices:
                positions[idx] = word
        
        if not positions:
            return ""
        
        max_pos = max(positions.keys())
        words = [positions.get(i, "") for i in range(max_pos + 1)]
        return " ".join(w for w in words if w)
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by OpenAlex ID or DOI."""
        
        if not paper_id:
            return Err("Empty ID")
        
        if paper_id.startswith("openalex_"):
            oa_id = paper_id.replace("openalex_", "")
            url = f"{self.BASE_URL}/works/{oa_id}"
        elif paper_id.startswith("10."):
            url = f"{self.BASE_URL}/works/doi:{paper_id}"
        elif paper_id.startswith("W"):
            url = f"{self.BASE_URL}/works/{paper_id}"
        else:
            return Err("Invalid ID format")
        
        params = {"mailto": self.email}
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Ok(None)
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        return Ok(self._parse_work(data))
    
    def get_citations(self, paper: Paper) -> Result[List[Paper], str]:
        """Get citing papers."""
        
        filter_value = None
        if paper.id.startswith("openalex_"):
            oa_id = paper.id.replace("openalex_", "")
            filter_value = f"cites:{oa_id}"
        elif paper.doi:
            filter_value = f"cites:doi:{paper.doi}"
        
        if not filter_value:
            return Ok([])
        
        url = f"{self.BASE_URL}/works"
        params = {"filter": filter_value, "per_page": "100", "mailto": self.email}
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Err(f"Failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        
        papers = []
        for item in safe_get(data, "results", []):
            p = self._parse_work(item)
            if p:
                papers.append(p)
        
        return Ok(papers)
