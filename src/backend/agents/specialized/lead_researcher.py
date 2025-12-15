"""
Lead Researcher Agent - Orchestrates the multi-agent research process.
Coordinates other agents and synthesizes final report structure.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from agents.planner import TaskPlanner, ResearchPlan
from agents.specialized.lead_researcher_decision import create_decision_engine
from observability.langsmith_config import trace_agent_call

logger = logging.getLogger(__name__)


class LeadResearcherAgent:
    """
    Lead researcher agent that orchestrates the entire research process.
    Coordinates specialized agents based on a research plan.
    """
    
    def __init__(self):
        """Initialize the lead researcher agent."""
        # Load agent prompt
        self.system_prompt = load_agent_prompt('lead_researcher')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="lead_researcher",
            system_prompt=self.system_prompt
        )
        
        # Initialize planner
        self.planner = TaskPlanner()
        
        # Initialize decision engine
        self.decision_engine = create_decision_engine()
        
        logger.info("Lead Researcher Agent initialized")
    
    @trace_agent_call("lead_researcher")
    def execute(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the lead researcher agent with intelligent decision-making.
        
        Args:
            user_request: User's research request
            context: Context with report_requirements and contribution_tracker
            
        Returns:
            Dictionary with research strategy and coordination results
        """
        # Get tracker from context
        tracker = context.get("contribution_tracker") if context else None
        agent_context = None
        
        # Log agent start
        if tracker:
            agent_context = tracker.log_agent_start(
                agent_name="lead_researcher",
                agent_type="lead_researcher",
                task=f"Analyze requirements and create research strategy for: {user_request[:80]}"
            )
        
        actions_taken = []
        errors = []
        
        try:
            logger.info("=" * 80)
            logger.info("🎯 LEAD RESEARCHER AGENT - STARTING EXECUTION")
            logger.info("=" * 80)
            logger.info(f"Request: {user_request[:100]}...")
            
            # Extract report requirements from context
            report_reqs = context.get("report_requirements", {}) if context else {}
            topic = report_reqs.get("topic", "Unknown Topic")
            page_count = report_reqs.get("page_count", 20)
            source_count = report_reqs.get("source_count", 10)
            complexity = report_reqs.get("complexity", "medium")
            include_analysis = report_reqs.get("include_analysis", True)
            include_visualizations = report_reqs.get("include_visualizations", True)
            
            actions_taken.append("Extracted report requirements from context")
            logger.info(f"✓ Extracted report requirements: Topic={topic}, Pages={page_count}, Sources={source_count}")
            
            # Run decision engine to determine agent allocation
            logger.info("\n🧠 RUNNING DECISION ENGINE...")
            actions_taken.append("Running decision engine to determine optimal agent configuration")
            
            strategy = self.decision_engine.analyze_requirements(
                topic=topic,
                detailed_requirements=user_request,
                page_count=page_count,
                source_count=source_count,
                complexity=complexity,
                include_analysis=include_analysis,
                include_visualizations=include_visualizations
            )
            
            actions_taken.append(
                f"Decision: Deploy {strategy.total_agents_needed} agents total "
                f"({strategy.data_collectors} collectors, {strategy.api_researchers} API researchers, "
                f"{strategy.analysts} analysts)"
            )
            
            logger.info(f"\n✓ Research strategy created:")
            logger.info(f"   Total agents: {strategy.total_agents_needed}")
            logger.info(f"   Data collectors: {strategy.data_collectors}")
            logger.info(f"   API researchers: {strategy.api_researchers}")
            logger.info(f"   Analysts: {strategy.analysts}")
            
            # Create research plan with the strategy
            actions_taken.append("Creating detailed research plan with task allocation")
            research_plan = self.planner.create_plan(user_request, context)
            optimized_plan = self.planner.optimize_plan(research_plan)
            cost_estimate = self.planner.estimate_plan_cost(optimized_plan)
            
            actions_taken.append(f"Created plan with {len(optimized_plan.subtasks)} tasks")
            actions_taken.append(f"Estimated cost: ${cost_estimate.get('total_cost_usd', 0):.4f}")
            
            # Prepare result
            result = {
                "agent": "lead_researcher",
                "status": "strategy_created",
                "research_strategy": {
                    "complexity": strategy.complexity_level,
                    "total_agents": strategy.total_agents_needed,
                    "agent_breakdown": {
                        "data_collectors": strategy.data_collectors,
                        "api_researchers": strategy.api_researchers,
                        "analysts": strategy.analysts
                    },
                    "reasoning": strategy.reasoning,
                    "agent_allocations": [
                        {
                            "agent_type": alloc.agent_type,
                            "count": alloc.count,
                            "reasoning": alloc.reasoning,
                            "subtasks": alloc.subtasks
                        }
                        for alloc in strategy.agent_allocations
                    ]
                },
                "research_plan": {
                    "plan_id": optimized_plan.plan_id,
                    "topic": optimized_plan.topic,
                    "subtasks": [
                        {
                            "task_id": task.task_id,
                            "agent_type": task.agent_type,
                            "description": task.description,
                            "priority": task.priority,
                            "dependencies": task.dependencies
                        }
                        for task in optimized_plan.subtasks
                    ],
                    "total_tasks": len(optimized_plan.subtasks)
                },
                "cost_estimate": cost_estimate,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"\n✅ LEAD RESEARCHER COMPLETED SUCCESSFULLY")
            logger.info("=" * 80 + "\n")
            
            # Log agent completion with detailed metrics
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Created research strategy: {strategy.total_agents_needed} agents "
                                 f"({strategy.data_collectors} collectors, {strategy.api_researchers} API, "
                                 f"{strategy.analysts} analysts)",
                    output_files=[],
                    tools_used=[],  # Lead researcher doesn't use external tools
                    tokens_used=cost_estimate.get("estimated_tokens", 0),
                    estimated_cost=cost_estimate.get("total_cost_usd", 0.0),
                    metrics={
                        "total_agents_allocated": strategy.total_agents_needed,
                        "data_collectors": strategy.data_collectors,
                        "api_researchers": strategy.api_researchers,
                        "analysts": strategy.analysts,
                        "complexity_level": strategy.complexity_level,
                        "page_count": page_count,
                        "source_count": source_count,
                        "include_analysis": include_analysis,
                        "include_visualizations": include_visualizations,
                        "estimated_sources_per_collector": strategy.estimated_sources_per_collector,
                        "total_subtasks": len(optimized_plan.subtasks)
                    },
                    actions_taken=actions_taken,
                    errors=errors
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error in lead researcher agent: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
            
            # Log agent failure
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Failed to create research strategy: {str(e)}",
                    output_files=[],
                    tools_used=[],
                    tokens_used=0,
                    estimated_cost=0.0,
                    metrics={},
                    actions_taken=actions_taken,
                    errors=errors
                )
            
            raise
    
    def coordinate_agents(
        self,
        research_plan: ResearchPlan,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate agent execution based on the research plan.
        
        Args:
            research_plan: The research plan to execute
            agent_results: Results from executed agents
            
        Returns:
            Coordination summary
        """
        # This would contain logic for:
        # - Tracking which tasks are complete
        # - Determining which tasks can execute next
        # - Aggregating results from specialized agents
        # - Triggering the report writer when research is complete
        
        logger.info("Coordinating agent execution...")
        
        completed_tasks = list(agent_results.keys())
        executable_tasks = self.planner.get_executable_tasks(research_plan, completed_tasks)
        
        return {
            "completed_tasks": len(completed_tasks),
            "executable_tasks": len(executable_tasks),
            "pending_tasks": len(research_plan.subtasks) - len(completed_tasks),
            "next_tasks": [task.task_id for task in executable_tasks]
        }
    
