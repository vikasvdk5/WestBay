"""
LangSmith integration for observability and tracing of multi-agent system.
Provides tracing, logging, and monitoring of LLM calls and agent interactions.
"""

import logging
import os
from typing import Optional, Dict, Any
from functools import wraps

from langsmith import Client
from langsmith.run_helpers import traceable

from config import settings

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """Configuration and setup for LangSmith observability."""
    
    def __init__(self):
        """Initialize LangSmith configuration."""
        self.enabled = bool(settings.langsmith_api_key)
        self.client = None
        
        if self.enabled:
            self._setup_langsmith()
        else:
            logger.warning("LangSmith API key not configured. Observability disabled.")
    
    def _setup_langsmith(self):
        """Set up LangSmith client and environment variables."""
        try:
            # Set environment variables for LangChain tracing
            os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
            os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
            
            # Initialize LangSmith client
            self.client = Client(
                api_url=settings.langchain_endpoint,
                api_key=settings.langsmith_api_key
            )
            
            logger.info(f"LangSmith observability enabled for project: {settings.langsmith_project}")
            
        except Exception as e:
            logger.error(f"Error setting up LangSmith: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if LangSmith is enabled."""
        return self.enabled
    
    def get_client(self) -> Optional[Client]:
        """Get LangSmith client instance."""
        return self.client


# Global LangSmith configuration instance
_langsmith_config = LangSmithConfig()


def get_langsmith_config() -> LangSmithConfig:
    """Get the global LangSmith configuration instance."""
    return _langsmith_config


def trace_agent_call(agent_name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace agent calls with LangSmith.
    
    Args:
        agent_name: Name of the agent being traced
        metadata: Additional metadata to include in the trace
        
    Usage:
        @trace_agent_call("lead_researcher")
        def execute_agent(input_data):
            # agent logic
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if _langsmith_config.is_enabled():
                # Use LangSmith traceable decorator
                traced_func = traceable(
                    name=f"{agent_name}.{func.__name__}",
                    metadata=metadata or {},
                    tags=[agent_name, "agent_call"]
                )(func)
                return traced_func(*args, **kwargs)
            else:
                # No tracing, just execute function
                return func(*args, **kwargs)
        return wrapper
    return decorator


def trace_llm_call(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace LLM calls with LangSmith.
    
    Args:
        operation: Description of the LLM operation
        metadata: Additional metadata to include in the trace
        
    Usage:
        @trace_llm_call("generate_plan")
        def call_llm(prompt):
            # LLM call logic
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if _langsmith_config.is_enabled():
                traced_func = traceable(
                    name=f"llm.{operation}",
                    metadata=metadata or {},
                    tags=["llm_call", operation]
                )(func)
                return traced_func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def trace_tool_call(tool_name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace tool calls with LangSmith.
    
    Args:
        tool_name: Name of the tool being called
        metadata: Additional metadata to include in the trace
        
    Usage:
        @trace_tool_call("web_scraper")
        def scrape_url(url):
            # scraping logic
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if _langsmith_config.is_enabled():
                traced_func = traceable(
                    name=f"tool.{tool_name}",
                    metadata=metadata or {},
                    tags=["tool_call", tool_name]
                )(func)
                return traced_func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


class TrackedSession:
    """
    Context manager for tracking a research session with LangSmith.
    
    Usage:
        with TrackedSession("session_123", "market_research") as session:
            # agent execution
            pass
    """
    
    def __init__(
        self,
        session_id: str,
        session_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize tracked session.
        
        Args:
            session_id: Unique session identifier
            session_type: Type of session (e.g., "market_research")
            metadata: Additional session metadata
        """
        self.session_id = session_id
        self.session_type = session_type
        self.metadata = metadata or {}
        self.run_id = None
    
    def __enter__(self):
        """Start tracking session."""
        if _langsmith_config.is_enabled():
            logger.info(f"Starting tracked session: {self.session_id}")
            # Note: Actual session tracking would use LangSmith's run context
            # This is a simplified version
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracking session."""
        if _langsmith_config.is_enabled():
            logger.info(f"Ending tracked session: {self.session_id}")
        return False


def log_agent_metrics(
    agent_name: str,
    metrics: Dict[str, Any]
):
    """
    Log agent performance metrics to LangSmith.
    
    Args:
        agent_name: Name of the agent
        metrics: Dictionary of metrics to log
    """
    if _langsmith_config.is_enabled():
        try:
            logger.info(f"Agent metrics for {agent_name}: {metrics}")
            # In a full implementation, this would send metrics to LangSmith
            # For now, we just log them
        except Exception as e:
            logger.error(f"Error logging metrics for {agent_name}: {e}")


def create_feedback(
    run_id: str,
    key: str,
    score: float,
    comment: Optional[str] = None
):
    """
    Create feedback for a LangSmith run.
    
    Args:
        run_id: LangSmith run ID
        key: Feedback key (e.g., "accuracy", "helpfulness")
        score: Feedback score (typically 0-1)
        comment: Optional comment
    """
    config = get_langsmith_config()
    
    if config.is_enabled() and config.client:
        try:
            config.client.create_feedback(
                run_id=run_id,
                key=key,
                score=score,
                comment=comment
            )
            logger.info(f"Feedback created for run {run_id}: {key}={score}")
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")


# Initialize LangSmith on module import
logger.info("LangSmith observability module loaded")

