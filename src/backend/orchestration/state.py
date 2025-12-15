"""
State management for LangGraph orchestration.
Defines the state schema and update functions for the multi-agent workflow.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from datetime import datetime
from operator import add

logger = logging.getLogger(__name__)


def take_last_status(left: str, right: str) -> str:
    """
    Reducer function for status field.
    Takes the last non-empty status value when multiple nodes update concurrently.
    """
    # If both are non-empty, prefer the rightmost (most recent)
    if right and right.strip():
        return right
    return left if left and left.strip() else right


def take_last_agent(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """
    Reducer function for current_agent field.
    Takes the last non-empty agent value when multiple nodes update concurrently.
    """
    # If both are non-empty, prefer the rightmost (most recent)
    if right:
        return right
    return left if left else right


def merge_completion_status(
    left: Optional[Dict[str, bool]], 
    right: Optional[Dict[str, bool]]
) -> Optional[Dict[str, bool]]:
    """
    Reducer function for agent_completion_status field.
    Merges completion status dictionaries from multiple concurrent updates.
    """
    # Handle None cases
    if left is None and right is None:
        return None
    if left is None:
        return right
    if right is None:
        return left
    
    # Merge dictionaries - right takes precedence for overlapping keys
    merged = left.copy()
    merged.update(right)
    return merged


class AgentState(TypedDict):
    """
    State schema for the multi-agent research workflow.
    This is the shared state that flows through the LangGraph.
    """
    
    # Input
    user_request: str
    report_requirements: Dict[str, Any]
    
    # Research Plan
    research_plan: Optional[Dict[str, Any]]
    cost_estimate: Optional[Dict[str, Any]]
    
    # Data Collection
    web_research_data: Optional[Dict[str, Any]]
    api_research_data: Optional[Dict[str, Any]]
    
    # Analysis
    analysis_results: Optional[Dict[str, Any]]
    insights: Optional[List[Dict[str, Any]]]
    visualizations: Optional[List[Dict[str, Any]]]
    
    # Report
    report_structure: Optional[Dict[str, Any]]
    llm_generated_content: Optional[Dict[str, Any]]  # Content from Straight-Through-LLM agent
    report_content: Optional[Any]  # Can be string or dict with markdown/html
    report_path: Optional[str]
    pdf_path: Optional[str]
    
    # Citations
    citations: Annotated[List[Dict[str, Any]], add]
    
    # Metadata
    session_id: str
    status: Annotated[str, take_last_status]  # Use reducer for concurrent updates
    current_agent: Annotated[Optional[str], take_last_agent]  # Use reducer for concurrent updates
    completed_tasks: Annotated[List[str], add]
    errors: Annotated[List[Dict[str, Any]], add]
    
    # Task Distribution and Completion Tracking
    agent_tasks: Optional[Dict[str, List[Dict[str, Any]]]]  # Tasks distributed to each agent
    agent_completion_status: Annotated[Optional[Dict[str, bool]], merge_completion_status]  # Track which agents have completed (merged from concurrent updates)
    required_agents: Optional[List[str]]  # List of agents that must complete before writer
    
    # Timestamps
    started_at: str
    updated_at: str


def create_initial_state(
    user_request: str,
    report_requirements: Dict[str, Any],
    session_id: str
) -> AgentState:
    """
    Create initial state for a new research session.
    
    Args:
        user_request: User's research request
        report_requirements: Report requirements specification
        session_id: Unique session identifier
        
    Returns:
        Initial AgentState
    """
    now = datetime.now().isoformat()
    
    return AgentState(
        # Input
        user_request=user_request,
        report_requirements=report_requirements,
        
        # Research Plan
        research_plan=None,
        cost_estimate=None,
        
        # Data Collection
        web_research_data=None,
        api_research_data=None,
        
        # Analysis
        analysis_results=None,
        insights=None,
        visualizations=None,
        
        # Report
        report_structure=None,
        report_content=None,
        report_path=None,
        pdf_path=None,
        
        # Citations
        citations=[],
        
        # Metadata
        session_id=session_id,
        status="initialized",
        current_agent=None,
        completed_tasks=[],
        errors=[],
        
        # Task Distribution
        agent_tasks=None,
        agent_completion_status=None,
        required_agents=None,
        
        # Timestamps
        started_at=now,
        updated_at=now
    )


def update_state_status(
    state: AgentState,
    new_status: str,
    current_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update state status and current agent.
    
    Args:
        state: Current state
        new_status: New status value
        current_agent: Currently executing agent
        
    Returns:
        Dictionary with updates to merge into state
    """
    updates = {
        "status": new_status,
        "updated_at": datetime.now().isoformat()
    }
    
    if current_agent:
        updates["current_agent"] = current_agent
    
    return updates


def mark_task_completed(
    state: AgentState,
    task_id: str
) -> Dict[str, Any]:
    """
    Mark a task as completed.
    
    Args:
        state: Current state
        task_id: ID of completed task
        
    Returns:
        Dictionary with updates to merge into state
    """
    return {
        "completed_tasks": [task_id],
        "updated_at": datetime.now().isoformat()
    }


def add_error(
    state: AgentState,
    agent_name: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add an error to the state.
    
    Args:
        state: Current state
        agent_name: Name of agent that encountered the error
        error_message: Error message
        error_details: Optional additional error details
        
    Returns:
        Dictionary with updates to merge into state
    """
    error_record = {
        "agent": agent_name,
        "message": error_message,
        "details": error_details or {},
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "errors": [error_record],
        "updated_at": datetime.now().isoformat()
    }


def validate_state(state: AgentState) -> bool:
    """
    Validate that the state has required fields.
    
    Args:
        state: State to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["user_request", "session_id", "status"]
    
    for field in required_fields:
        if field not in state or state[field] is None:
            logger.error(f"State missing required field: {field}")
            return False
    
    return True


class StateManager:
    """Manager for state operations and validation with persistence."""
    
    def __init__(self, persistence_file: Optional[Path] = None):
        """
        Initialize state manager with optional persistence.
        
        Args:
            persistence_file: Path to file for persisting states
        """
        self.states: Dict[str, AgentState] = {}
        
        # Set up persistence
        if persistence_file is None:
            from config import settings
            
            # Derive data directory from reports_dir (./data/reports -> ./data)
            reports_path = Path(settings.reports_dir)
            data_dir = reports_path.parent
            self.persistence_file = data_dir / "sessions" / "states.json"
        else:
            self.persistence_file = persistence_file
        
        # Ensure directory exists
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing states
        self._load_states()
        
        logger.info(f"State Manager initialized with persistence at {self.persistence_file}")
    
    def _load_states(self):
        """Load states from persistence file."""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    self.states = data
                logger.info(f"Loaded {len(self.states)} states from persistence")
            else:
                logger.info("No existing states found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading states: {e}")
            self.states = {}
    
    def _save_states(self):
        """Save states to persistence file."""
        try:
            with open(self.persistence_file, 'w') as f:
                json.dump(self.states, f, indent=2, default=str)
            logger.debug(f"Saved {len(self.states)} states to persistence")
        except Exception as e:
            logger.error(f"Error saving states: {e}")
    
    def create_state(
        self,
        user_request: str,
        report_requirements: Dict[str, Any],
        session_id: str
    ) -> AgentState:
        """
        Create and store a new state.
        
        Args:
            user_request: User's request
            report_requirements: Report requirements
            session_id: Session identifier
            
        Returns:
            Created state
        """
        state = create_initial_state(user_request, report_requirements, session_id)
        self.states[session_id] = state
        self._save_states()  # Persist immediately
        logger.info(f"Created state for session: {session_id}")
        return state
    
    def get_state(self, session_id: str) -> Optional[AgentState]:
        """Get state by session ID."""
        return self.states.get(session_id)
    
    def update_state(self, session_id: str, updates: Dict[str, Any]):
        """
        Update state with new values.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply
        """
        if session_id in self.states:
            self.states[session_id].update(updates)
            self.states[session_id]["updated_at"] = datetime.now().isoformat()
            self._save_states()  # Persist immediately
            logger.debug(f"Updated state for session: {session_id}")
    
    def delete_state(self, session_id: str):
        """Delete state by session ID."""
        if session_id in self.states:
            del self.states[session_id]
            self._save_states()  # Persist immediately
            logger.info(f"Deleted state for session: {session_id}")
    
    def list_sessions(self) -> List[str]:
        """Get list of all session IDs."""
        return list(self.states.keys())
    
    def cleanup_old_sessions(self, days: int = 7):
        """
        Clean up sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        to_delete = []
        for session_id, state in self.states.items():
            try:
                updated_at = datetime.fromisoformat(state.get("updated_at", ""))
                if updated_at < cutoff:
                    to_delete.append(session_id)
            except (ValueError, TypeError):
                pass
        
        for session_id in to_delete:
            self.delete_state(session_id)
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old sessions")


# Global state manager instance
_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    return _state_manager

