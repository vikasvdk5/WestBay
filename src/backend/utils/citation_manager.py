"""
Citation manager for tracking and formatting sources in research reports.
Manages citation numbering, reference linking, and source attribution.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class Citation:
    """Represents a single citation/source."""
    
    def __init__(
        self,
        citation_id: int,
        source: str,
        url: Optional[str] = None,
        retrieved_at: Optional[datetime] = None,
        content_snippet: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a citation.
        
        Args:
            citation_id: Unique citation number
            source: Name or description of the source
            url: URL of the source
            retrieved_at: When the source was retrieved
            content_snippet: Brief snippet of cited content
            metadata: Additional metadata
        """
        self.citation_id = citation_id
        self.source = source
        self.url = url
        self.retrieved_at = retrieved_at or datetime.now()
        self.content_snippet = content_snippet
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary."""
        return {
            "id": self.citation_id,
            "source": self.source,
            "url": self.url,
            "retrieved_at": self.retrieved_at.isoformat() if isinstance(self.retrieved_at, datetime) else self.retrieved_at,
            "content_snippet": self.content_snippet,
            "metadata": self.metadata
        }
    
    def format(self, style: str = "numbered") -> str:
        """
        Format citation according to style.
        
        Args:
            style: Citation style (numbered, apa, mla)
            
        Returns:
            Formatted citation string
        """
        if style == "numbered":
            formatted = f"[{self.citation_id}] {self.source}"
            if self.url:
                formatted += f" - {self.url}"
            if isinstance(self.retrieved_at, datetime):
                formatted += f" (Retrieved: {self.retrieved_at.strftime('%Y-%m-%d')})"
            return formatted
        elif style == "apa":
            # Simplified APA format
            formatted = f"{self.source}."
            if self.url:
                formatted += f" Retrieved from {self.url}"
            return formatted
        else:
            return f"{self.source}"


class CitationManager:
    """
    Manages citations for research reports.
    Tracks sources, assigns citation numbers, and handles formatting.
    """
    
    def __init__(self):
        """Initialize citation manager."""
        self.citations: List[Citation] = []
        self.citation_map: Dict[str, int] = {}  # URL/source -> citation_id
        self.next_id = 1
        logger.info("Citation Manager initialized")
    
    def add_citation(
        self,
        source: str,
        url: Optional[str] = None,
        content_snippet: Optional[str] = None,
        retrieved_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a citation and return its ID.
        
        Args:
            source: Source name/description
            url: Source URL
            content_snippet: Content snippet
            retrieved_at: Retrieved timestamp
            metadata: Additional metadata
            
        Returns:
            Citation ID (1-indexed)
        """
        # Check if citation already exists
        citation_key = url or source
        if citation_key in self.citation_map:
            return self.citation_map[citation_key]
        
        # Create new citation
        citation = Citation(
            citation_id=self.next_id,
            source=source,
            url=url,
            retrieved_at=retrieved_at,
            content_snippet=content_snippet,
            metadata=metadata
        )
        
        self.citations.append(citation)
        self.citation_map[citation_key] = self.next_id
        
        logger.info(f"Added citation #{self.next_id}: {source}")
        
        self.next_id += 1
        return citation.citation_id
    
    def get_citation(self, citation_id: int) -> Optional[Citation]:
        """
        Get citation by ID.
        
        Args:
            citation_id: Citation ID
            
        Returns:
            Citation object or None
        """
        for citation in self.citations:
            if citation.citation_id == citation_id:
                return citation
        return None
    
    def get_all_citations(self) -> List[Citation]:
        """Get all citations."""
        return self.citations
    
    def format_all(self, style: str = "numbered") -> str:
        """
        Format all citations.
        
        Args:
            style: Citation style
            
        Returns:
            Formatted citations string
        """
        if not self.citations:
            return "## References\n\nNo citations available."
        
        lines = ["## References\n"]
        for citation in self.citations:
            lines.append(citation.format(style))
        
        return "\n".join(lines)
    
    def get_citations_by_ids(self, citation_ids: List[int]) -> List[Citation]:
        """
        Get multiple citations by their IDs.
        
        Args:
            citation_ids: List of citation IDs
            
        Returns:
            List of Citation objects
        """
        return [c for c in self.citations if c.citation_id in citation_ids]
    
    def save_to_file(self, filepath: Path):
        """
        Save citations to JSON file.
        
        Args:
            filepath: Path to save file
        """
        try:
            citations_data = [c.to_dict() for c in self.citations]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(citations_data, f, indent=2)
            
            logger.info(f"Citations saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving citations: {e}")
            raise
    
    def load_from_file(self, filepath: Path):
        """
        Load citations from JSON file.
        
        Args:
            filepath: Path to load from
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                citations_data = json.load(f)
            
            for data in citations_data:
                retrieved_at = data.get("retrieved_at")
                if retrieved_at:
                    retrieved_at = datetime.fromisoformat(retrieved_at)
                
                citation = Citation(
                    citation_id=data["id"],
                    source=data["source"],
                    url=data.get("url"),
                    retrieved_at=retrieved_at,
                    content_snippet=data.get("content_snippet"),
                    metadata=data.get("metadata", {})
                )
                
                self.citations.append(citation)
                citation_key = citation.url or citation.source
                self.citation_map[citation_key] = citation.citation_id
                
                if citation.citation_id >= self.next_id:
                    self.next_id = citation.citation_id + 1
            
            logger.info(f"Loaded {len(citations_data)} citations from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading citations: {e}")
            raise
    
    def clear(self):
        """Clear all citations."""
        self.citations = []
        self.citation_map = {}
        self.next_id = 1
        logger.info("Citations cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about citations.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.citations)
        with_urls = len([c for c in self.citations if c.url])
        with_snippets = len([c for c in self.citations if c.content_snippet])
        
        return {
            "total_citations": total,
            "citations_with_urls": with_urls,
            "citations_with_snippets": with_snippets,
            "percentage_with_urls": round((with_urls / total * 100) if total > 0 else 0, 1)
        }


def create_citation_manager() -> CitationManager:
    """
    Factory function to create a citation manager.
    
    Returns:
        CitationManager instance
    """
    return CitationManager()

