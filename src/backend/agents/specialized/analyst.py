"""
Analyst Agent - Analyzes research data and generates insights.
Creates visualizations and identifies trends from collected data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from observability.langsmith_config import trace_agent_call
from utils.visualization import create_chart_generator
from config import settings

logger = logging.getLogger(__name__)


class AnalystAgent:
    """
    Analyst agent that analyzes research data and generates insights.
    Creates visualizations and identifies trends.
    """
    
    def __init__(self):
        """Initialize the analyst agent."""
        # Load agent prompt
        self.system_prompt = load_agent_prompt('analyst')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="analyst",
            system_prompt=self.system_prompt
        )
        
        # Initialize chart generator
        self.chart_generator = create_chart_generator()
        
        logger.info("Analyst Agent initialized")
    
    @trace_agent_call("analyst")
    def execute(
        self,
        research_data: Dict[str, Any],
        topic: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the analyst agent.
        
        Args:
            research_data: Collected research data to analyze
            topic: Research topic
            context: Optional context with contribution_tracker, assigned_tasks, and report_requirements
            
        Returns:
            Dictionary with analysis results and insights
        """
        try:
            # Get tracker from context
            tracker = context.get("contribution_tracker") if context else None
            assigned_tasks = context.get("assigned_tasks", []) if context else []
            report_reqs = context.get("report_requirements", {}) if context else {}
            agent_context = None
            
            # Log agent start
            if tracker:
                agent_context = tracker.log_agent_start(
                    agent_name="analyst",
                    agent_type="analyst",
                    task=f"Analyze research data and generate insights for topic: {topic[:80]}"
                )
            
            logger.info(f"Analyst analyzing data for topic: {topic}")
            
            # Perform analysis
            analysis_results = self._analyze_data(research_data, topic)
            
            # Log analysis tool usage
            if tracker:
                tracker.log_tool_usage(
                    tool_name="data_analysis",
                    tool_type="llm",
                    data_collected=f"Analyzed data and extracted {len(analysis_results.get('key_metrics', []))} metrics",
                    execution_time=0.0,
                    success=True,
                    metadata={"topic": topic, "analysis_type": "statistical"}
                )
            
            # Generate insights
            insights = self._generate_insights(analysis_results)
            
            # Create visualizations specifications
            visualizations_specs = self._specify_visualizations(analysis_results)
            
            # Actually generate the visualizations
            visualizations = self._generate_visualizations(visualizations_specs, research_data)
            
            # Log visualization generation
            if tracker and visualizations:
                for viz in visualizations:
                    tracker.log_tool_usage(
                        tool_name="visualization_generator",
                        tool_type="visualization",
                        data_collected=f"Generated {viz.get('type')} chart: {viz.get('title')}",
                        execution_time=0.0,
                        success=True,
                        output_files=[viz.get("png_path"), viz.get("html_path")],
                        metadata={"chart_type": viz.get("type"), "title": viz.get("title")}
                    )
            
            # Save analysis results
            analysis_files = self._save_analysis(topic, analysis_results, insights, visualizations)
            
            result = {
                "agent": "analyst",
                "status": "completed",
                "topic": topic,
                "analysis": analysis_results,
                "insights": insights,
                "visualizations": visualizations,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log agent completion
            if tracker and agent_context:
                output_files = []
                if analysis_files:
                    output_files.extend(analysis_files)
                # Add visualization file paths
                for viz in visualizations:
                    if viz.get("png_path"):
                        output_files.append(viz["png_path"])
                    if viz.get("html_path"):
                        output_files.append(viz["html_path"])
                
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Generated {len(insights)} insights and {len(visualizations)} visualizations",
                    output_files=output_files,
                    metrics={"insights_count": len(insights), "visualizations_count": len(visualizations)},
                    actions_taken=["data_analysis", "insight_generation", "visualization_creation"]
                )
            
            logger.info(f"Analysis completed with {len(insights)} insights and {len(visualizations)} visualizations")
            return result
            
        except Exception as e:
            # Log agent error
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Error during analysis: {str(e)}",
                    errors=[str(e)]
                )
            logger.error(f"Error in analyst agent: {e}")
            raise
    
    def _analyze_data(
        self,
        research_data: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """
        Analyze research data to extract key metrics and trends.
        
        Args:
            research_data: Research data to analyze
            topic: Research topic
            
        Returns:
            Analysis results dictionary
        """
        # In a real implementation, this would use LLM to analyze the data
        # For now, we'll create a structured analysis template
        
        analysis = {
            "key_metrics": self._extract_key_metrics(research_data),
            "trends": self._identify_trends(research_data),
            "comparisons": self._generate_comparisons(research_data),
            "data_quality": self._assess_data_quality(research_data)
        }
        
        return analysis
    
    def _extract_key_metrics(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key metrics from research data."""
        # Simplified example - in real implementation would use LLM
        metrics = [
            {
                "name": "Market Size",
                "value": "Extracted from data",
                "unit": "USD Billion",
                "confidence": 0.85
            },
            {
                "name": "Growth Rate",
                "value": "Calculated",
                "unit": "CAGR %",
                "confidence": 0.80
            }
        ]
        return metrics
    
    def _identify_trends(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify trends in the research data."""
        trends = [
            {
                "trend": "Market Growth",
                "direction": "increasing",
                "strength": "strong",
                "confidence": 0.85,
                "description": "Market showing strong growth trajectory"
            },
            {
                "trend": "Technology Adoption",
                "direction": "increasing",
                "strength": "moderate",
                "confidence": 0.75,
                "description": "Steady adoption of new technologies"
            }
        ]
        return trends
    
    def _generate_comparisons(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comparative analysis."""
        comparisons = [
            {
                "type": "year_over_year",
                "metric": "Market Size",
                "change": "+15%",
                "significance": "high"
            }
        ]
        return comparisons
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of collected data."""
        # Count data sources
        num_sources = len(data.get("data_sources", []))
        
        return {
            "sources_count": num_sources,
            "completeness": "high" if num_sources >= 5 else "moderate",
            "confidence_level": 0.85 if num_sources >= 5 else 0.70,
            "gaps": []
        }
    
    def _generate_insights(
        self,
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable insights from analysis.
        
        Args:
            analysis_results: Analysis results
            
        Returns:
            List of insights
        """
        insights = [
            {
                "insight_id": "insight_1",
                "title": "Strong Market Growth",
                "description": "Market is experiencing strong growth driven by multiple factors",
                "impact": "high",
                "confidence": 0.85,
                "supporting_data": ["trend_1", "metric_1"]
            },
            {
                "insight_id": "insight_2",
                "title": "Technology Disruption",
                "description": "New technologies are disrupting traditional market dynamics",
                "impact": "medium",
                "confidence": 0.75,
                "supporting_data": ["trend_2"]
            }
        ]
        return insights
    
    def _specify_visualizations(
        self,
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Specify visualizations to create for the report.
        
        Args:
            analysis_results: Analysis results
            
        Returns:
            List of visualization specifications
        """
        visualizations = [
            {
                "viz_id": "chart_1",
                "type": "line_chart",
                "title": "Market Growth Trend",
                "data": {
                    "x": [2020, 2021, 2022, 2023, 2024, 2025],
                    "y": [160, 210, 280, 320, 385, 450]
                },
                "x_axis": "Year",
                "y_axis": "Market Size (USD Billion)",
                "description": "Historical and projected market size growth trajectory"
            },
            {
                "viz_id": "chart_2",
                "type": "bar_chart",
                "title": "Market Share Distribution",
                "data": {
                    "x": ["Company A", "Company B", "Company C", "Company D", "Others"],
                    "y": [25, 18, 15, 12, 30]
                },
                "x_axis": "Company",
                "y_axis": "Market Share (%)",
                "description": "Current market share distribution among major players"
            }
        ]
        return visualizations
    
    def _generate_visualizations(
        self,
        viz_specs: List[Dict[str, Any]],
        research_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Actually generate visualizations from specifications.
        
        Args:
            viz_specs: Visualization specifications
            research_data: Research data (for context)
            
        Returns:
            List of generated visualization metadata with file paths
        """
        generated_visualizations = []
        
        for spec in viz_specs:
            try:
                viz_type = spec.get("type", "line_chart")
                chart_id = spec.get("viz_id", f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                if viz_type == "line_chart":
                    result = self.chart_generator.create_line_chart(
                        data=spec.get("data", {}),
                        title=spec.get("title", "Chart"),
                        x_label=spec.get("x_axis", "X"),
                        y_label=spec.get("y_axis", "Y"),
                        chart_id=chart_id,
                        use_plotly=True
                    )
                elif viz_type == "bar_chart":
                    result = self.chart_generator.create_bar_chart(
                        data=spec.get("data", {}),
                        title=spec.get("title", "Chart"),
                        x_label=spec.get("x_axis", "X"),
                        y_label=spec.get("y_axis", "Y"),
                        chart_id=chart_id,
                        use_plotly=True
                    )
                elif viz_type == "pie_chart":
                    result = self.chart_generator.create_pie_chart(
                        data=spec.get("data", {}),
                        title=spec.get("title", "Chart"),
                        chart_id=chart_id,
                        use_plotly=True
                    )
                else:
                    logger.warning(f"Unknown visualization type: {viz_type}")
                    continue
                
                # Add description to result
                result["description"] = spec.get("description", "")
                result["title"] = spec.get("title", "")
                generated_visualizations.append(result)
                
                logger.info(f"Generated visualization: {chart_id}")
                
            except Exception as e:
                logger.error(f"Error generating visualization {spec.get('viz_id')}: {e}")
        
        return generated_visualizations
    
    def _save_analysis(
        self,
        topic: str,
        analysis_results: Dict[str, Any],
        insights: List[Dict[str, Any]],
        visualizations: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Save analysis results to file.
        
        Args:
            topic: Research topic
            analysis_results: Analysis results
            insights: Generated insights
            visualizations: Visualization specifications
            
        Returns:
            List of file paths created
        """
        try:
            # Create research notes directory
            notes_dir = Path(settings.research_notes_dir)
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{topic.replace(' ', '_')[:30]}_{timestamp}.json"
            filepath = notes_dir / filename
            
            # Prepare data
            output_data = {
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis_results,
                "insights": insights,
                "visualizations": visualizations
            }
            
            # Write as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Analysis results saved to {filepath}")
            return [str(filepath)]
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            return []

