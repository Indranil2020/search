#!/usr/bin/env python3
"""
Scholarly Bridge - Google Scholar Access via scholarly package

This module provides a bridge between the Java backend and the scholarly
Python package for accessing Google Scholar without CAPTCHAs.

Usage:
    python scholarly_bridge.py search "query" [max_results]
    python scholarly_bridge.py author "author name"
    python scholarly_bridge.py citations "paper_title"
"""

import sys
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Scholarly package
from scholarly import scholarly, ProxyGenerator


@dataclass
class Paper:
    """Paper data structure matching Java Paper model"""
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: str
    citation_count: int
    doi: Optional[str]
    url: Optional[str]
    pdf_url: Optional[str]
    source: str = "google_scholar"
    access_type: str = "unknown"


class ScholarlyBridge:
    """Bridge class for scholarly package operations"""
    
    def __init__(self, use_proxy: bool = True, proxy_type: str = "free"):
        self.proxy_configured = False
        
        if use_proxy:
            self._setup_proxy(proxy_type)
    
    def _setup_proxy(self, proxy_type: str) -> None:
        """Configure proxy for rate limiting protection"""
        pg = ProxyGenerator()
        
        if proxy_type == "free":
            # Use free proxies (may be slower/less reliable)
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            self.proxy_configured = True
            
        elif proxy_type == "scraper":
            # ScraperAPI (requires API key)
            api_key = os.getenv("SCRAPER_API_KEY")
            if api_key:
                pg.ScraperAPI(api_key)
                scholarly.use_proxy(pg)
                self.proxy_configured = True
                
        elif proxy_type == "luminati":
            # Bright Data / Luminati (requires credentials)
            user = os.getenv("LUMINATI_USER")
            password = os.getenv("LUMINATI_PASSWORD")
            if user and password:
                pg.Luminati(user, password)
                scholarly.use_proxy(pg)
                self.proxy_configured = True
    
    def search_papers(self, query: str, max_results: int = 100) -> List[Paper]:
        """
        Search Google Scholar for papers matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects
        """
        papers = []
        
        search_query = scholarly.search_pubs(query)
        
        count = 0
        while count < max_results:
            result = next(search_query, None)
            if result is None:
                break
                
            paper = self._parse_publication(result)
            if paper:
                papers.append(paper)
            
            count += 1
        
        return papers
    
    def search_author(self, author_name: str) -> dict:
        """
        Search for an author and get their publications.
        
        Args:
            author_name: Name of the author to search
            
        Returns:
            Dictionary with author info and publications
        """
        search_query = scholarly.search_author(author_name)
        author = next(search_query, None)
        
        if author is None:
            return {"error": "Author not found"}
        
        # Fill author details
        author = scholarly.fill(author)
        
        publications = []
        for pub in author.get("publications", [])[:50]:
            filled_pub = scholarly.fill(pub)
            paper = self._parse_publication(filled_pub)
            if paper:
                publications.append(paper)
        
        return {
            "name": author.get("name", ""),
            "affiliation": author.get("affiliation", ""),
            "interests": author.get("interests", []),
            "citations": author.get("citedby", 0),
            "h_index": author.get("hindex", 0),
            "publications": [asdict(p) for p in publications]
        }
    
    def get_citations(self, paper_title: str) -> List[Paper]:
        """
        Get papers that cite a given paper.
        
        Args:
            paper_title: Title of the paper to find citations for
            
        Returns:
            List of citing papers
        """
        search_query = scholarly.search_pubs(paper_title)
        paper = next(search_query, None)
        
        if paper is None:
            return []
        
        # Fill to get citation info
        paper = scholarly.fill(paper)
        
        citing_papers = []
        citations = scholarly.citedby(paper)
        
        count = 0
        while count < 50:
            citation = next(citations, None)
            if citation is None:
                break
                
            citing_paper = self._parse_publication(citation)
            if citing_paper:
                citing_papers.append(citing_paper)
            
            count += 1
        
        return citing_papers
    
    def _parse_publication(self, pub: dict) -> Optional[Paper]:
        """Parse scholarly publication result into Paper object"""
        bib = pub.get("bib", {})
        
        title = bib.get("title", "")
        if not title:
            return None
        
        # Extract authors
        authors = bib.get("author", "").split(" and ")
        authors = [a.strip() for a in authors if a.strip()]
        
        # Extract year
        year = None
        year_str = bib.get("pub_year", "")
        if year_str:
            year = int(year_str) if year_str.isdigit() else None
        
        # Extract citation count
        citation_count = pub.get("num_citations", 0)
        if citation_count is None:
            citation_count = 0
        
        # Extract URLs
        url = pub.get("pub_url", "")
        pdf_url = pub.get("eprint_url", "")
        
        # Try to extract DOI
        doi = None
        pub_url = pub.get("pub_url", "")
        if "doi.org" in pub_url:
            doi = pub_url.split("doi.org/")[-1]
        
        return Paper(
            title=title,
            authors=authors,
            year=year,
            abstract=bib.get("abstract", ""),
            citation_count=citation_count,
            doi=doi,
            url=url,
            pdf_url=pdf_url if pdf_url else None,
            access_type="open" if pdf_url else "unknown"
        )


def main():
    """Main entry point for command-line usage"""
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: scholarly_bridge.py <command> <query> [max_results]"}))
        sys.exit(1)
    
    command = sys.argv[1]
    query = sys.argv[2]
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    # Determine proxy type from environment
    proxy_type = os.getenv("SCHOLARLY_PROXY", "free")
    
    bridge = ScholarlyBridge(use_proxy=True, proxy_type=proxy_type)
    
    if command == "search":
        papers = bridge.search_papers(query, max_results)
        result = [asdict(p) for p in papers]
        print(json.dumps(result, ensure_ascii=False))
        
    elif command == "author":
        result = bridge.search_author(query)
        print(json.dumps(result, ensure_ascii=False))
        
    elif command == "citations":
        papers = bridge.get_citations(query)
        result = [asdict(p) for p in papers]
        print(json.dumps(result, ensure_ascii=False))
        
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
