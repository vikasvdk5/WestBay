"""
FastAPI routes for the multi-agent market research system.
Provides endpoints for report generation, cost estimation, and status tracking.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from orchestration.graph_builder import create_workflow
from agents.specialized.cost_calculator import CostCalculatorAgent
from orchestration.state import get_state_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global workflow instance
workflow = create_workflow()

# Global state manager
state_manager = get_state_manager()


# Request/Response models
class ReportRequirements(BaseModel):
    """Report requirements specification."""
    topic: str = Field(..., description="Research topic")
    page_count: int = Field(default=10, ge=1, le=101, description="Number of pages")
    source_count: int = Field(default=4, ge=0, le=31, description="Number of sources")
    complexity: str = Field(default="medium", pattern="^(simple|medium|complex)$")
    include_analysis: bool = Field(default=True, description="Include analysis")
    include_visualizations: bool = Field(default=True, description="Include visualizations")
    urls: list[str] = Field(default_factory=list, description="Specific URLs to scrape")
    api_requests: list[Dict[str, Any]] = Field(default_factory=list, description="API requests to make")


class SubmitRequirementsRequest(BaseModel):
    """Request model for submitting report requirements."""
    user_request: str = Field(..., description="User's research request")
    requirements: ReportRequirements = Field(..., description="Report requirements")


class SubmitRequirementsResponse(BaseModel):
    """Response model for submitting report requirements."""
    session_id: str
    status: str
    message: str
    summarized_requirement: str
    estimated_completion_time: str


class CostEstimateResponse(BaseModel):
    """Response model for cost estimate."""
    session_id: str
    total_tokens: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    min_cost_usd: float
    max_cost_usd: float
    budget_status: str
    agent_breakdown: Dict[str, Dict[str, Any]]
    recommendations: list[str]


class ReportStructureResponse(BaseModel):
    """Response model for report structure preview."""
    session_id: str
    sections: list[Dict[str, Any]]
    estimated_pages: int
    ready_for_generation: bool


class GenerateReportRequest(BaseModel):
    """Request model for generating report."""
    session_id: str
    confirmed_structure: Optional[list[Dict[str, Any]]] = None


class GenerateReportResponse(BaseModel):
    """Response model for report generation."""
    session_id: str
    status: str
    message: str
    progress: int


class ReportStatusResponse(BaseModel):
    """Response model for report status."""
    session_id: str
    status: str
    current_agent: Optional[str]
    completed_tasks: list[str]
    total_tasks: int
    progress: int
    report_path: Optional[str]
    errors: list[Dict[str, Any]]


# Routes
@router.post("/submit-requirements", response_model=SubmitRequirementsResponse)
async def submit_requirements(request: SubmitRequirementsRequest):
    """
    Submit report requirements and get initial analysis.
    
    This endpoint:
    1. Creates a new session
    2. Analyzes the user request
    3. Returns summarized requirements
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create initial state
        state_manager.create_state(
            user_request=request.user_request,
            report_requirements=request.requirements.model_dump(),
            session_id=session_id
        )
        
        # Summarize requirements using LLM (simplified version)
        summarized = f"Market research report on '{request.requirements.topic}' "
        summarized += f"with {request.requirements.page_count} pages, "
        summarized += f"{request.requirements.source_count} sources, "
        summarized += f"{request.requirements.complexity} complexity."
        
        if request.requirements.include_analysis:
            summarized += " Includes detailed analysis."
        if request.requirements.include_visualizations:
            summarized += " Includes data visualizations."
        
        # Estimate completion time (simplified)
        estimated_time = "15-30 minutes"
        if request.requirements.complexity == "complex":
            estimated_time = "30-45 minutes"
        
        logger.info(f"Requirements submitted for session: {session_id}")
        
        return SubmitRequirementsResponse(
            session_id=session_id,
            status="requirements_received",
            message="Requirements successfully submitted",
            summarized_requirement=summarized,
            estimated_completion_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Error submitting requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-estimate/{session_id}", response_model=CostEstimateResponse)
async def get_cost_estimate(session_id: str):
    """
    Get cost estimate for report generation.
    
    This endpoint calculates expected token usage and costs before starting.
    """
    try:
        # Get state
        state = state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate cost estimate
        cost_calculator = CostCalculatorAgent()
        result = cost_calculator.execute(
            report_requirements=state["report_requirements"]
        )
        
        cost_est = result["cost_estimate"]
        token_est = result["token_estimate"]
        agent_breakdown = result["agent_breakdown"]
        budget_assessment = result["budget_assessment"]
        recommendations = result["recommendations"]
        
        logger.info(f"Cost estimate calculated for session: {session_id}")
        
        return CostEstimateResponse(
            session_id=session_id,
            total_tokens=token_est["total_tokens"],
            input_tokens=token_est["input_tokens"],
            output_tokens=token_est["output_tokens"],
            total_cost_usd=cost_est["total_cost_usd"],
            min_cost_usd=cost_est["min_cost_usd"],
            max_cost_usd=cost_est["max_cost_usd"],
            budget_status=budget_assessment["status"],
            agent_breakdown=agent_breakdown,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating cost estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview-structure/{session_id}", response_model=ReportStructureResponse)
async def get_report_structure(session_id: str):
    """
    Get report structure preview.
    
    Returns the planned structure of the report for user review.
    """
    try:
        # Get state
        state = state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate structure (simplified)
        sections = [
            {
                "id": "executive_summary",
                "title": "Executive Summary",
                "confidence": 0.85,
                "editable": True
            },
            {
                "id": "market_overview",
                "title": "Market Overview",
                "confidence": 0.90,
                "editable": True
            },
            {
                "id": "key_findings",
                "title": "Key Findings",
                "confidence": 0.80,
                "editable": True
            },
            {
                "id": "analysis",
                "title": "Detailed Analysis",
                "confidence": 0.85,
                "editable": True
            },
            {
                "id": "recommendations",
                "title": "Recommendations",
                "confidence": 0.75,
                "editable": True
            }
        ]
        
        requirements = state["report_requirements"]
        estimated_pages = requirements.get("page_count", 20)
        
        logger.info(f"Structure preview generated for session: {session_id}")
        
        return ReportStructureResponse(
            session_id=session_id,
            sections=sections,
            estimated_pages=estimated_pages,
            ready_for_generation=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Start report generation process.
    
    This endpoint initiates the multi-agent workflow in the background.
    """
    try:
        # Get state
        state = state_manager.get_state(request.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update state
        state_manager.update_state(request.session_id, {
            "status": "generating",
            "current_agent": "lead_researcher"
        })
        
        # Start background task for report generation
        background_tasks.add_task(
            _generate_report_background,
            request.session_id,
            state["user_request"],
            state["report_requirements"]
        )
        
        logger.info(f"Report generation started for session: {request.session_id}")
        
        return GenerateReportResponse(
            session_id=request.session_id,
            status="generating",
            message="Report generation started",
            progress=5
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting report generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/workflow-state/{session_id}")
async def get_workflow_debug_state(session_id: str):
    """
    Debug endpoint to get detailed workflow state information.
    Useful for troubleshooting stuck workflows.
    """
    try:
        state = state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "status": state.get("status"),
            "current_agent": state.get("current_agent"),
            "completed_tasks": state.get("completed_tasks", []),
            "required_agents": state.get("required_agents", []),
            "agent_completion_status": state.get("agent_completion_status", {}),
            "agent_tasks": state.get("agent_tasks", {}),
            "has_report_structure": state.get("report_structure") is not None,
            "has_web_data": state.get("web_research_data") is not None,
            "has_api_data": state.get("api_research_data") is not None,
            "has_analysis": state.get("analysis_results") is not None,
            "has_report": state.get("report_path") is not None,
            "errors": state.get("errors", []),
            "started_at": state.get("started_at"),
            "updated_at": state.get("updated_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debug state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions.
    
    Returns list of session IDs and their status.
    """
    try:
        sessions = []
        for session_id in state_manager.list_sessions():
            state = state_manager.get_state(session_id)
            if state:
                sessions.append({
                    "session_id": session_id,
                    "status": state.get("status"),
                    "topic": state.get("report_requirements", {}).get("topic", "Unknown"),
                    "started_at": state.get("started_at"),
                    "updated_at": state.get("updated_at")
                })
        
        return {
            "total_sessions": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report-status/{session_id}", response_model=ReportStatusResponse)
async def get_report_status(session_id: str):
    """
    Get current status of report generation.
    
    Returns progress, current agent, and completion status.
    """
    try:
        # Get state
        state = state_manager.get_state(session_id)
        if not state:
            # Provide helpful error message
            available_sessions = state_manager.list_sessions()
            raise HTTPException(
                status_code=404, 
                detail=f"Session '{session_id}' not found. Available sessions: {len(available_sessions)}"
            )
        
        # Calculate progress
        total_tasks = 6  # cost, plan, collect, api, analyze, write
        completed = len(state.get("completed_tasks", []))
        progress = int((completed / total_tasks) * 100)
        
        return ReportStatusResponse(
            session_id=session_id,
            status=state.get("status", "unknown"),
            current_agent=state.get("current_agent"),
            completed_tasks=state.get("completed_tasks", []),
            total_tasks=total_tasks,
            progress=progress,
            report_path=state.get("report_path"),
            errors=state.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{session_id}")
async def get_report(session_id: str):
    """
    Get the generated report.
    
    Returns the completed report content and metadata.
    """
    try:
        # Get state
        state = state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if state.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Report not yet completed")
        
        # Get report content - prefer HTML version
        report_content = state.get("report_content")
        
        # Check if we have HTML report
        report_html = None
        if isinstance(report_content, dict) and "report_html" in report_content:
            report_html = report_content["report_html"]
        elif isinstance(report_content, str):
            report_html = report_content
        
        return {
            "session_id": session_id,
            "status": "completed",
            "report_content": state.get("report_content"),
            "report_html": report_html,
            "report_path": state.get("report_path"),
            "pdf_path": state.get("pdf_path"),
            "citations": state.get("citations", []),
            "visualizations": state.get("visualizations", []),
            "generated_at": state.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{session_id}/pdf")
async def download_pdf(session_id: str):
    """
    Download the report as PDF.
    
    Returns PDF file for download.
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    try:
        # Get state
        state = state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if state.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Report not yet completed")
        
        # Get PDF path
        pdf_path = state.get("pdf_path")
        
        if not pdf_path or not Path(pdf_path).exists():
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"research_report_{session_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task function
async def _generate_report_background(
    session_id: str,
    user_request: str,
    report_requirements: Dict[str, Any]
):
    """
    Background task for report generation.
    
    This runs the full multi-agent workflow asynchronously.
    """
    try:
        logger.info(f"Background report generation started for: {session_id}")
        
        # Execute workflow
        final_state = workflow.execute(
            user_request=user_request,
            report_requirements=report_requirements,
            session_id=session_id
        )
        
        # Update state with results
        state_manager.update_state(session_id, final_state)
        
        logger.info(f"Background report generation completed for: {session_id}")
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in background report generation: {e}")
        logger.error(f"Traceback: {error_trace}")
        
        # Update state with detailed error
        state_manager.update_state(session_id, {
            "status": "error",
            "current_agent": "workflow",
            "errors": [{
                "agent": "workflow",
                "message": str(e),
                "traceback": error_trace,
                "timestamp": datetime.now().isoformat()
            }]
        })

