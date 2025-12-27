"""
Data Models
"""

from .paper import (
    Paper,
    Author,
    ReliabilityScore,
    ReliabilityLevel,
    AccessType,
    SourceType,
    calculate_reliability,
    HIGH_IMPACT_JOURNALS,
    REPUTABLE_PUBLISHERS
)

__all__ = [
    "Paper",
    "Author",
    "ReliabilityScore",
    "ReliabilityLevel",
    "AccessType",
    "SourceType",
    "calculate_reliability",
    "HIGH_IMPACT_JOURNALS",
    "REPUTABLE_PUBLISHERS"
]
