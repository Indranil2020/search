"""
Unpaywall Adapter

Find open access versions of papers.
Free API with email.
"""

from typing import Optional

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import Paper, AccessType
from backend.utils.result import Result, Ok, Err, safe_get


class UnpaywallAdapter(BaseAdapter):
    """Unpaywall adapter for finding open access versions."""
    
    BASE_URL = "https://api.unpaywall.org/v2"
    
    def __init__(self, email: str = "user@example.com"):
        config = AdapterConfig(
            name="Unpaywall",
            rate_limit=10.0,
            timeout=15
        )
        super().__init__(config)
        self.email = email
    
    def search(self, query: str, max_results: int = 100) -> Result[list, str]:
        """Unpaywall doesn't support search, only DOI lookup."""
        return Ok([])
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Not implemented - use find_open_access instead."""
        return Ok(None)
    
    def find_open_access(self, doi: str) -> Result[Optional[dict], str]:
        """
        Find open access version of a paper.
        
        Returns dict with:
        - is_oa: bool
        - best_oa_location: dict with url, pdf_url, etc.
        - oa_locations: list of all OA locations
        """
        
        if not doi:
            return Err("Empty DOI")
        
        url = f"{self.BASE_URL}/{doi}"
        params = {"email": self.email}
        
        response = self.client.get(url, params=params)
        if response.is_err:
            return Ok(None)
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Ok(None)
        
        data = json_result.unwrap()
        
        is_oa = safe_get(data, "is_oa", False)
        best_location = safe_get(data, "best_oa_location", {})
        all_locations = safe_get(data, "oa_locations", [])
        
        result = {
            "is_oa": is_oa,
            "best_oa_location": best_location,
            "oa_locations": all_locations,
            "pdf_url": safe_get(best_location, "url_for_pdf"),
            "html_url": safe_get(best_location, "url"),
            "version": safe_get(best_location, "version"),
            "host_type": safe_get(best_location, "host_type")
        }
        
        return Ok(result)
    
    def enrich_paper(self, paper: Paper) -> Paper:
        """
        Enrich paper with open access information.
        Updates access_type, pdf_url, and urls.
        """
        
        if not paper.doi:
            return paper
        
        oa_result = self.find_open_access(paper.doi)
        if oa_result.is_err:
            return paper
        
        oa_data = oa_result.unwrap()
        if not oa_data:
            return paper
        
        if oa_data.get("is_oa"):
            paper.access_type = AccessType.OPEN
            
            pdf_url = oa_data.get("pdf_url")
            if pdf_url:
                paper.pdf_url = pdf_url
                paper.urls["pdf"] = pdf_url
            
            html_url = oa_data.get("html_url")
            if html_url:
                paper.html_url = html_url
                paper.urls["oa_html"] = html_url
        
        return paper
