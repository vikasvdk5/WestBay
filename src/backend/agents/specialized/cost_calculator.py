"""
Cost Calculator Agent - Estimates token usage and costs for report generation.
Provides cost breakdown before initiating the research process.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from observability.langsmith_config import trace_agent_call

logger = logging.getLogger(__name__)


class CostCalculatorAgent:
    """
    Cost calculator agent that estimates token usage and costs.
    Provides cost breakdowns by agent and task type.
    """
    
    # Token estimates per agent type (average)
    AGENT_TOKEN_ESTIMATES = {
        "data_collector": 5000,
        "api_researcher": 3000,
        "analyst": 8000,
        "writer": 12000,
        "lead_researcher": 5000
    }
    
    # Gemini API pricing (per 1M tokens)
    PRICING = {
        "input_per_1m": 0.075,  # $0.075 per 1M input tokens
        "output_per_1m": 0.30,  # $0.30 per 1M output tokens
    }
    
    # Complexity multipliers
    COMPLEXITY_MULTIPLIERS = {
        "simple": 1.0,
        "medium": 1.5,
        "complex": 2.0
    }
    
    def __init__(self):
        """Initialize the cost calculator agent."""
        # Load agent prompt
        self.system_prompt = load_agent_prompt('cost_calculator')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="cost_calculator",
            system_prompt=self.system_prompt
        )
        
        logger.info("Cost Calculator Agent initialized")
    
    @trace_agent_call("cost_calculator")
    def execute(
        self,
        report_requirements: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the cost calculator agent.
        
        Args:
            report_requirements: Report requirements specification
            context: Optional context information
            
        Returns:
            Dictionary with cost estimates
        """
        try:
            logger.info("Cost Calculator estimating report costs...")
            
            # Extract requirements
            page_count = report_requirements.get("page_count", 20)
            source_count = report_requirements.get("source_count", 10)
            complexity = report_requirements.get("complexity", "medium")
            include_analysis = report_requirements.get("include_analysis", True)
            include_visualizations = report_requirements.get("include_visualizations", True)
            
            # Calculate token estimates
            token_estimate = self._calculate_tokens(
                page_count,
                source_count,
                complexity,
                include_analysis,
                include_visualizations
            )
            
            # Calculate cost
            cost_estimate = self._calculate_cost(token_estimate)
            
            # Get breakdown by agent
            agent_breakdown = self._get_agent_breakdown(
                token_estimate,
                source_count,
                include_analysis
            )
            
            # Assess budget
            budget_assessment = self._assess_budget(cost_estimate["total_cost_usd"])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                cost_estimate["total_cost_usd"],
                report_requirements
            )
            
            result = {
                "agent": "cost_calculator",
                "status": "completed",
                "token_estimate": token_estimate,
                "cost_estimate": cost_estimate,
                "agent_breakdown": agent_breakdown,
                "budget_assessment": budget_assessment,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Cost estimate: ${cost_estimate['total_cost_usd']:.2f} for {token_estimate['total_tokens']:,} tokens")
            return result
            
        except Exception as e:
            logger.error(f"Error in cost calculator agent: {e}")
            raise
    
    def _calculate_tokens(
        self,
        page_count: int,
        source_count: int,
        complexity: str,
        include_analysis: bool,
        include_visualizations: bool
    ) -> Dict[str, int]:
        """
        Calculate estimated token usage.
        
        Args:
            page_count: Number of pages in report
            source_count: Number of data sources
            complexity: Report complexity (simple/medium/complex)
            include_analysis: Whether to include analysis
            include_visualizations: Whether to include visualizations
            
        Returns:
            Dictionary with token estimates
        """
        multiplier = self.COMPLEXITY_MULTIPLIERS.get(complexity, 1.5)
        
        # Research phase tokens
        research_tokens = source_count * self.AGENT_TOKEN_ESTIMATES["data_collector"]
        api_tokens = (source_count // 2) * self.AGENT_TOKEN_ESTIMATES["api_researcher"]
        
        # Analysis phase tokens
        analysis_tokens = 0
        if include_analysis:
            analysis_tokens = self.AGENT_TOKEN_ESTIMATES["analyst"]
            if include_visualizations:
                analysis_tokens += 3000  # Additional tokens for viz generation
        
        # Writing phase tokens
        writing_tokens = page_count * 1000  # ~1000 tokens per page
        
        # Coordination tokens
        coordination_tokens = self.AGENT_TOKEN_ESTIMATES["lead_researcher"]
        
        # Apply complexity multiplier
        subtotal = research_tokens + api_tokens + analysis_tokens + writing_tokens + coordination_tokens
        total_tokens = int(subtotal * multiplier)
        
        # Assume 70% input, 30% output
        input_tokens = int(total_tokens * 0.7)
        output_tokens = int(total_tokens * 0.3)
        
        return {
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "research_tokens": int((research_tokens + api_tokens) * multiplier),
            "analysis_tokens": int(analysis_tokens * multiplier),
            "writing_tokens": int(writing_tokens * multiplier),
            "coordination_tokens": int(coordination_tokens * multiplier)
        }
    
    def _calculate_cost(self, token_estimate: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate cost estimate from token usage.
        
        Args:
            token_estimate: Token estimate dictionary
            
        Returns:
            Cost estimate dictionary
        """
        input_cost = (token_estimate["input_tokens"] / 1_000_000) * self.PRICING["input_per_1m"]
        output_cost = (token_estimate["output_tokens"] / 1_000_000) * self.PRICING["output_per_1m"]
        total_cost = input_cost + output_cost
        
        # Add confidence range (±20%)
        min_cost = total_cost * 0.8
        max_cost = total_cost * 1.2
        
        return {
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 2),
            "min_cost_usd": round(min_cost, 2),
            "max_cost_usd": round(max_cost, 2),
            "confidence_range": "±20%"
        }
    
    def _get_agent_breakdown(
        self,
        token_estimate: Dict[str, int],
        source_count: int,
        include_analysis: bool
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get cost breakdown by agent.
        
        Args:
            token_estimate: Token estimate
            source_count: Number of sources
            include_analysis: Whether analysis is included
            
        Returns:
            Agent breakdown dictionary
        """
        total_tokens = token_estimate["total_tokens"]
        
        breakdown = {
            "lead_researcher": {
                "tokens": token_estimate["coordination_tokens"],
                "percentage": round((token_estimate["coordination_tokens"] / total_tokens) * 100, 1)
            },
            "data_collector": {
                "tokens": token_estimate["research_tokens"] // 2,
                "percentage": round(((token_estimate["research_tokens"] // 2) / total_tokens) * 100, 1)
            },
            "api_researcher": {
                "tokens": token_estimate["research_tokens"] // 2,
                "percentage": round(((token_estimate["research_tokens"] // 2) / total_tokens) * 100, 1)
            },
            "writer": {
                "tokens": token_estimate["writing_tokens"],
                "percentage": round((token_estimate["writing_tokens"] / total_tokens) * 100, 1)
            }
        }
        
        if include_analysis:
            breakdown["analyst"] = {
                "tokens": token_estimate["analysis_tokens"],
                "percentage": round((token_estimate["analysis_tokens"] / total_tokens) * 100, 1)
            }
        
        return breakdown
    
    def _assess_budget(self, total_cost: float) -> Dict[str, Any]:
        """
        Assess the budget based on cost thresholds.
        
        Args:
            total_cost: Total estimated cost
            
        Returns:
            Budget assessment dictionary
        """
        if total_cost < 1.0:
            status = "green"
            message = "Low cost - no action needed"
        elif total_cost < 5.0:
            status = "yellow"
            message = "Medium cost - consider optimization if near upper bound"
        else:
            status = "red"
            message = "High cost - recommend scope reduction or phased approach"
        
        return {
            "status": status,
            "message": message,
            "total_cost_usd": total_cost
        }
    
    def _generate_recommendations(
        self,
        total_cost: float,
        requirements: Dict[str, Any]
    ) -> List[str]:
        """
        Generate cost optimization recommendations.
        
        Args:
            total_cost: Total estimated cost
            requirements: Report requirements
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if total_cost > 5.0:
            recommendations.extend([
                "Consider reducing the number of data sources to focus on highest-quality sources",
                "Reduce page count by targeting only essential sections",
                "Simplify visualizations or reduce the number of charts",
                "Consider a phased approach: initial report followed by deep-dive analysis"
            ])
        elif total_cost > 2.0:
            recommendations.append("Current scope is reasonable, but consider source prioritization for cost savings")
        else:
            recommendations.append("Cost is within acceptable range - proceed with current scope")
        
        return recommendations

