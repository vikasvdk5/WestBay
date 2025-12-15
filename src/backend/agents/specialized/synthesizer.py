"""
Synthesizer Agent - Dynamically creates report structure based on research requirements.
Decoupled from orchestration to focus solely on intelligent report synthesis.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from observability.langsmith_config import trace_agent_call

logger = logging.getLogger(__name__)


class ReportSection:
    """Represents a section in the report structure."""
    
    def __init__(
        self,
        section_id: str,
        title: str,
        description: str,
        mandatory: bool = False,
        subsections: Optional[List['ReportSection']] = None,
        content_requirements: Optional[List[str]] = None
    ):
        self.section_id = section_id
        self.title = title
        self.description = description
        self.mandatory = mandatory
        self.subsections = subsections or []
        self.content_requirements = content_requirements or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "description": self.description,
            "mandatory": self.mandatory,
            "subsections": [sub.to_dict() for sub in self.subsections],
            "content_requirements": self.content_requirements
        }


class SynthesizerAgent:
    """
    Synthesizer Agent - Creates dynamic, intelligent report structures.
    
    Responsibilities:
    - Analyze research topic and detailed requirements
    - Determine necessary report sections beyond the 4 mandatory ones
    - Create hierarchical section structure with subsections
    - Specify content requirements for each section
    - Adapt structure based on report type (market research, technology analysis, etc.)
    """
    
    # Mandatory sections that every report must have
    MANDATORY_SECTIONS = [
        {
            "section_id": "executive_summary",
            "title": "Executive Summary",
            "description": "High-level overview of key findings and recommendations"
        },
        {
            "section_id": "introduction",
            "title": "Introduction",
            "description": "Background, context, and objectives of the research"
        },
        {
            "section_id": "methodology",
            "title": "Methodology",
            "description": "Research approach, data sources, and analysis methods"
        },
        {
            "section_id": "references",
            "title": "References",
            "description": "Citations and sources used in the research"
        }
    ]
    
    def __init__(self):
        """Initialize the synthesizer agent."""
        # Load agent prompt (if needed for LLM-based section generation)
        try:
            self.system_prompt = load_agent_prompt('synthesizer')
        except:
            # Fallback if prompt file doesn't exist yet
            self.system_prompt = "You are a report structure synthesizer."
        
        # Initialize executor for LLM calls if needed
        self.executor = AgentExecutor(
            agent_name="synthesizer",
            system_prompt=self.system_prompt
        )
        
        logger.info("Synthesizer Agent initialized")
    
    @trace_agent_call("synthesizer")
    def execute(
        self,
        topic: str,
        detailed_requirements: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create dynamic report structure based on research requirements.
        
        Args:
            topic: Research topic
            detailed_requirements: Detailed requirements from user
            context: Additional context including report requirements
            
        Returns:
            Dictionary with report structure and metadata
        """
        # Get tracker from context
        tracker = context.get("contribution_tracker") if context else None
        agent_context = None
        
        # Log agent start
        if tracker:
            agent_context = tracker.log_agent_start(
                agent_name="synthesizer",
                agent_type="synthesizer",
                task=f"Create dynamic report structure for: {topic}"
            )
        
        actions_taken = []
        errors = []
        
        try:
            logger.info("=" * 80)
            logger.info("📝 SYNTHESIZER AGENT - STARTING EXECUTION")
            logger.info("=" * 80)
            logger.info(f"Topic: {topic}")
            logger.info(f"Requirements: {detailed_requirements[:100]}...")
            
            actions_taken.append("Analyzing topic and requirements")
            
            # Get report requirements from context
            report_reqs = context.get("report_requirements", {}) if context else {}
            page_count = report_reqs.get("page_count", 20)
            include_analysis = report_reqs.get("include_analysis", True)
            include_visualizations = report_reqs.get("include_visualizations", True)
            complexity = report_reqs.get("complexity", "medium")
            
            logger.info(f"\n📊 Report Configuration:")
            logger.info(f"   Page Count: {page_count}")
            logger.info(f"   Complexity: {complexity}")
            logger.info(f"   Include Analysis: {include_analysis}")
            logger.info(f"   Include Visualizations: {include_visualizations}")
            
            # Step 1: Create mandatory sections
            logger.info(f"\n🔹 Creating mandatory sections...")
            sections = self._create_mandatory_sections()
            actions_taken.append(f"Created {len(self.MANDATORY_SECTIONS)} mandatory sections")
            
            # Step 2: Analyze topic to determine report type
            report_type = self._determine_report_type(topic, detailed_requirements)
            actions_taken.append(f"Identified report type: {report_type}")
            logger.info(f"\n🔍 Report Type: {report_type}")
            
            # Step 3: Generate dynamic sections based on topic and requirements
            logger.info(f"\n🔹 Generating dynamic sections...")
            dynamic_sections = self._generate_dynamic_sections(
                topic=topic,
                requirements=detailed_requirements,
                report_type=report_type,
                page_count=page_count,
                include_analysis=include_analysis,
                include_visualizations=include_visualizations,
                complexity=complexity
            )
            
            actions_taken.append(f"Generated {len(dynamic_sections)} dynamic sections")
            logger.info(f"   Generated {len(dynamic_sections)} dynamic sections")
            
            # Step 4: Insert dynamic sections in appropriate order
            # Order: Executive Summary -> Introduction -> Dynamic Sections -> Methodology -> References
            final_sections = [
                sections[0],  # Executive Summary
                sections[1],  # Introduction
                *dynamic_sections,  # Dynamic sections
                sections[2],  # Methodology
                sections[3]   # References
            ]
            
            # Log all sections
            logger.info(f"\n📋 Final Report Structure ({len(final_sections)} sections):")
            for i, section in enumerate(final_sections, 1):
                logger.info(f"   {i}. {section.title}")
                if section.subsections:
                    for j, subsection in enumerate(section.subsections, 1):
                        logger.info(f"      {i}.{j}. {subsection.title}")
            
            # Step 5: Prepare result
            result = {
                "agent": "synthesizer",
                "status": "completed",
                "report_structure": {
                    "report_type": report_type,
                    "total_sections": len(final_sections),
                    "mandatory_sections": len(self.MANDATORY_SECTIONS),
                    "dynamic_sections": len(dynamic_sections),
                    "sections": [section.to_dict() for section in final_sections]
                },
                "metadata": {
                    "topic": topic,
                    "page_count": page_count,
                    "complexity": complexity,
                    "include_analysis": include_analysis,
                    "include_visualizations": include_visualizations
                },
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"\n✅ SYNTHESIZER COMPLETED SUCCESSFULLY")
            logger.info(f"   Total sections: {len(final_sections)}")
            logger.info(f"   Mandatory: {len(self.MANDATORY_SECTIONS)}, Dynamic: {len(dynamic_sections)}")
            logger.info("=" * 80 + "\n")
            
            # Log agent completion
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Created {len(final_sections)}-section report structure "
                                 f"({len(dynamic_sections)} dynamic sections)",
                    output_files=[],
                    tools_used=[],
                    tokens_used=0,  # No LLM calls in basic implementation
                    estimated_cost=0.0,
                    metrics={
                        "total_sections": len(final_sections),
                        "mandatory_sections": len(self.MANDATORY_SECTIONS),
                        "dynamic_sections": len(dynamic_sections),
                        "report_type": report_type,
                        "total_subsections": sum(len(s.subsections) for s in final_sections)
                    },
                    actions_taken=actions_taken,
                    errors=errors
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error in synthesizer agent: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
            
            # Log agent failure
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Failed to create report structure: {str(e)}",
                    output_files=[],
                    tools_used=[],
                    tokens_used=0,
                    estimated_cost=0.0,
                    metrics={},
                    actions_taken=actions_taken,
                    errors=errors
                )
            
            raise
    
    def _create_mandatory_sections(self) -> List[ReportSection]:
        """Create the 4 mandatory sections."""
        sections = []
        
        for section_def in self.MANDATORY_SECTIONS:
            section = ReportSection(
                section_id=section_def["section_id"],
                title=section_def["title"],
                description=section_def["description"],
                mandatory=True
            )
            sections.append(section)
        
        return sections
    
    def _determine_report_type(self, topic: str, requirements: str) -> str:
        """
        Determine the type of report based on topic and requirements.
        
        Returns:
            Report type string
        """
        topic_lower = topic.lower()
        requirements_lower = requirements.lower()
        combined = topic_lower + " " + requirements_lower
        
        # Market research keywords
        if any(keyword in combined for keyword in ["market", "industry", "market size", "market share", "competitive"]):
            return "market_research"
        
        # Technology analysis keywords
        if any(keyword in combined for keyword in ["technology", "innovation", "technical", "architecture", "implementation"]):
            return "technology_analysis"
        
        # Financial analysis keywords
        if any(keyword in combined for keyword in ["financial", "investment", "revenue", "profit", "valuation", "stock"]):
            return "financial_analysis"
        
        # Trend analysis keywords
        if any(keyword in combined for keyword in ["trend", "forecast", "prediction", "future", "outlook"]):
            return "trend_analysis"
        
        # Comparative analysis keywords
        if any(keyword in combined for keyword in ["compare", "comparison", "versus", "vs", "competitive"]):
            return "comparative_analysis"
        
        # Default to general research
        return "general_research"
    
    def _generate_dynamic_sections(
        self,
        topic: str,
        requirements: str,
        report_type: str,
        page_count: int,
        include_analysis: bool,
        include_visualizations: bool,
        complexity: str
    ) -> List[ReportSection]:
        """
        Generate dynamic sections based on report type and requirements.
        
        This is the core intelligence - it determines what sections are needed
        beyond the mandatory 4 sections.
        """
        dynamic_sections = []
        
        # Generate sections based on report type
        if report_type == "market_research":
            dynamic_sections.extend(self._create_market_research_sections(
                topic, requirements, page_count, include_analysis, include_visualizations
            ))
        
        elif report_type == "technology_analysis":
            dynamic_sections.extend(self._create_technology_analysis_sections(
                topic, requirements, page_count, include_analysis
            ))
        
        elif report_type == "financial_analysis":
            dynamic_sections.extend(self._create_financial_analysis_sections(
                topic, requirements, page_count, include_analysis, include_visualizations
            ))
        
        elif report_type == "trend_analysis":
            dynamic_sections.extend(self._create_trend_analysis_sections(
                topic, requirements, page_count, include_analysis, include_visualizations
            ))
        
        elif report_type == "comparative_analysis":
            dynamic_sections.extend(self._create_comparative_analysis_sections(
                topic, requirements, page_count, include_analysis
            ))
        
        else:  # general_research
            dynamic_sections.extend(self._create_general_research_sections(
                topic, requirements, page_count, include_analysis
            ))
        
        # Add analysis section if requested
        if include_analysis:
            dynamic_sections.append(self._create_analysis_section(include_visualizations))
        
        # Add recommendations/conclusion section
        dynamic_sections.append(self._create_conclusions_section(report_type))
        
        return dynamic_sections
    
    def _create_market_research_sections(
        self,
        topic: str,
        requirements: str,
        page_count: int,
        include_analysis: bool,
        include_visualizations: bool
    ) -> List[ReportSection]:
        """Create sections specific to market research reports."""
        sections = []
        
        # Market Overview
        sections.append(ReportSection(
            section_id="market_overview",
            title="Market Overview",
            description="Current state of the market, size, and key characteristics",
            subsections=[
                ReportSection(
                    section_id="market_definition",
                    title="Market Definition and Scope",
                    description="Define the market boundaries and segments"
                ),
                ReportSection(
                    section_id="market_size",
                    title="Market Size and Growth",
                    description="Current market size and historical growth rates"
                )
            ],
            content_requirements=["Market size data", "Growth statistics", "Market segments"]
        ))
        
        # Competitive Landscape
        sections.append(ReportSection(
            section_id="competitive_landscape",
            title="Competitive Landscape",
            description="Analysis of key players and competitive dynamics",
            subsections=[
                ReportSection(
                    section_id="key_players",
                    title="Key Market Players",
                    description="Overview of major companies and their market positions"
                ),
                ReportSection(
                    section_id="market_share",
                    title="Market Share Analysis",
                    description="Distribution of market share among competitors"
                )
            ],
            content_requirements=["Competitor profiles", "Market share data", "Competitive advantages"]
        ))
        
        # Market Trends and Drivers
        sections.append(ReportSection(
            section_id="market_trends",
            title="Market Trends and Drivers",
            description="Key trends, drivers, and factors influencing the market",
            subsections=[
                ReportSection(
                    section_id="growth_drivers",
                    title="Growth Drivers",
                    description="Factors driving market growth"
                ),
                ReportSection(
                    section_id="challenges",
                    title="Market Challenges",
                    description="Obstacles and challenges facing the market"
                )
            ],
            content_requirements=["Trend analysis", "Driver identification", "Challenge assessment"]
        ))
        
        # Only add forecast section for longer reports
        if page_count >= 20:
            sections.append(ReportSection(
                section_id="market_forecast",
                title="Market Forecast",
                description="Future projections and growth outlook",
                content_requirements=["Growth projections", "Future trends", "Scenario analysis"]
            ))
        
        return sections
    
    def _create_technology_analysis_sections(
        self,
        topic: str,
        requirements: str,
        page_count: int,
        include_analysis: bool
    ) -> List[ReportSection]:
        """Create sections for technology analysis reports."""
        sections = []
        
        sections.append(ReportSection(
            section_id="technology_overview",
            title="Technology Overview",
            description="Current state and evolution of the technology",
            subsections=[
                ReportSection(
                    section_id="tech_fundamentals",
                    title="Technical Fundamentals",
                    description="Core concepts and architecture"
                ),
                ReportSection(
                    section_id="tech_evolution",
                    title="Evolution and Maturity",
                    description="Historical development and current maturity level"
                )
            ]
        ))
        
        sections.append(ReportSection(
            section_id="use_cases",
            title="Use Cases and Applications",
            description="Practical applications and implementation examples"
        ))
        
        sections.append(ReportSection(
            section_id="tech_landscape",
            title="Technology Landscape",
            description="Ecosystem, vendors, and solution providers"
        ))
        
        return sections
    
    def _create_financial_analysis_sections(
        self,
        topic: str,
        requirements: str,
        page_count: int,
        include_analysis: bool,
        include_visualizations: bool
    ) -> List[ReportSection]:
        """Create sections for financial analysis reports."""
        sections = []
        
        sections.append(ReportSection(
            section_id="financial_overview",
            title="Financial Overview",
            description="Summary of financial performance and metrics",
            subsections=[
                ReportSection(
                    section_id="financial_performance",
                    title="Financial Performance",
                    description="Revenue, profitability, and key metrics"
                ),
                ReportSection(
                    section_id="valuation",
                    title="Valuation Analysis",
                    description="Valuation metrics and comparisons"
                )
            ]
        ))
        
        sections.append(ReportSection(
            section_id="financial_trends",
            title="Financial Trends",
            description="Historical trends and future outlook"
        ))
        
        return sections
    
    def _create_trend_analysis_sections(
        self,
        topic: str,
        requirements: str,
        page_count: int,
        include_analysis: bool,
        include_visualizations: bool
    ) -> List[ReportSection]:
        """Create sections for trend analysis reports."""
        sections = []
        
        sections.append(ReportSection(
            section_id="current_trends",
            title="Current Trends",
            description="Identification and analysis of current trends"
        ))
        
        sections.append(ReportSection(
            section_id="emerging_trends",
            title="Emerging Trends",
            description="Nascent trends and future directions"
        ))
        
        sections.append(ReportSection(
            section_id="trend_implications",
            title="Implications and Impact",
            description="Impact of trends on stakeholders"
        ))
        
        return sections
    
    def _create_comparative_analysis_sections(
        self,
        topic: str,
        requirements: str,
        page_count: int,
        include_analysis: bool
    ) -> List[ReportSection]:
        """Create sections for comparative analysis reports."""
        sections = []
        
        sections.append(ReportSection(
            section_id="comparison_criteria",
            title="Comparison Criteria",
            description="Factors and metrics used for comparison"
        ))
        
        sections.append(ReportSection(
            section_id="comparative_analysis",
            title="Comparative Analysis",
            description="Side-by-side comparison of subjects",
            subsections=[
                ReportSection(
                    section_id="strengths_weaknesses",
                    title="Strengths and Weaknesses",
                    description="Comparative strengths and weaknesses"
                ),
                ReportSection(
                    section_id="performance_comparison",
                    title="Performance Comparison",
                    description="Quantitative performance metrics"
                )
            ]
        ))
        
        return sections
    
    def _create_general_research_sections(
        self,
        topic: str,
        requirements: str,
        page_count: int,
        include_analysis: bool
    ) -> List[ReportSection]:
        """Create sections for general research reports."""
        sections = []
        
        sections.append(ReportSection(
            section_id="background",
            title="Background and Context",
            description="Historical background and current context"
        ))
        
        sections.append(ReportSection(
            section_id="key_findings",
            title="Key Findings",
            description="Main research findings and discoveries"
        ))
        
        sections.append(ReportSection(
            section_id="discussion",
            title="Discussion",
            description="Interpretation and implications of findings"
        ))
        
        return sections
    
    def _create_analysis_section(self, include_visualizations: bool) -> ReportSection:
        """Create the analysis section."""
        subsections = [
            ReportSection(
                section_id="data_analysis",
                title="Data Analysis",
                description="Statistical and quantitative analysis"
            ),
            ReportSection(
                section_id="insights",
                title="Key Insights",
                description="Critical insights derived from analysis"
            )
        ]
        
        if include_visualizations:
            subsections.append(ReportSection(
                section_id="visualizations",
                title="Data Visualizations",
                description="Charts, graphs, and visual representations"
            ))
        
        return ReportSection(
            section_id="analysis",
            title="Analysis",
            description="Detailed analysis of collected data",
            subsections=subsections,
            content_requirements=["Statistical analysis", "Insights", "Data patterns"]
        )
    
    def _create_conclusions_section(self, report_type: str) -> ReportSection:
        """Create the conclusions/recommendations section."""
        if report_type in ["market_research", "financial_analysis"]:
            title = "Conclusions and Recommendations"
            subsections = [
                ReportSection(
                    section_id="key_conclusions",
                    title="Key Conclusions",
                    description="Main conclusions from the research"
                ),
                ReportSection(
                    section_id="recommendations",
                    title="Strategic Recommendations",
                    description="Actionable recommendations for stakeholders"
                )
            ]
        else:
            title = "Conclusions"
            subsections = [
                ReportSection(
                    section_id="summary_findings",
                    title="Summary of Findings",
                    description="Summary of key research outcomes"
                ),
                ReportSection(
                    section_id="future_directions",
                    title="Future Directions",
                    description="Suggestions for future research or action"
                )
            ]
        
        return ReportSection(
            section_id="conclusions",
            title=title,
            description="Final conclusions and recommendations",
            subsections=subsections,
            content_requirements=["Summary", "Recommendations", "Action items"]
        )


def create_synthesizer_agent() -> SynthesizerAgent:
    """Factory function to create a synthesizer agent."""
    return SynthesizerAgent()

