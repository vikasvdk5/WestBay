"""
LangGraph workflow builder for multi-agent orchestration.
Creates and compiles the LangGraph with proper routing and conditional edges.
"""

import logging
from typing import Literal, Dict, Any, List, cast
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from orchestration.state import AgentState, update_state_status, mark_task_completed
from agents.specialized.lead_researcher import LeadResearcherAgent
from agents.specialized.synthesizer import SynthesizerAgent
from agents.specialized.data_collector import DataCollectorAgent
from agents.specialized.api_researcher import APIResearcherAgent
from agents.specialized.analyst import AnalystAgent
from agents.specialized.straight_through_llm import StraightThroughLLMAgent
from agents.specialized.writer import WriterAgent
from agents.specialized.cost_calculator import CostCalculatorAgent
from utils.contribution_tracker import create_contribution_tracker, get_contribution_tracker

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """
    Multi-agent workflow orchestrator using LangGraph.
    Coordinates specialized agents for market research report generation.
    """
    
    def __init__(self):
        """Initialize the multi-agent workflow."""
        # Initialize agents
        self.lead_researcher = LeadResearcherAgent()
        self.synthesizer = SynthesizerAgent()
        self.data_collector = DataCollectorAgent()
        self.api_researcher = APIResearcherAgent()
        self.analyst = AnalystAgent()
        self.straight_through_llm = StraightThroughLLMAgent()
        self.writer = WriterAgent()
        self.cost_calculator = CostCalculatorAgent()
        
        # Build graph
        self.graph = self._build_graph()
        
        logger.info("Multi-Agent Workflow initialized with 8 specialized agents")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph with state schema
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("cost_calculator", self._cost_calculator_node)
        workflow.add_node("lead_researcher", self._lead_researcher_node)
        workflow.add_node("synthesizer", self._synthesizer_node)  # Report structure synthesis (runs first)
        workflow.add_node("data_collector", self._data_collector_node)
        workflow.add_node("api_researcher", self._api_researcher_node)
        workflow.add_node("analyst", self._analyst_node)
        workflow.add_node("straight_through_llm", self._straight_through_llm_node)  # Direct LLM content generation
        workflow.add_node("check_completion", self._check_completion_node)  # Check if all agents completed
        workflow.add_node("writer", self._writer_node)
        
        # Add edges - Updated workflow with proper parallel execution handling
        # Flow: START → cost → lead → synthesizer → (parallel: data, api, analyst) → check_completion → writer → END
        # Writer only starts after all parallel agents complete
        workflow.add_edge(START, "cost_calculator")
        workflow.add_conditional_edges(
            "cost_calculator",
            self._route_after_cost_estimate,
            {
                "proceed": "lead_researcher",
                "high_cost": END
            }
        )
        workflow.add_edge("lead_researcher", "synthesizer")  # Lead → Synthesizer (structure creation)
        
        # Synthesizer completes structure, then triggers execution of agents
        # Execute agents sequentially - they update completion status independently
        # After all agents execute, check completion and route to writer
        workflow.add_edge("synthesizer", "data_collector")   # Start data collection
        
        # Route from data_collector based on whether API researcher is needed
        workflow.add_conditional_edges(
            "data_collector",
            self._route_after_data_collector,
            {
                "to_api": "api_researcher",
                "to_analyst": "analyst",
                "to_llm": "straight_through_llm",
                "to_check": "check_completion"
            }
        )
        
        # Route from api_researcher to analyst, llm, or check
        workflow.add_conditional_edges(
            "api_researcher",
            self._route_after_api_researcher,
            {
                "to_analyst": "analyst",
                "to_llm": "straight_through_llm",
                "to_check": "check_completion"
            }
        )
        
        # Route from analyst to llm or check
        workflow.add_conditional_edges(
            "analyst",
            self._route_after_analyst,
            {
                "to_llm": "straight_through_llm",
                "to_check": "check_completion"
            }
        )
        
        # Straight-through-LLM always goes to check_completion
        workflow.add_edge("straight_through_llm", "check_completion")
        
        # Completion checker routes to writer if all done, else there's an error
        workflow.add_conditional_edges(
            "check_completion",
            self._route_after_completion_check,
            {
                "all_complete": "writer",
                "incomplete": END  # Should not happen if agents executed sequentially
            }
        )
        
        workflow.add_edge("writer", END)
        
        # Compile with memory
        memory = MemorySaver()
        compiled_graph = workflow.compile(checkpointer=memory)
        
        logger.info("LangGraph workflow compiled")
        return compiled_graph
    
    # Node implementations
    def _cost_calculator_node(self, state: AgentState) -> Dict[str, Any]:
        """Cost calculator node."""
        logger.info("Executing cost_calculator node")
        
        try:
            result = self.cost_calculator.execute(
                report_requirements=state["report_requirements"]
            )
            
            return {
                "cost_estimate": result,
                "status": "cost_estimated",
                "current_agent": "cost_calculator",
                "completed_tasks": ["cost_estimation"]
            }
            
        except Exception as e:
            logger.error(f"Error in cost_calculator node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "cost_calculator",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _lead_researcher_node(self, state: AgentState) -> Dict[str, Any]:
        """Lead researcher node - Orchestration and strategy."""
        logger.info("=" * 80)
        logger.info("🎯 NODE: Lead Researcher (Orchestration & Strategy)")
        logger.info("=" * 80)
        
        try:
            # Get tracker from registry (not from state - state must be serializable)
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            result = self.lead_researcher.execute(
                user_request=state["user_request"],
                context={
                    "cost_estimate": state.get("cost_estimate"),
                    "report_requirements": state.get("report_requirements"),
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            # Extract task distribution from research plan
            research_plan = result.get("research_plan", {})
            research_strategy = result.get("research_strategy", {})
            
            # Distribute tasks to agents based on strategy
            agent_tasks = self._distribute_tasks_to_agents(research_plan, research_strategy)
            
            # Determine which agents are required (will be used for completion checking)
            required_agents = []
            if research_strategy.get("agent_breakdown", {}).get("data_collectors", 0) > 0:
                required_agents.append("data_collector")
            if research_strategy.get("agent_breakdown", {}).get("api_researchers", 0) > 0:
                required_agents.append("api_researcher")
            if research_strategy.get("agent_breakdown", {}).get("analysts", 0) > 0:
                required_agents.append("analyst")
            
            # ALWAYS include straight_through_llm - guaranteed content generation
            required_agents.append("straight_through_llm")
            
            # Initialize completion status
            agent_completion_status = {agent: False for agent in required_agents}
            
            logger.info("✅ Lead Researcher completed - Strategy created")
            logger.info(f"   Task distribution: {len(agent_tasks)} agent groups")
            logger.info(f"   Required agents: {required_agents}")
            
            return {
                "research_plan": research_plan,
                "status": "strategy_created",
                "current_agent": "lead_researcher",
                "completed_tasks": ["research_strategy"],
                "agent_tasks": agent_tasks,
                "required_agents": required_agents,
                "agent_completion_status": agent_completion_status
            }
            
        except Exception as e:
            logger.error(f"❌ Error in lead_researcher node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "lead_researcher",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _distribute_tasks_to_agents(
        self,
        research_plan: Dict[str, Any],
        research_strategy: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Distribute tasks from research plan to specific agents.
        
        Args:
            research_plan: Research plan with subtasks
            research_strategy: Strategy with agent allocations
            
        Returns:
            Dictionary mapping agent names to their assigned tasks
        """
        agent_tasks = {
            "data_collector": [],
            "api_researcher": [],
            "analyst": [],
            "straight_through_llm": []  # Always gets the full report structure
        }
        
        # Get subtasks from research plan
        subtasks = research_plan.get("subtasks", [])
        
        # Distribute tasks based on agent_type in subtasks
        for task in subtasks:
            agent_type = task.get("agent_type", "").lower()
            if "data_collector" in agent_type or "researcher" in agent_type:
                agent_tasks["data_collector"].append(task)
            elif "api" in agent_type:
                agent_tasks["api_researcher"].append(task)
            elif "analyst" in agent_type or "analysis" in agent_type:
                agent_tasks["analyst"].append(task)
        
        # If no tasks distributed, assign based on strategy
        if not any(agent_tasks.values()):
            strategy_breakdown = research_strategy.get("agent_breakdown", {})
            if strategy_breakdown.get("data_collectors", 0) > 0:
                agent_tasks["data_collector"] = [{"description": "Web research and data collection"}]
            if strategy_breakdown.get("api_researchers", 0) > 0:
                agent_tasks["api_researcher"] = [{"description": "API data collection"}]
            if strategy_breakdown.get("analysts", 0) > 0:
                agent_tasks["analyst"] = [{"description": "Data analysis and visualization"}]
        
        # ALWAYS assign straight_through_llm task - guaranteed content generation
        agent_tasks["straight_through_llm"] = [{
            "description": "Generate comprehensive report content using LLM foundational knowledge",
            "priority": "high",
            "always_execute": True
        }]
        
        return agent_tasks
    
    def _synthesizer_node(self, state: AgentState) -> Dict[str, Any]:
        """Synthesizer node - Dynamic report structure generation."""
        logger.info("=" * 80)
        logger.info("📝 NODE: Synthesizer (Report Structure Generation)")
        logger.info("=" * 80)
        
        try:
            # Get tracker from registry
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            # Extract topic and requirements
            report_reqs = state.get("report_requirements", {})
            topic = report_reqs.get("topic", state.get("user_request", "Unknown"))
            detailed_requirements = state.get("user_request", "")
            
            logger.info(f"Creating dynamic report structure for: {topic}")
            
            result = self.synthesizer.execute(
                topic=topic,
                detailed_requirements=detailed_requirements,
                context={
                    "report_requirements": report_reqs,
                    "research_plan": state.get("research_plan"),
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            report_structure = result.get("report_structure", {})
            total_sections = report_structure.get("total_sections", 0)
            dynamic_sections = report_structure.get("dynamic_sections", 0)
            
            logger.info(f"✅ Synthesizer completed - {total_sections} sections created ({dynamic_sections} dynamic)")
            
            return {
                "report_structure": report_structure,
                "status": "structure_created",
                "current_agent": "synthesizer",
                "completed_tasks": ["report_structure_synthesis"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error in synthesizer node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "synthesizer",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _data_collector_node(self, state: AgentState) -> Dict[str, Any]:
        """Data collector node - Web scraping and data collection."""
        logger.info("=" * 80)
        logger.info("🌐 NODE: Data Collector (Web Research)")
        logger.info("=" * 80)
        
        try:
            # Get session ID and tracker
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            # Get assigned tasks from lead researcher
            agent_tasks = state.get("agent_tasks", {})
            assigned_tasks = agent_tasks.get("data_collector", [])
            
            # Extract URLs from report requirements or use defaults
            urls = state["report_requirements"].get("urls", [
                "https://example.com/market-data"
            ])
            topic = state["user_request"]
            
            logger.info(f"Collecting web research data for: {topic}")
            logger.info(f"Assigned tasks: {len(assigned_tasks)}")
            logger.info(f"URLs to scrape: {len(urls)}")
            
            result = self.data_collector.execute(
                urls=urls,
                topic=topic,
                context={
                    "assigned_tasks": assigned_tasks,
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            logger.info(f"✅ Data Collector completed - Collected data from {len(urls)} sources")
            
            # Mark this agent as complete
            completion_status = state.get("agent_completion_status", {}).copy()
            completion_status["data_collector"] = True
            
            return {
                "web_research_data": result,
                "citations": result.get("citations", []),
                "status": "web_research_complete",
                "current_agent": "data_collector",
                "completed_tasks": ["web_data_collection"],
                "agent_completion_status": completion_status
            }
            
        except Exception as e:
            logger.error(f"❌ Error in data_collector node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "data_collector",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _api_researcher_node(self, state: AgentState) -> Dict[str, Any]:
        """API researcher node - External API data collection."""
        logger.info("=" * 80)
        logger.info("🔌 NODE: API Researcher (External Data Collection)")
        logger.info("=" * 80)
        
        try:
            # Get session ID and tracker
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            # Get assigned tasks from lead researcher
            agent_tasks = state.get("agent_tasks", {})
            assigned_tasks = agent_tasks.get("api_researcher", [])
            
            # Extract API requests from report requirements
            api_requests = state["report_requirements"].get("api_requests", [])
            topic = state["user_request"]
            
            if not api_requests:
                logger.info("ℹ️  No API requests specified, skipping API research")
                # Mark as complete even if skipped
                completion_status = state.get("agent_completion_status", {}).copy()
                completion_status["api_researcher"] = True
                return {
                    "api_research_data": {"status": "skipped"},
                    "status": "api_research_skipped",
                    "current_agent": "api_researcher",
                    "completed_tasks": ["api_data_collection"],
                    "agent_completion_status": completion_status
                }
            
            logger.info(f"Collecting API data for: {topic}")
            logger.info(f"Assigned tasks: {len(assigned_tasks)}")
            logger.info(f"API requests to process: {len(api_requests)}")
            
            result = self.api_researcher.execute(
                api_requests=api_requests,
                topic=topic,
                context={
                    "assigned_tasks": assigned_tasks,
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            logger.info(f"✅ API Researcher completed - Processed {len(api_requests)} API requests")
            
            # Mark this agent as complete
            completion_status = state.get("agent_completion_status", {}).copy()
            completion_status["api_researcher"] = True
            
            return {
                "api_research_data": result,
                "citations": result.get("citations", []),
                "status": "api_research_complete",
                "current_agent": "api_researcher",
                "completed_tasks": ["api_data_collection"],
                "agent_completion_status": completion_status
            }
            
        except Exception as e:
            logger.error(f"Error in api_researcher node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "api_researcher",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _analyst_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyst node - Data analysis and visualization generation."""
        logger.info("=" * 80)
        logger.info("📊 NODE: Analyst (Data Analysis & Visualizations)")
        logger.info("=" * 80)
        
        try:
            # Get session ID and tracker
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            # Get assigned tasks from lead researcher
            agent_tasks = state.get("agent_tasks", {})
            assigned_tasks = agent_tasks.get("analyst", [])
            
            # Combine research data
            research_data = {
                "web_data": state.get("web_research_data"),
                "api_data": state.get("api_research_data"),
                "data_sources": []
            }
            
            topic = state["user_request"]
            report_reqs = state.get("report_requirements", {})
            
            logger.info(f"Analyzing data for: {topic}")
            logger.info(f"Assigned tasks: {len(assigned_tasks)}")
            logger.info(f"Analysis requested: {report_reqs.get('include_analysis', True)}")
            logger.info(f"Visualizations requested: {report_reqs.get('include_visualizations', True)}")
            
            result = self.analyst.execute(
                research_data=research_data,
                topic=topic,
                context={
                    "assigned_tasks": assigned_tasks,
                    "report_requirements": report_reqs,
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            visualizations = result.get("visualizations", [])
            insights = result.get("insights", [])
            
            logger.info(f"✅ Analyst completed - Generated {len(insights)} insights, {len(visualizations)} visualizations")
            
            # Mark this agent as complete
            completion_status = state.get("agent_completion_status", {}).copy()
            completion_status["analyst"] = True
            
            return {
                "analysis_results": result.get("analysis"),
                "insights": insights,
                "visualizations": visualizations,
                "status": "analysis_complete",
                "current_agent": "analyst",
                "completed_tasks": ["data_analysis"],
                "agent_completion_status": completion_status
            }
            
        except Exception as e:
            logger.error(f"❌ Error in analyst node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "analyst",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _straight_through_llm_node(self, state: AgentState) -> Dict[str, Any]:
        """Straight-Through-LLM node - Direct content generation using LLM foundational knowledge."""
        logger.info("=" * 80)
        logger.info("🤖 NODE: Straight-Through-LLM (Direct Content Generation)")
        logger.info("=" * 80)
        
        try:
            # Get session ID and tracker
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            # Get inputs
            report_structure = state.get("report_structure")
            user_requirements = state.get("report_requirements")
            
            if not report_structure:
                logger.error("No report structure available - Synthesizer must run first!")
                raise ValueError("report_structure is required from Synthesizer")
            
            # Collect any available research data (optional - agent works without it)
            research_data = {
                "web_data": state.get("web_research_data"),
                "api_data": state.get("api_research_data"),
                "analysis": state.get("analysis_results")
            }
            
            topic = user_requirements.get("topic", "Unknown")
            sections_count = len(report_structure.get("sections", []))
            
            logger.info(f"Generating comprehensive content for: {topic[:80]}")
            logger.info(f"Report structure: {sections_count} sections")
            logger.info(f"Page count target: {user_requirements.get('page_count', 10)}")
            logger.info(f"Complexity: {user_requirements.get('complexity', 'medium')}")
            
            result = self.straight_through_llm.execute(
                report_structure=report_structure,
                user_requirements=user_requirements,
                research_data=research_data,
                context={
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            sections_generated = result.get("sections_generated", 0)
            total_words = result.get("total_word_count", 0)
            
            logger.info(f"✅ Straight-Through-LLM completed - Generated {sections_generated} sections, {total_words} words")
            
            # Mark this agent as complete
            completion_status = state.get("agent_completion_status", {}).copy()
            completion_status["straight_through_llm"] = True
            
            return {
                "llm_generated_content": result,
                "status": "llm_content_complete",
                "current_agent": "straight_through_llm",
                "completed_tasks": ["llm_content_generation"],
                "agent_completion_status": completion_status
            }
            
        except Exception as e:
            logger.error(f"❌ Error in straight_through_llm node: {e}")
            # Even on error, mark as complete to not block workflow
            completion_status = state.get("agent_completion_status", {}).copy()
            completion_status["straight_through_llm"] = True
            return {
                "status": "error",
                "agent_completion_status": completion_status,
                "errors": [{
                    "agent": "straight_through_llm",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _writer_node(self, state: AgentState) -> Dict[str, Any]:
        """Writer node - Final report generation (Markdown, HTML, PDF).
        
        This node only executes after ALL parallel agents (data_collector, api_researcher, analyst)
        have completed their tasks. The dependency is enforced by conditional routing.
        """
        logger.info("=" * 80)
        logger.info("✍️  NODE: Writer (Report Generation)")
        logger.info("=" * 80)
        logger.info("✅ All parallel agents have completed - Starting final report synthesis")
        
        # Verify all agents completed
        required_agents = state.get("required_agents", [])
        completion_status = state.get("agent_completion_status", {})
        logger.info(f"   Required agents: {required_agents}")
        logger.info(f"   All completed: {all(completion_status.get(agent, False) for agent in required_agents)}")
        
        try:
            # Get report structure from Synthesizer (or use fallback)
            report_structure = state.get("report_structure")
            if not report_structure:
                logger.warning("No report structure from Synthesizer, using default structure")
                report_structure = {
                    "sections": [
                        {"id": "executive_summary", "title": "Executive Summary"},
                        {"id": "market_overview", "title": "Market Overview"},
                        {"id": "key_findings", "title": "Key Findings"}
                    ]
                }
            else:
                total_sections = report_structure.get("total_sections", 0)
                logger.info(f"Using Synthesizer structure with {total_sections} sections")
            
            research_findings = {
                "web_data": state.get("web_research_data"),
                "api_data": state.get("api_research_data"),
                "llm_content": state.get("llm_generated_content")  # Content from Straight-Through-LLM
            }
            
            analysis_results = state.get("analysis_results")
            citations = state.get("citations", [])
            
            logger.info(f"Generating report for: {state['user_request'][:80]}...")
            logger.info(f"   Report structure: {report_structure is not None} (sections: {len(report_structure.get('sections', [])) if report_structure else 0})")
            logger.info(f"   Research findings: web_data={research_findings.get('web_data') is not None}, api_data={research_findings.get('api_data') is not None}")
            logger.info(f"   Analysis results: {analysis_results is not None}")
            logger.info(f"   Citations count: {len(citations)}")
            
            # Get session ID and tracker
            session_id = state.get("session_id")
            tracker = get_contribution_tracker(session_id) if session_id else None
            
            result = self.writer.execute(
                report_structure=report_structure,
                research_findings=research_findings,
                analysis_results=analysis_results or {},  # Ensure not None
                citations=citations,
                context={
                    "topic": state["user_request"],
                    "report_requirements": state.get("report_requirements", {}),
                    "contribution_tracker": tracker,
                    "session_id": session_id
                }
            )
            
            logger.info(f"✅ Writer completed - Report generated (MD + HTML + PDF)")
            logger.info(f"   Report path: {result.get('report_path')}")
            logger.info(f"   PDF path: {result.get('pdf_path')}")
            
            return {
                "report_content": {
                    "markdown": result.get("report"),
                    "html": result.get("report_html")
                },
                "report_path": result.get("report_path"),
                "pdf_path": result.get("pdf_path"),
                "status": "completed",
                "current_agent": "writer",
                "completed_tasks": ["report_writing"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error in writer node: {e}")
            return {
                "status": "error",
                "errors": [{
                    "agent": "writer",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _route_after_data_collector(self, state: AgentState) -> Literal["to_api", "to_analyst", "to_llm", "to_check"]:
        """Route after data collector - determine next agent based on requirements."""
        required_agents = state.get("required_agents", [])
        completion_status = state.get("agent_completion_status", {})
        
        if "api_researcher" in required_agents and not completion_status.get("api_researcher", False):
            logger.info("   → Routing to API Researcher")
            return "to_api"
        elif "analyst" in required_agents and not completion_status.get("analyst", False):
            logger.info("   → Routing to Analyst")
            return "to_analyst"
        elif "straight_through_llm" in required_agents and not completion_status.get("straight_through_llm", False):
            logger.info("   → Routing to Straight-Through-LLM")
            return "to_llm"
        else:
            logger.info("   → All agents complete, routing to completion check")
            return "to_check"
    
    def _route_after_api_researcher(self, state: AgentState) -> Literal["to_analyst", "to_llm", "to_check"]:
        """Route after API researcher - go to analyst, llm, or check based on requirements."""
        required_agents = state.get("required_agents", [])
        completion_status = state.get("agent_completion_status", {})
        
        if "analyst" in required_agents and not completion_status.get("analyst", False):
            logger.info("   → Routing to Analyst")
            return "to_analyst"
        elif "straight_through_llm" in required_agents and not completion_status.get("straight_through_llm", False):
            logger.info("   → Routing to Straight-Through-LLM")
            return "to_llm"
        else:
            logger.info("   → All remaining agents complete, routing to completion check")
            return "to_check"
    
    def _route_after_analyst(self, state: AgentState) -> Literal["to_llm", "to_check"]:
        """Route after analyst - go to straight-through-LLM or check completion."""
        required_agents = state.get("required_agents", [])
        completion_status = state.get("agent_completion_status", {})
        
        if "straight_through_llm" in required_agents and not completion_status.get("straight_through_llm", False):
            logger.info("   → Routing to Straight-Through-LLM")
            return "to_llm"
        else:
            logger.info("   → All agents complete, routing to completion check")
            return "to_check"
    
    def _check_completion_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Check completion node - verifies if all required agents have completed.
        This node is called after all agents execute.
        It doesn't modify state, just checks and logs.
        """
        required_agents = state.get("required_agents", [])
        completion_status = state.get("agent_completion_status", {})
        
        logger.info("=" * 80)
        logger.info("🔍 CHECK COMPLETION NODE")
        logger.info("=" * 80)
        logger.info(f"   Required agents: {required_agents}")
        logger.info(f"   Completion status: {completion_status}")
        
        # Count completed agents
        completed_count = sum(1 for agent in required_agents if completion_status.get(agent, False))
        logger.info(f"   Completed: {completed_count}/{len(required_agents)} agents")
        
        # Verify all are complete
        for agent in required_agents:
            if completion_status.get(agent, False):
                logger.info(f"   ✅ {agent}: COMPLETE")
            else:
                logger.error(f"   ❌ {agent}: INCOMPLETE")
        
        # Return empty dict - state is already updated by the agents
        return {}
    
    def _route_after_completion_check(self, state: AgentState) -> Literal["all_complete", "incomplete"]:
        """
        Route after completion check.
        Check if all required agents have finished before proceeding to writer.
        This is called after the check_completion node.
        
        Args:
            state: Current state
            
        Returns:
            "all_complete" if all agents done, "incomplete" otherwise (should not happen)
        """
        required_agents = state.get("required_agents", [])
        completion_status = state.get("agent_completion_status", {})
        
        logger.info("=" * 80)
        logger.info("🔍 FINAL COMPLETION CHECK")
        logger.info("=" * 80)
        logger.info(f"   Required agents: {required_agents}")
        logger.info(f"   Completion status: {completion_status}")
        
        # Check if all required agents are complete
        all_complete = all(
            completion_status.get(agent, False) 
            for agent in required_agents
        )
        
        if all_complete:
            logger.info("✅✅✅ ALL REQUIRED AGENTS COMPLETED - Routing to Writer Agent ✅✅✅")
            return "all_complete"
        else:
            incomplete = [agent for agent in required_agents if not completion_status.get(agent, False)]
            logger.error(f"❌ ERROR: Some agents did not complete: {incomplete}")
            logger.error(f"   This should not happen with sequential execution!")
            logger.error(f"   Completion status: {completion_status}")
            return "incomplete"
    
    # Conditional routing
    def _route_after_cost_estimate(self, state: AgentState) -> Literal["proceed", "high_cost"]:
        """
        Route based on cost estimate.
        
        Args:
            state: Current state
            
        Returns:
            Next node to execute
        """
        cost_estimate = state.get("cost_estimate", {})
        
        if not cost_estimate:
            return "proceed"
        
        budget_assessment = cost_estimate.get("budget_assessment", {})
        status = budget_assessment.get("status", "green")
        
        # For red status (high cost), we could stop or request approval
        # For now, we'll proceed but log a warning
        if status == "red":
            logger.warning(f"High cost estimate: ${budget_assessment.get('total_cost_usd', 0):.2f}")
            # In production, this might trigger an approval workflow
            # For now, proceed
        
        return "proceed"
    
    def execute(
        self,
        user_request: str,
        report_requirements: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute the multi-agent workflow.
        
        Args:
            user_request: User's research request
            report_requirements: Report requirements specification
            session_id: Session identifier
            
        Returns:
            Final state dictionary
        """
        try:
            logger.info(f"Starting workflow execution for session: {session_id}")
            
            # Create contribution tracker (stored in registry, not in state)
            # LangGraph state must be serializable, but ContributionTracker is not
            topic = report_requirements.get("topic", "Unknown")
            tracker = create_contribution_tracker(session_id, topic)
            
            # Create initial state (without tracker - agents will retrieve from registry)
            from orchestration.state import create_initial_state
            initial_state = create_initial_state(
                user_request,
                report_requirements,
                session_id
            )
            
            # Execute graph with LangSmith tracing
            config = {"configurable": {"thread_id": session_id}}
            
            logger.info("=" * 80)
            logger.info("🚀 STARTING WORKFLOW EXECUTION")
            logger.info("=" * 80)
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Topic: {topic}")
            logger.info(f"Initial state keys: {list(initial_state.keys())}")
            
            # Use stream for better observability (can see each step)
            # But invoke() is simpler for now - we'll add streaming later if needed
            try:
                final_state = self.graph.invoke(initial_state, config)
                logger.info("=" * 80)
                logger.info("✅ WORKFLOW EXECUTION COMPLETED")
                logger.info("=" * 80)
                logger.info(f"Final status: {final_state.get('status')}")
                logger.info(f"Final agent: {final_state.get('current_agent')}")
                logger.info(f"Completed tasks: {final_state.get('completed_tasks', [])}")
                logger.info(f"Report path: {final_state.get('report_path')}")
            except Exception as e:
                logger.error("=" * 80)
                logger.error("❌ WORKFLOW EXECUTION FAILED")
                logger.error("=" * 80)
                logger.error(f"Error: {e}", exc_info=True)
                raise
            
            # Save contribution summary
            try:
                summary_file = tracker.save_summary()
                logger.info(f"Contribution summary saved: {summary_file}")
                final_state["contribution_summary_path"] = str(summary_file)
            except Exception as e:
                logger.error(f"Error saving contribution summary: {e}")
            
            logger.info(f"Workflow execution completed for session: {session_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            raise


def create_workflow() -> MultiAgentWorkflow:
    """
    Factory function to create a multi-agent workflow.
    
    Returns:
        MultiAgentWorkflow instance
    """
    return MultiAgentWorkflow()

