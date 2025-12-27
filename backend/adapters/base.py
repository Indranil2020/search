"""
Base Adapter Interface

All source adapters inherit from this base class.
All methods return Result types - no exceptions raised.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass

from backend.models.paper import Paper
from backend.utils.result import Result, Ok, Err
from backend.utils.http import HttpClient


@dataclass
class AdapterConfig:
    """Adapter configuration."""
    name: str
    rate_limit: float = 1.0
    timeout: int = 30
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class BaseAdapter(ABC):
    """Base adapter for all data sources."""
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self.client = HttpClient(
            timeout=config.timeout,
            rate_limit=config.rate_limit
        )
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @abstractmethod
    def search(self, query: str, max_results: int = 100) -> Result[List[Paper], str]:
        """Search for papers. Returns Result."""
        pass
    
    @abstractmethod
    def get_by_id(self, paper_id: str) -> Result[Optional[Paper], str]:
        """Get paper by ID. Returns Result."""
        pass
    
    def get_citations(self, paper: Paper) -> Result[List[Paper], str]:
        """Get citing papers. Override if supported."""
        return Ok([])
    
    def get_references(self, paper: Paper) -> Result[List[Paper], str]:
        """Get referenced papers. Override if supported."""
        return Ok([])
