"""
Custom LangGraph-based task decomposition planner.
Breaks down user requirements into sub-tasks for multi-agent execution.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings

logger = logging.getLogger(__name__)


class SubTask(BaseModel):
    """Represents a sub-task in the research plan."""
    
    task_id: str = Field(description="Unique identifier for the task")
    agent_type: str = Field(description="Type of agent to handle this task")
    description: str = Field(description="Description of the task")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this task depends on")
    priority: int = Field(default=1, description="Priority level (1=highest)")
    estimated_tokens: Optional[int] = Field(default=None, description="Estimated token usage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ResearchPlan(BaseModel):
    """Represents a complete research plan."""
    
    plan_id: str = Field(description="Unique identifier for the plan")
    topic: str = Field(description="Research topic")
    subtasks: List[SubTask] = Field(description="List of sub-tasks")
    total_estimated_tokens: Optional[int] = Field(default=None, description="Total estimated token usage")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskPlanner:
    """
    Custom LangGraph-based planner for task decomposition.
    Uses Gemini to intelligently break down research requirements.
    """
    
    PLANNING_PROMPT = """You are an expert research planner. Your task is to break down a market research request into specific, actionable sub-tasks.

Available Agent Types:
- data_collector: Web scraping and content extraction from URLs
- api_researcher: Calling external APIs for data
- analyst: Analyzing data, identifying trends, creating visualizations
- writer: Writing report sections and synthesizing findings
- cost_calculator: Estimating token usage and costs

Guidelines:
1. Break down the research into 3-8 specific sub-tasks
2. Assign each task to the most appropriate agent type
3. Identify dependencies between tasks
4. Prioritize tasks (1 = highest priority, execute first)
5. Keep task descriptions clear and specific

Output Format (JSON):
{{
  "subtasks": [
    {{
      "task_id": "task_1",
      "agent_type": "data_collector",
      "description": "Scrape market size data from industry reports",
      "dependencies": [],
      "priority": 1
    }},
    ...
  ]
}}

User Request: {user_request}

Generate a research plan as JSON:"""
    
    def __init__(self):
        """Initialize the task planner."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.3,  # Lower temperature for more structured output
        )
        logger.info("Task Planner initialized")
    
    def create_plan(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ResearchPlan:
        """
        Create a research plan from user request.
        
        Args:
            user_request: The user's research requirements
            context: Optional context information
            
        Returns:
            ResearchPlan object with sub-tasks
        """
        try:
            logger.info(f"Creating research plan for: {user_request[:100]}...")
            
            # Invoke LLM to generate plan
            planning_prompt = self.PLANNING_PROMPT.format(user_request=user_request)
            
            messages = [
                SystemMessage(content="You are a research planning expert."),
                HumanMessage(content=planning_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            subtasks = self._parse_plan_response(response_content)
            
            # Create research plan
            plan = ResearchPlan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                topic=user_request[:100],
                subtasks=subtasks,
                metadata=context or {}
            )
            
            logger.info(f"Research plan created with {len(subtasks)} sub-tasks")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating research plan: {e}")
            # Return a fallback plan
            return self._create_fallback_plan(user_request)
    
    def _parse_plan_response(self, response: str) -> List[SubTask]:
        """
        Parse LLM response into SubTask objects.
        
        Args:
            response: LLM response content
            
        Returns:
            List of SubTask objects
        """
        import json
        import re
        
        subtasks = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                
                for i, task_data in enumerate(plan_data.get("subtasks", [])):
                    subtask = SubTask(
                        task_id=task_data.get("task_id", f"task_{i+1}"),
                        agent_type=task_data.get("agent_type", "data_collector"),
                        description=task_data.get("description", ""),
                        dependencies=task_data.get("dependencies", []),
                        priority=task_data.get("priority", i+1),
                        metadata=task_data.get("metadata", {})
                    )
                    subtasks.append(subtask)
            
        except Exception as e:
            logger.warning(f"Error parsing plan response: {e}")
        
        return subtasks
    
    def _create_fallback_plan(self, user_request: str) -> ResearchPlan:
        """
        Create a basic fallback plan if LLM parsing fails.
        
        Args:
            user_request: User's request
            
        Returns:
            Basic ResearchPlan
        """
        logger.warning("Creating fallback plan")
        
        subtasks = [
            SubTask(
                task_id="task_1",
                agent_type="data_collector",
                description=f"Collect data for: {user_request[:100]}",
                dependencies=[],
                priority=1
            ),
            SubTask(
                task_id="task_2",
                agent_type="analyst",
                description="Analyze collected data and identify trends",
                dependencies=["task_1"],
                priority=2
            ),
            SubTask(
                task_id="task_3",
                agent_type="writer",
                description="Write comprehensive research report",
                dependencies=["task_1", "task_2"],
                priority=3
            )
        ]
        
        return ResearchPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            topic=user_request[:100],
            subtasks=subtasks
        )
    
    def optimize_plan(self, plan: ResearchPlan) -> ResearchPlan:
        """
        Optimize a research plan by reordering tasks and resolving dependencies.
        
        Args:
            plan: The research plan to optimize
            
        Returns:
            Optimized research plan
        """
        # Sort tasks by priority and dependencies
        # Tasks with no dependencies and higher priority go first
        
        sorted_tasks = sorted(
            plan.subtasks,
            key=lambda t: (len(t.dependencies), t.priority)
        )
        
        plan.subtasks = sorted_tasks
        logger.info(f"Plan optimized: {len(sorted_tasks)} tasks reordered")
        
        return plan
    
    def get_executable_tasks(
        self,
        plan: ResearchPlan,
        completed_task_ids: List[str]
    ) -> List[SubTask]:
        """
        Get tasks that are ready to execute (dependencies met).
        
        Args:
            plan: The research plan
            completed_task_ids: List of completed task IDs
            
        Returns:
            List of executable SubTask objects
        """
        executable = []
        
        for task in plan.subtasks:
            # Skip if already completed
            if task.task_id in completed_task_ids:
                continue
            
            # Check if all dependencies are met
            deps_met = all(dep_id in completed_task_ids for dep_id in task.dependencies)
            
            if deps_met:
                executable.append(task)
        
        return executable
    
    def estimate_plan_cost(self, plan: ResearchPlan) -> Dict[str, Any]:
        """
        Estimate the cost of executing a research plan.
        
        Args:
            plan: The research plan
            
        Returns:
            Dictionary with cost estimates
        """
        # Simple token estimation based on agent types
        agent_token_estimates = {
            "data_collector": 5000,
            "api_researcher": 3000,
            "analyst": 8000,
            "writer": 12000,
            "cost_calculator": 2000
        }
        
        total_tokens = 0
        breakdown = {}
        
        for task in plan.subtasks:
            est_tokens = agent_token_estimates.get(task.agent_type, 5000)
            total_tokens += est_tokens
            
            if task.agent_type not in breakdown:
                breakdown[task.agent_type] = 0
            breakdown[task.agent_type] += est_tokens
        
        # Estimate cost (Gemini pricing: ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens)
        # Assume 70% input, 30% output
        input_tokens = int(total_tokens * 0.7)
        output_tokens = int(total_tokens * 0.3)
        
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30
        total_cost = input_cost + output_cost
        
        plan.total_estimated_tokens = total_tokens
        
        return {
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(total_cost, 2),
            "breakdown_by_agent": breakdown
        }

