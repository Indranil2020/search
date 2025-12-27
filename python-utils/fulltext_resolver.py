#!/usr/bin/env python3
"""
Full-Text Resolver - Open Access and Paywall Bypass

This module provides full-text resolution for scientific papers via:
1. Unpaywall - Legal open access discovery
2. Sci-Hub - Paywall bypass (use according to your jurisdiction)
3. PubMed Central - Free biomedical full texts
4. arXiv - Preprints

Usage:
    python fulltext_resolver.py resolve <doi>
    python fulltext_resolver.py batch <file_with_dois>
"""

import sys
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Optional, List
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor


@dataclass
class FullTextResult:
    """Result of full-text resolution attempt"""
    doi: str
    found: bool
    pdf_url: Optional[str] = None
    source: str = "unknown"
    access_type: str = "unknown"  # open, green, bronze, gold, hybrid, paywalled
    license: Optional[str] = None
    error: Optional[str] = None


class UnpaywallResolver:
    """
    Unpaywall API - Legal open access finder
    FREE and legal - finds OA versions of papers
    API: https://unpaywall.org/products/api
    """
    
    BASE_URL = "https://api.unpaywall.org/v2"
    
    def __init__(self, email: str):
        self.email = email
    
    def resolve(self, doi: str) -> FullTextResult:
        """Resolve DOI to open access PDF via Unpaywall"""
        url = f"{self.BASE_URL}/{doi}?email={self.email}"
        
        data = self._fetch_json(url)
        
        if not data:
            return FullTextResult(doi=doi, found=False, error="No response from Unpaywall")
        
        if data.get("error"):
            return FullTextResult(doi=doi, found=False, error=data.get("message"))
        
        # Check for open access
        is_oa = data.get("is_oa", False)
        
        if not is_oa:
            return FullTextResult(
                doi=doi, 
                found=False, 
                access_type="paywalled",
                error="No open access version found"
            )
        
        # Find best open access location
        best_oa = data.get("best_oa_location", {})
        
        if not best_oa:
            return FullTextResult(doi=doi, found=False, access_type="unknown")
        
        pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url")
        
        return FullTextResult(
            doi=doi,
            found=bool(pdf_url),
            pdf_url=pdf_url,
            source="unpaywall",
            access_type=best_oa.get("oa_color", "unknown"),
            license=best_oa.get("license")
        )
    
    def _fetch_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL"""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "UltraResearchSystem/1.0"}
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read().decode())


class PubMedCentralResolver:
    """
    PubMed Central - Free biomedical full texts
    FREE and legal
    """
    
    BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0"
    
    def resolve(self, doi: str) -> FullTextResult:
        """Check if paper is available on PMC"""
        url = f"{self.BASE_URL}/?ids={doi}&format=json"
        
        data = self._fetch_json(url)
        
        if not data:
            return FullTextResult(doi=doi, found=False, error="No response from PMC")
        
        records = data.get("records", [])
        
        if not records:
            return FullTextResult(doi=doi, found=False)
        
        record = records[0]
        pmcid = record.get("pmcid")
        
        if not pmcid:
            return FullTextResult(doi=doi, found=False)
        
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        
        return FullTextResult(
            doi=doi,
            found=True,
            pdf_url=pdf_url,
            source="pmc",
            access_type="gold"
        )
    
    def _fetch_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL"""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "UltraResearchSystem/1.0"}
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read().decode())


class SciHubResolver:
    """
    Sci-Hub - Paywall bypass
    
    WARNING: Use according to your jurisdiction's laws.
    This is provided for educational purposes.
    """
    
    # Sci-Hub mirrors (these change frequently)
    MIRRORS = [
        "https://sci-hub.se",
        "https://sci-hub.st",
        "https://sci-hub.ru",
        "https://sci-hub.ee",
        "https://sci-hub.ren",
    ]
    
    def __init__(self):
        self.working_mirror = None
    
    def resolve(self, doi: str) -> FullTextResult:
        """Resolve DOI via Sci-Hub"""
        # Find working mirror
        mirror = self._find_working_mirror()
        
        if not mirror:
            return FullTextResult(
                doi=doi, 
                found=False, 
                error="No working Sci-Hub mirror found"
            )
        
        # Construct Sci-Hub URL
        scihub_url = f"{mirror}/{doi}"
        
        # We don't actually fetch the PDF, just provide the URL
        # The user can then access it themselves
        return FullTextResult(
            doi=doi,
            found=True,
            pdf_url=scihub_url,
            source="scihub",
            access_type="scihub"
        )
    
    def _find_working_mirror(self) -> Optional[str]:
        """Find a working Sci-Hub mirror"""
        if self.working_mirror:
            return self.working_mirror
        
        for mirror in self.MIRRORS:
            if self._test_mirror(mirror):
                self.working_mirror = mirror
                return mirror
        
        return None
    
    def _test_mirror(self, mirror: str) -> bool:
        """Test if a mirror is working"""
        req = urllib.request.Request(
            mirror,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        response = urllib.request.urlopen(req, timeout=10)
        return response.status == 200


class ArXivResolver:
    """
    arXiv - Preprints
    FREE and legal
    """
    
    def resolve_from_title(self, title: str) -> FullTextResult:
        """Search arXiv by title and return PDF URL if found"""
        encoded_title = urllib.parse.quote(title)
        url = f"http://export.arxiv.org/api/query?search_query=ti:{encoded_title}&max_results=1"
        
        data = self._fetch_xml(url)
        
        if not data:
            return FullTextResult(doi="", found=False)
        
        # Parse arXiv response (simplified)
        arxiv_id_match = re.search(r"<id>http://arxiv.org/abs/([^<]+)</id>", data)
        
        if not arxiv_id_match:
            return FullTextResult(doi="", found=False)
        
        arxiv_id = arxiv_id_match.group(1)
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        return FullTextResult(
            doi=f"arXiv:{arxiv_id}",
            found=True,
            pdf_url=pdf_url,
            source="arxiv",
            access_type="gold"
        )
    
    def _fetch_xml(self, url: str) -> Optional[str]:
        """Fetch XML from URL"""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "UltraResearchSystem/1.0"}
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        return response.read().decode()


class FullTextResolver:
    """
    Master resolver that tries multiple sources in order
    
    Resolution order:
    1. Unpaywall (legal OA)
    2. PubMed Central (legal OA for biomedical)
    3. arXiv (preprints)
    4. Sci-Hub (if enabled and legal in jurisdiction)
    """
    
    def __init__(self, email: str, enable_scihub: bool = False):
        self.unpaywall = UnpaywallResolver(email)
        self.pmc = PubMedCentralResolver()
        self.arxiv = ArXivResolver()
        self.scihub = SciHubResolver() if enable_scihub else None
    
    def resolve(self, doi: str, title: Optional[str] = None) -> FullTextResult:
        """
        Try to resolve full text from multiple sources
        
        Args:
            doi: DOI of the paper
            title: Optional title for arXiv search fallback
            
        Returns:
            FullTextResult with best available option
        """
        # 1. Try Unpaywall first (legal, comprehensive)
        result = self.unpaywall.resolve(doi)
        if result.found:
            return result
        
        # 2. Try PMC for biomedical papers
        result = self.pmc.resolve(doi)
        if result.found:
            return result
        
        # 3. Try arXiv if we have a title
        if title:
            result = self.arxiv.resolve_from_title(title)
            if result.found:
                return result
        
        # 4. Try Sci-Hub as last resort (if enabled)
        if self.scihub:
            result = self.scihub.resolve(doi)
            if result.found:
                return result
        
        # Nothing found
        return FullTextResult(
            doi=doi,
            found=False,
            access_type="paywalled",
            error="No open access version found in any source"
        )
    
    def batch_resolve(self, dois: List[str], max_workers: int = 5) -> List[FullTextResult]:
        """Resolve multiple DOIs in parallel"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.resolve, dois))
        return results


def main():
    """Main entry point for command-line usage"""
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: fulltext_resolver.py <resolve|batch> <doi|file>"
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    target = sys.argv[2]
    
    # Get configuration from environment
    email = os.getenv("UNPAYWALL_EMAIL", "researcher@example.com")
    enable_scihub = os.getenv("ENABLE_SCIHUB", "false").lower() == "true"
    
    resolver = FullTextResolver(email, enable_scihub)
    
    if command == "resolve":
        result = resolver.resolve(target)
        print(json.dumps(asdict(result), ensure_ascii=False))
        
    elif command == "batch":
        # Read DOIs from file
        with open(target, "r") as f:
            dois = [line.strip() for line in f if line.strip()]
        
        results = resolver.batch_resolve(dois)
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False))
        
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
