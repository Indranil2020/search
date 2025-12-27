"""
Europe PMC Adapter

40M+ life science publications.
Free API, no key required.
"""

from typing import List, Optional

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int, safe_list


class EuropePMCAdapter(BaseAdapter):
    """Europe PMC adapter."""
    
    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    
    def __init__(self):
        config = AdapterConfig(
            name="Europe PMC",
            rate_limit=10.0,
            timeout=30
        )
        super().__init__(config)
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search Europe PMC."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        papers = []
        cursor = "*"
        page_size = min(100, max_results)
        
        while len(papers) < max_results:
            batch = self._search_batch(query, page_size, cursor)
            if batch.is_err:
                if papers:
                    return Ok(papers)
                return batch
            
            results, next_cursor = batch.unwrap()
            if not results:
                break
            
            papers.extend(results)
            
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
        
        return Ok(papers[:max_results])
    
    def _search_batch(self, query: str, page_size: int, cursor: str) -> Result[tuple, str]:
        """Search batch."""
        
        url = f"{self.BASE_URL}/search"
        params = {
            "query": query,
            "pageSize": str(page_size),
            "cursorMark": cursor,
            "format": "json",
            "resultType": "core"
        }
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        result_list = safe_get(data, "resultList", {})
        results = safe_get(result_list, "result", [])
        next_cursor = safe_get(data, "nextCursorMark")
        
        papers = []
        for item in results:
            paper = self._parse_result(item)
            if paper:
                papers.append(paper)
        
        return Ok((papers, next_cursor))
    
    def _parse_result(self, data: dict) -> Optional[Paper]:
        """Parse Europe PMC result."""
        
        pmid = safe_get(data, "pmid")
        pmcid = safe_get(data, "pmcid")
        
        if not pmid and not pmcid:
            return None
        
        paper_id = f"europmc_{pmcid or pmid}"
        
        title = safe_get(data, "title", "Unknown")
        
        # Authors
        authors = []
        author_list = safe_get(data, "authorList", {})
        for author in safe_get(author_list, "author", []):
            name = safe_get(author, "fullName")
            if name:
                authors.append(Author(name=name))
        
        # Year
        year = None
        pub_year = safe_get(data, "pubYear")
        if pub_year:
            year = safe_int(pub_year)
        
        # Journal
        journal = safe_get(data, "journalTitle")
        
        # Abstract
        abstract = safe_get(data, "abstractText")
        
        # DOI
        doi = safe_get(data, "doi")
        
        # Citations
        citation_count = safe_int(safe_get(data, "citedByCount", 0))
        
        # Open access
        is_oa = safe_get(data, "isOpenAccess") == "Y"
        
        # Source type
        source_type = SourceType.PEER_REVIEWED
        pub_type = safe_get(data, "pubType")
        if pub_type == "preprint":
            source_type = SourceType.PREPRINT
        
        paper = Paper(
            id=paper_id,
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            abstract=abstract,
            citation_count=citation_count,
            source="Europe PMC",
            source_type=source_type,
            sources_found_in=["Europe PMC"],
            access_type=AccessType.OPEN if is_oa else AccessType.PAYWALLED
        )
        
        paper.urls = {
            "europepmc": f"https://europepmc.org/article/MED/{pmid}" if pmid else f"https://europepmc.org/article/PMC/{pmcid}"
        }
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
            paper.urls["scihub"] = f"https://sci-hub.se/{doi}"
        if pmcid:
            paper.urls["pmc"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            paper.pdf_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"
        
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
        """Get paper by PMID or PMCID."""
        
        if not paper_id:
            return Err("Empty ID")
        
        clean_id = paper_id.replace("europmc_", "")
        
        if clean_id.startswith("PMC"):
            source = "PMC"
            ext_id = clean_id
        else:
            source = "MED"
            ext_id = clean_id
        
        url = f"{self.BASE_URL}/search"
        params = {
            "query": f"EXT_ID:{ext_id} AND SRC:{source}",
            "format": "json",
            "resultType": "core"
        }
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Ok(None)
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        results = safe_get(safe_get(data, "resultList", {}), "result", [])
        
        if results:
            return Ok(self._parse_result(results[0]))
        
        return Ok(None)
