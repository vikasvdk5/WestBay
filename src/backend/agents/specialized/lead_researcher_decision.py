"""
Lead Researcher Decision Engine
Analyzes report requirements and determines optimal agent configuration.
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentAllocation:
    """Represents the allocation of agents for a task."""
    agent_type: str
    count: int
    reasoning: str
    subtasks: List[str]


@dataclass
class ResearchStrategy:
    """Complete research strategy based on requirements."""
    complexity_level: str
    total_agents_needed: int
    data_collectors: int
    api_researchers: int
    analysts: int
    estimated_sources_per_collector: int
    estimated_apis_per_researcher: int
    reasoning: List[str]
    agent_allocations: List[AgentAllocation]


class LeadResearcherDecisionEngine:
    """
    Decision engine that determines how many agents to spawn and why.
    Based on topic, requirements, complexity, page count, sources, etc.
    """
    
    def __init__(self):
        """Initialize the decision engine."""
        self.complexity_multipliers = {
            "simple": 1.0,
            "medium": 1.5,
            "complex": 2.0
        }
        logger.info("Lead Researcher Decision Engine initialized")
    
    def analyze_requirements(
        self,
        topic: str,
        detailed_requirements: str,
        page_count: int,
        source_count: int,
        complexity: str,
        include_analysis: bool,
        include_visualizations: bool
    ) -> ResearchStrategy:
        """
        Analyze all requirements and create optimal research strategy.
        
        Args:
            topic: Research topic
            detailed_requirements: Detailed requirements text
            page_count: Target page count
            source_count: Number of sources needed
            complexity: Report complexity (simple, medium, complex)
            include_analysis: Whether to include detailed analysis
            include_visualizations: Whether to include visualizations
            
        Returns:
            ResearchStrategy with complete agent allocation plan
        """
        logger.info("=" * 80)
        logger.info("LEAD RESEARCHER DECISION ENGINE - ANALYZING REQUIREMENTS")
        logger.info("=" * 80)
        
        reasoning = []
        
        # 1. Analyze Topic Complexity
        logger.info(f"\n📋 REQUIREMENT ANALYSIS:")
        logger.info(f"   Topic: {topic}")
        logger.info(f"   Page Count: {page_count}")
        logger.info(f"   Sources Needed: {source_count}")
        logger.info(f"   Complexity: {complexity}")
        logger.info(f"   Include Analysis: {include_analysis}")
        logger.info(f"   Include Visualizations: {include_visualizations}")
        
        # 2. Determine base agent needs
        multiplier = self.complexity_multipliers.get(complexity.lower(), 1.5)
        
        # Calculate data collectors needed
        # Rule: 1 collector can handle 3-5 sources, adjusted by complexity
        sources_per_collector = max(3, int(5 / multiplier))
        data_collectors = max(1, (source_count + sources_per_collector - 1) // sources_per_collector)
        
        reasoning.append(
            f"Based on {source_count} sources and {complexity} complexity, "
            f"need {data_collectors} data collector(s) (each handling ~{sources_per_collector} sources)"
        )
        
        logger.info(f"\n🔍 DATA COLLECTION STRATEGY:")
        logger.info(f"   Sources per collector: {sources_per_collector}")
        logger.info(f"   Data collectors needed: {data_collectors}")
        logger.info(f"   Reasoning: {reasoning[-1]}")
        
        # Calculate API researchers needed
        # Rule: For complex topics, use 1-2 API researchers for external data
        api_researchers = 0
        if complexity.lower() in ["medium", "complex"]:
            # Check if topic likely needs external API data
            api_keywords = ["market", "financial", "crypto", "stock", "economy", "technology"]
            needs_api = any(keyword in topic.lower() or keyword in detailed_requirements.lower() 
                          for keyword in api_keywords)
            
            if needs_api:
                api_researchers = 1 if complexity.lower() == "medium" else 2
                reasoning.append(
                    f"Topic mentions market/financial data - deploying {api_researchers} "
                    f"API researcher(s) for external data sources"
                )
                
                logger.info(f"\n🌐 API RESEARCH STRATEGY:")
                logger.info(f"   API researchers needed: {api_researchers}")
                logger.info(f"   Reasoning: {reasoning[-1]}")
            else:
                reasoning.append("Topic doesn't require external API data - using web sources only")
                logger.info(f"\n🌐 API RESEARCH STRATEGY:")
                logger.info(f"   API researchers needed: 0")
                logger.info(f"   Reasoning: {reasoning[-1]}")
        
        # Calculate analysts needed
        # Rule: 1 analyst for every 20 pages or if analysis requested
        analysts = 0
        if include_analysis:
            analysts = max(1, page_count // 20)
            reasoning.append(
                f"Analysis requested for {page_count}-page report - "
                f"deploying {analysts} analyst(s)"
            )
            
            logger.info(f"\n📊 ANALYSIS STRATEGY:")
            logger.info(f"   Analysts needed: {analysts}")
            logger.info(f"   Reasoning: {reasoning[-1]}")
            
            # Add visualization consideration
            if include_visualizations:
                reasoning.append(
                    f"Visualizations requested - analyst(s) will generate {max(2, page_count // 10)} charts"
                )
                logger.info(f"   Visualizations: ~{max(2, page_count // 10)} charts will be generated")
        else:
            reasoning.append("No detailed analysis requested - data will be summarized directly")
            logger.info(f"\n📊 ANALYSIS STRATEGY:")
            logger.info(f"   Analysts needed: 0")
            logger.info(f"   Reasoning: {reasoning[-1]}")
        
        # Create agent allocations with subtasks
        agent_allocations = []
        
        if data_collectors > 0:
            subtasks = self._generate_collector_subtasks(
                topic, 
                detailed_requirements, 
                data_collectors,
                source_count
            )
            agent_allocations.append(AgentAllocation(
                agent_type="data_collector",
                count=data_collectors,
                reasoning=f"Collect data from {source_count} web sources",
                subtasks=subtasks
            ))
        
        if api_researchers > 0:
            subtasks = self._generate_api_researcher_subtasks(topic, api_researchers)
            agent_allocations.append(AgentAllocation(
                agent_type="api_researcher",
                count=api_researchers,
                reasoning="Gather external API data for market/financial insights",
                subtasks=subtasks
            ))
        
        if analysts > 0:
            subtasks = self._generate_analyst_subtasks(
                topic,
                include_visualizations,
                page_count
            )
            agent_allocations.append(AgentAllocation(
                agent_type="analyst",
                count=analysts,
                reasoning=f"Analyze collected data and generate {max(2, page_count // 10)} visualizations",
                subtasks=subtasks
            ))
        
        # ALWAYS include straight_through_llm agent - guaranteed content generation
        agent_allocations.append(AgentAllocation(
            agent_type="straight_through_llm",
            count=1,
            reasoning="Generate comprehensive report content using LLM foundational knowledge (always included)",
            subtasks=[
                f"Generate professional content for all report sections on {topic}",
                f"Produce {page_count * 250} words of well-structured, business-quality narrative",
                "Provide citations and references for all claims",
                "Ensure no placeholder text in any section"
            ]
        ))
        
        total_agents = data_collectors + api_researchers + analysts + 1  # +1 for straight_through_llm
        
        strategy = ResearchStrategy(
            complexity_level=complexity,
            total_agents_needed=total_agents,
            data_collectors=data_collectors,
            api_researchers=api_researchers,
            analysts=analysts,
            estimated_sources_per_collector=sources_per_collector,
            estimated_apis_per_researcher=2 if api_researchers > 0 else 0,
            reasoning=reasoning,
            agent_allocations=agent_allocations
        )
        
        # Log final strategy
        logger.info(f"\n" + "=" * 80)
        logger.info(f"FINAL RESEARCH STRATEGY")
        logger.info(f"=" * 80)
        logger.info(f"   Total agents to deploy: {total_agents}")
        logger.info(f"   - Data Collectors: {data_collectors}")
        logger.info(f"   - API Researchers: {api_researchers}")
        logger.info(f"   - Analysts: {analysts}")
        logger.info(f"   - Straight-Through-LLM: 1 (always included)")
        logger.info(f"\n   REASONING SUMMARY:")
        for i, reason in enumerate(reasoning, 1):
            logger.info(f"   {i}. {reason}")
        logger.info("=" * 80 + "\n")
        
        return strategy
    
    def _generate_collector_subtasks(
        self,
        topic: str,
        requirements: str,
        collector_count: int,
        total_sources: int
    ) -> List[str]:
        """Generate subtasks for data collectors."""
        subtasks = []
        sources_per_collector = (total_sources + collector_count - 1) // collector_count
        
        # Try to identify different aspects from requirements
        aspects = self._extract_research_aspects(topic, requirements)
        
        if len(aspects) >= collector_count:
            for i in range(collector_count):
                subtasks.append(
                    f"Research {aspects[i]} - collect data from ~{sources_per_collector} sources"
                )
        else:
            for i in range(collector_count):
                subtasks.append(
                    f"Collect data on {topic} (batch {i+1}/{collector_count}) - "
                    f"~{sources_per_collector} sources"
                )
        
        return subtasks
    
    def _generate_api_researcher_subtasks(
        self,
        topic: str,
        researcher_count: int
    ) -> List[str]:
        """Generate subtasks for API researchers."""
        subtasks = []
        
        # Common API data types
        api_types = [
            "market data and financial metrics",
            "industry statistics and trends",
            "competitive analysis data",
            "economic indicators"
        ]
        
        for i in range(researcher_count):
            subtasks.append(
                f"Gather {api_types[i % len(api_types)]} via external APIs"
            )
        
        return subtasks
    
    def _generate_analyst_subtasks(
        self,
        topic: str,
        include_viz: bool,
        page_count: int
    ) -> List[str]:
        """Generate subtasks for analysts."""
        subtasks = [
            "Analyze collected data and identify key trends",
            "Generate insights and recommendations"
        ]
        
        if include_viz:
            num_charts = max(2, page_count // 10)
            subtasks.append(f"Create {num_charts} data visualizations")
        
        return subtasks
    
    def _extract_research_aspects(
        self,
        topic: str,
        requirements: str
    ) -> List[str]:
        """Extract different research aspects from topic and requirements."""
        # Common research dimensions
        aspects = [
            "market size and growth trends",
            "competitive landscape analysis",
            "technology and innovation trends",
            "regulatory and policy factors",
            "consumer behavior and demographics"
        ]
        
        # Could be enhanced with NLP to extract from requirements
        # For now, return standard aspects
        return aspects


def create_decision_engine() -> LeadResearcherDecisionEngine:
    """Factory function to create decision engine."""
    return LeadResearcherDecisionEngine()

