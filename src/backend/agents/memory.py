"""
Memory management module for multi-agent system.
Handles conversation history, context retrieval, and citation tracking.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import settings

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history for agents."""
    
    def __init__(self, max_messages: int = 50):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self.messages: List[BaseMessage] = []
        self.max_messages = max_messages
    
    def add_message(self, message: BaseMessage):
        """Add a message to conversation history."""
        self.messages.append(message)
        
        # Trim if exceeds max
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_human_message(self, content: str):
        """Add a human message to history."""
        self.add_message(HumanMessage(content=content))
    
    def add_ai_message(self, content: str):
        """Add an AI message to history."""
        self.add_message(AIMessage(content=content))
    
    def get_messages(self, last_n: Optional[int] = None) -> List[BaseMessage]:
        """
        Get conversation messages.
        
        Args:
            last_n: If provided, return only the last n messages
            
        Returns:
            List of messages
        """
        if last_n:
            return self.messages[-last_n:]
        return self.messages
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []
        logger.info("Conversation memory cleared")
    
    def to_dict(self) -> List[Dict[str, str]]:
        """Convert messages to dictionary format."""
        return [
            {
                "type": msg.__class__.__name__,
                "content": msg.content
            }
            for msg in self.messages
        ]


class VectorMemory:
    """Manages vector store for context retrieval."""
    
    def __init__(self, collection_name: str = "research_context"):
        """
        Initialize vector memory with embeddings.
        
        Args:
            collection_name: Name of the vector collection
        """
        self.collection_name = collection_name
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.gemini_api_key
        )
        
        # Initialize or load vector store
        persist_directory = str(Path(settings.vector_store_path) / collection_name)
        
        try:
            self.vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
            logger.info(f"Vector store initialized: {collection_name}")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """
        Add documents to vector store.
        
        Args:
            texts: List of text documents to add
            metadatas: Optional metadata for each document
        """
        try:
            self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
            logger.info(f"Added {len(texts)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def clear(self):
        """Clear all documents from the vector store."""
        try:
            self.vectorstore.delete_collection()
            logger.info(f"Vector store cleared: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")


class CitationTracker:
    """Tracks citations and sources for the research report."""
    
    def __init__(self):
        """Initialize citation tracker."""
        self.citations: List[Dict[str, Any]] = []
        self.citation_map: Dict[str, int] = {}  # URL/source -> citation number
    
    def add_citation(
        self,
        source: str,
        url: Optional[str] = None,
        content_snippet: Optional[str] = None,
        retrieved_at: Optional[datetime] = None
    ) -> int:
        """
        Add a citation and return its number.
        
        Args:
            source: Name or description of the source
            url: URL of the source (if applicable)
            content_snippet: Brief snippet of cited content
            retrieved_at: When the source was retrieved
            
        Returns:
            Citation number (1-indexed)
        """
        # Check if citation already exists
        citation_key = url or source
        if citation_key in self.citation_map:
            return self.citation_map[citation_key]
        
        # Add new citation
        citation_num = len(self.citations) + 1
        citation = {
            "number": citation_num,
            "source": source,
            "url": url,
            "content_snippet": content_snippet,
            "retrieved_at": retrieved_at or datetime.now(),
        }
        
        self.citations.append(citation)
        self.citation_map[citation_key] = citation_num
        
        logger.info(f"Added citation #{citation_num}: {source}")
        return citation_num
    
    def get_citation(self, citation_num: int) -> Optional[Dict[str, Any]]:
        """Get citation by number."""
        if 1 <= citation_num <= len(self.citations):
            return self.citations[citation_num - 1]
        return None
    
    def get_all_citations(self) -> List[Dict[str, Any]]:
        """Get all citations."""
        return self.citations
    
    def format_citations(self, style: str = "numbered") -> str:
        """
        Format citations for report.
        
        Args:
            style: Citation style ('numbered', 'apa', etc.)
            
        Returns:
            Formatted citations string
        """
        if style == "numbered":
            lines = ["## References\n"]
            for citation in self.citations:
                line = f"[{citation['number']}] {citation['source']}"
                if citation['url']:
                    line += f" - {citation['url']}"
                line += f" (Retrieved: {citation['retrieved_at'].strftime('%Y-%m-%d')})"
                lines.append(line)
            return "\n".join(lines)
        else:
            # Default to simple list
            return "\n".join([c['source'] for c in self.citations])
    
    def save_to_file(self, filepath: Path):
        """Save citations to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.citations, f, indent=2, default=str)
        logger.info(f"Citations saved to {filepath}")
    
    def clear(self):
        """Clear all citations."""
        self.citations = []
        self.citation_map = {}
        logger.info("Citations cleared")


class ResearchMemory:
    """Combined memory system for research agents."""
    
    def __init__(self, session_id: str):
        """
        Initialize research memory.
        
        Args:
            session_id: Unique identifier for this research session
        """
        self.session_id = session_id
        self.conversation = ConversationMemory()
        self.vector_memory = VectorMemory(collection_name=f"research_{session_id}")
        self.citations = CitationTracker()
        self.metadata = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "status": "active"
        }
    
    def save_session(self, output_dir: Optional[Path] = None):
        """
        Save the entire session to disk.
        
        Args:
            output_dir: Directory to save session data
        """
        if output_dir is None:
            output_dir = Path(settings.research_notes_dir) / f"session_{self.session_id}"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save conversation history
        conv_file = output_dir / "conversation.json"
        with open(conv_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversation.to_dict(), f, indent=2)
        
        # Save citations
        citations_file = output_dir / "citations.json"
        self.citations.save_to_file(citations_file)
        
        # Save metadata
        meta_file = output_dir / "metadata.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, default=str)
        
        logger.info(f"Session saved to {output_dir}")
    
    def clear_all(self):
        """Clear all memory components."""
        self.conversation.clear()
        self.vector_memory.clear()
        self.citations.clear()
        logger.info(f"All memory cleared for session {self.session_id}")

