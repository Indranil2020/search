"""
PubMed/MEDLINE Adapter

35M+ biomedical papers.
Free API: 3 req/s without key, 10 req/s with key.
"""

from typing import List, Optional
import xml.etree.ElementTree as ET

from .base import BaseAdapter, AdapterConfig
from backend.models.paper import (
    Paper, Author, SourceType, AccessType, calculate_reliability
)
from backend.utils.result import Result, Ok, Err, safe_get, safe_int


class PubMedAdapter(BaseAdapter):
    """PubMed search adapter."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None, email: str = "user@example.com"):
        rate = 10.0 if api_key else 3.0
        config = AdapterConfig(
            name="PubMed",
            rate_limit=rate,
            timeout=30,
            api_key=api_key
        )
        super().__init__(config)
        self.email = email
    
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search PubMed."""
        
        if not query or not query.strip():
            return Err("Empty query")
        
        # Step 1: Search for PMIDs
        pmids_result = self._search_pmids(query, max_results)
        if pmids_result.is_err:
            return Err(pmids_result.error)
        
        pmids = pmids_result.unwrap()
        if not pmids:
            return Ok([])
        
        # Step 2: Fetch details
        return self._fetch_details(pmids)
    
    def _search_pmids(self, query: str, max_results: int) -> Result[List[str], str]:
        """Search for PMIDs."""
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": str(max_results),
            "retmode": "json",
            "sort": "relevance"
        }
        
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        if self.email:
            params["email"] = self.email
        
        url = f"{self.BASE_URL}/esearch.fcgi"
        response = self.client.get(url, params=params)
        
        if response.is_err:
            return Err(f"Search failed: {response.error.message}")
        
        json_result = response.unwrap().json()
        if json_result.is_err:
            return Err(f"Invalid response: {json_result.error}")
        
        data = json_result.unwrap()
        esearch = safe_get(data, "esearchresult", {})
        idlist = safe_get(esearch, "idlist", [])
        
        return Ok(idlist)
    
    def _fetch_details(self, pmids: List[str]) -> Result[List[Paper], str]:
        """Fetch paper details."""
        
        if not pmids:
            return Ok([])
        
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        
        url = f"{self.BASE_URL}/efetch.fcgi"
        response = self.client.get(url, params=params)
        
        if response.is_err:
            return Err(f"Fetch failed: {response.error.message}")
        
        xml_result = response.unwrap().xml()
        if xml_result.is_err:
            return Err(f"Invalid XML: {xml_result.error}")
        
        root = xml_result.unwrap()
        
        papers = []
        for article in root.findall(".//PubmedArticle"):
            paper = self._parse_article(article)
            if paper:
                papers.append(paper)
        
        return Ok(papers)
    
    def _parse_article(self, article: ET.Element) -> Optional[Paper]:
        """Parse PubmedArticle element."""
        
        medline = article.find("MedlineCitation")
        if medline is None:
            return None
        
        article_data = medline.find("Article")
        if article_data is None:
            return None
        
        # PMID
        pmid_el = medline.find("PMID")
        pmid = pmid_el.text if pmid_el is not None else None
        if not pmid:
            return None
        
        # Title
        title_el = article_data.find("ArticleTitle")
        title = title_el.text if title_el is not None and title_el.text else "Unknown"
        
        # Authors
        authors = []
        author_list = article_data.find("AuthorList")
        if author_list is not None:
            for author_el in author_list.findall("Author"):
                lastname = author_el.find("LastName")
                forename = author_el.find("ForeName")
                parts = []
                if forename is not None and forename.text:
                    parts.append(forename.text)
                if lastname is not None and lastname.text:
                    parts.append(lastname.text)
                if parts:
                    authors.append(Author(name=" ".join(parts)))
        
        # Year
        year = None
        journal = article_data.find("Journal")
        if journal is not None:
            issue = journal.find("JournalIssue")
            if issue is not None:
                pubdate = issue.find("PubDate")
                if pubdate is not None:
                    year_el = pubdate.find("Year")
                    if year_el is not None:
                        year = safe_int(year_el.text)
        
        # Journal name
        journal_name = None
        if journal is not None:
            jt = journal.find("Title")
            if jt is not None:
                journal_name = jt.text
        
        # Abstract
        abstract = None
        abstract_el = article_data.find("Abstract")
        if abstract_el is not None:
            texts = []
            for text_el in abstract_el.findall("AbstractText"):
                if text_el.text:
                    texts.append(text_el.text)
            abstract = " ".join(texts)
        
        # DOI
        doi = None
        article_ids = article.find(".//ArticleIdList")
        if article_ids is not None:
            for aid in article_ids.findall("ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text
                    break
        
        # PMCID
        pmcid = None
        if article_ids is not None:
            for aid in article_ids.findall("ArticleId"):
                if aid.get("IdType") == "pmc":
                    pmcid = aid.text
                    break
        
        # Keywords
        keywords = []
        mesh_list = medline.find("MeshHeadingList")
        if mesh_list is not None:
            for mesh in mesh_list.findall("MeshHeading"):
                desc = mesh.find("DescriptorName")
                if desc is not None and desc.text:
                    keywords.append(desc.text)
        
        paper = Paper(
            id=f"pubmed_{pmid}",
            title=title,
            authors=authors,
            year=year,
            journal=journal_name,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            abstract=abstract,
            keywords=keywords[:10],
            source="PubMed",
            source_type=SourceType.PEER_REVIEWED,
            sources_found_in=["PubMed"],
            access_type=AccessType.OPEN if pmcid else AccessType.PAYWALLED
        )
        
        # URLs
        paper.urls = {
            "pubmed": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        }
        if doi:
            paper.urls["doi"] = f"https://doi.org/{doi}"
            paper.urls["scihub"] = f"https://sci-hub.se/{doi}"
        if pmcid:
            paper.urls["pmc"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            paper.pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        
        # Calculate reliability
        paper.reliability = calculate_reliability(
            paper,
            is_peer_reviewed=True,
            journal_name=journal_name,
            citation_count=0,
            sources_found=1,
            year=year
        )
        
        return paper
    
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by PMID."""
        
        if not paper_id:
            return Err("Empty ID")
        
        pmid = paper_id.replace("pubmed_", "").strip()
        result = self._fetch_details([pmid])
        
        if result.is_err:
            return Err(result.error)
        
        papers = result.unwrap()
        return Ok(papers[0] if papers else None)
