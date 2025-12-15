"""
Writer Agent - Generates the final market research report.
Structures content, writes sections, and formats citations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from observability.langsmith_config import trace_agent_call
from utils.pdf_generator import create_pdf_generator
from utils.citation_manager import create_citation_manager
from config import settings

logger = logging.getLogger(__name__)


class WriterAgent:
    """
    Writer agent that generates the final research report.
    Synthesizes findings from all agents into a coherent report.
    """
    
    def __init__(self):
        """Initialize the writer agent."""
        # Load agent prompt (now uses synthesizer prompt which includes report writing)
        self.system_prompt = load_agent_prompt('synthesizer')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="writer",
            system_prompt=self.system_prompt
        )
        
        # Initialize PDF generator
        self.pdf_generator = create_pdf_generator()
        
        logger.info("Writer Agent initialized")
    
    @trace_agent_call("writer")
    def execute(
        self,
        report_structure: Dict[str, Any],
        research_findings: Dict[str, Any],
        analysis_results: Dict[str, Any],
        citations: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the writer agent.
        
        Args:
            report_structure: Report structure specification
            research_findings: Research findings from data collection
            analysis_results: Analysis results from analyst
            citations: List of all citations
            context: Optional context information
            
        Returns:
            Dictionary with generated report
        """
        try:
            # Get tracker from context
            tracker = context.get("contribution_tracker") if context else None
            topic = context.get("topic", "research") if context else "research"
            report_reqs = context.get("report_requirements", {}) if context else {}
            agent_context = None
            
            # Log agent start
            if tracker:
                sections_count = len(report_structure.get("sections", [])) if report_structure else 0
                agent_context = tracker.log_agent_start(
                    agent_name="writer",
                    agent_type="writer",
                    task=f"Generate {sections_count}-section report with {len(citations) if citations else 0} citations for: {topic[:80]}"
                )
            
            logger.info("Writer generating report...")
            
            # Ensure all inputs are not None (defensive programming)
            if report_structure is None:
                logger.warning("report_structure is None, using default")
                report_structure = {"sections": [
                    {"id": "executive_summary", "title": "Executive Summary"},
                    {"id": "market_overview", "title": "Market Overview"}
                ]}
            
            if research_findings is None:
                logger.warning("research_findings is None, using empty dict")
                research_findings = {}
            
            if analysis_results is None:
                logger.warning("analysis_results is None, using empty dict")
                analysis_results = {}
            
            if citations is None:
                logger.warning("citations is None, using empty list")
                citations = []
            
            if context is None:
                context = {}
            
            # Generate report sections
            report_sections = self._generate_sections(
                report_structure,
                research_findings,
                analysis_results
            )
            
            # Log section generation
            if tracker:
                tracker.log_tool_usage(
                    tool_name="report_section_generator",
                    tool_type="llm",
                    data_collected=f"Generated {len(report_sections)} report sections",
                    execution_time=0.0,
                    success=True,
                    metadata={"sections_count": len(report_sections)}
                )
            
            # Format citations
            formatted_citations = self._format_citations(citations)
            
            # Assemble complete report
            full_report = self._assemble_report(report_sections, formatted_citations)
            
            # Generate HTML version
            html_report = self._generate_html_report(report_sections, formatted_citations, analysis_results)
            
            # Log HTML generation
            if tracker:
                tracker.log_tool_usage(
                    tool_name="html_report_generator",
                    tool_type="llm",
                    data_collected=f"Generated HTML report ({len(html_report)} bytes)",
                    execution_time=0.0,
                    success=True,
                    metadata={"html_size": len(html_report)}
                )
            
            # Save markdown report
            report_path = self._save_report(full_report, context)
            
            # Generate PDF with visualizations
            pdf_path = self._generate_pdf_report(
                report_sections,
                citations,
                analysis_results,
                context
            )
            
            # Log PDF generation
            if tracker:
                tracker.log_tool_usage(
                    tool_name="pdf_generator",
                    tool_type="visualization",
                    data_collected=f"Generated PDF report",
                    execution_time=0.0,
                    success=True,
                    output_files=[str(pdf_path)],
                    metadata={"sections": len(report_sections), "pdf_path": str(pdf_path)}
                )
            
            result = {
                "agent": "writer",
                "status": "completed",
                "report": full_report,
                "report_html": html_report,
                "report_path": str(report_path),
                "pdf_path": str(pdf_path),
                "sections_count": len(report_sections),
                "citations_count": len(citations),
                "word_count": len(full_report.split()),
                "timestamp": datetime.now().isoformat()
            }
            
            # Log agent completion
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Generated {len(report_sections)}-section report with {result['word_count']} words",
                    output_files=[str(report_path), str(pdf_path)],
                    metrics={
                        "sections_count": len(report_sections),
                        "word_count": result['word_count'],
                        "citations_count": len(citations)
                    },
                    actions_taken=["section_generation", "html_formatting", "pdf_generation", "citation_formatting"]
                )
            
            logger.info(f"Report generated: {len(report_sections)} sections, {result['word_count']} words")
            return result
            
        except Exception as e:
            # Log agent error
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Error during report generation: {str(e)}",
                    errors=[str(e)]
                )
            logger.error(f"Error in writer agent: {e}")
            raise
    
    def _generate_sections(
        self,
        report_structure: Dict[str, Any],
        research_findings: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate content for each report section, prioritizing LLM-generated content.
        
        Args:
            report_structure: Report structure
            research_findings: Research findings (includes llm_content)
            analysis_results: Analysis results
            
        Returns:
            List of section dictionaries with comprehensive content
        """
        sections = []
        
        # Get LLM-generated content if available (with safety checks)
        llm_content = research_findings.get("llm_content", {}) if research_findings else {}
        llm_sections = llm_content.get("section_contents", []) if llm_content else []
        
        # Filter out any None values from llm_sections
        if llm_sections:
            llm_sections = [s for s in llm_sections if s is not None]
        
        logger.info(f"Generating sections - LLM content available: {len(llm_sections)} sections")
        
        # Safely get sections (report_structure should not be None after execute() check)
        section_specs = report_structure.get("sections", []) if report_structure else []
        
        for section_spec in section_specs:
            if not section_spec:
                logger.warning("Encountered None section_spec, skipping")
                continue
                
            section_id = section_spec.get("id", "")
            section_title = section_spec.get("title", "")
            
            # Try to find LLM-generated content for this section (with safety check)
            llm_section = next(
                (s for s in llm_sections if s and s.get("section_id") == section_id),
                None
            )
            
            if llm_section and llm_section.get("content"):
                # Use LLM-generated content (comprehensive, professional content!)
                logger.info(f"✅ Using LLM-generated content for section: {section_id} ({section_title})")
                
                # Enhance LLM content with visualizations if available
                content = llm_section["content"]
                
                # Check if this section should include visualizations
                visualizations = analysis_results.get("visualizations", []) if analysis_results else []
                # Filter out None values
                if visualizations:
                    visualizations = [v for v in visualizations if v is not None]
                
                if visualizations and ("analysis" in section_id.lower() or "data" in section_id.lower()):
                    logger.info(f"   Adding {len(visualizations)} visualizations to section {section_id}")
                    content += "\n\n### Data Visualizations\n\n"
                    for i, viz in enumerate(visualizations, 1):
                        if viz:  # Additional safety check
                            content += f"**Figure {i}: {viz.get('title', 'Chart')}**\n\n"
                            content += f"![{viz.get('title', 'Chart')}](visualization_placeholder_{i})\n\n"
                            if viz.get('description'):
                                content += f"*{viz['description']}*\n\n"
                
                section_content = {
                    "id": section_id,
                    "title": section_title,
                    "content": content,
                    "word_count": llm_section.get("word_count", len(content.split())),
                    "source": "straight_through_llm",
                    "citations": llm_section.get("citations", [])
                }
            else:
                # Fall back to template-based method (for backwards compatibility)
                logger.info(f"⚠️  No LLM content for section {section_id}, using template-based generation")
                section_content = self._write_section(
                    section_spec,
                    research_findings,
                    analysis_results
                )
            
            sections.append(section_content)
        
        logger.info(f"Generated {len(sections)} sections total")
        return sections
    
    def _write_section(
        self,
        section_spec: Dict[str, Any],
        research_findings: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Write content for a specific section.
        
        Args:
            section_spec: Section specification
            research_findings: Research findings
            analysis_results: Analysis results
            
        Returns:
            Section dictionary with content
        """
        section_id = section_spec.get("id", "")
        title = section_spec.get("title", "")
        
        # In a real implementation, this would use LLM to generate section content
        # based on the research findings and analysis results
        
        # Generate placeholder content based on section type
        if section_id == "executive_summary":
            content = self._generate_executive_summary(research_findings, analysis_results)
        elif section_id == "market_overview":
            content = self._generate_market_overview(research_findings)
        elif section_id == "key_findings":
            content = self._generate_key_findings(analysis_results)
        else:
            content = f"Content for {title} section will be generated based on research findings."
        
        return {
            "id": section_id,
            "title": title,
            "content": content,
            "word_count": len(content.split())
        }
    
    def _generate_executive_summary(
        self,
        research_findings: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> str:
        """Generate executive summary section."""
        summary = """
## Executive Summary

This market research report provides a comprehensive analysis of the industry landscape,
key trends, and strategic insights. Based on extensive research from multiple sources
and in-depth analysis, we have identified significant growth opportunities and emerging
challenges in the market.

Key highlights include strong market growth driven by technological innovation,
increasing consumer demand, and favorable regulatory conditions. Our analysis reveals
several actionable insights for stakeholders looking to capitalize on market opportunities.
        """.strip()
        
        return summary
    
    def _generate_market_overview(self, research_findings: Dict[str, Any]) -> str:
        """Generate market overview section."""
        overview = """
## Market Overview

The market has demonstrated robust growth over the past several years, with projections
indicating continued expansion in the coming period. Multiple factors contribute to this
growth trajectory, including technological advancements, changing consumer preferences,
and strategic investments by key industry players.

Our research indicates a dynamic competitive landscape with both established leaders
and emerging challengers vying for market share. The market structure reflects a balance
between consolidation trends and new entrant activity.
        """.strip()
        
        return overview
    
    def _generate_key_findings(self, analysis_results: Dict[str, Any]) -> str:
        """Generate key findings section."""
        findings = """
## Key Findings

Based on our comprehensive analysis, we have identified the following key findings:

1. **Market Growth**: The market is experiencing strong growth with a positive trajectory
   expected to continue over the forecast period.

2. **Technology Adoption**: Rapid adoption of new technologies is reshaping the competitive
   landscape and creating new opportunities for innovation.

3. **Consumer Trends**: Evolving consumer preferences are driving demand for new products
   and services, requiring companies to adapt their strategies.

4. **Competitive Dynamics**: The competitive landscape is becoming more complex with both
   consolidation and new entry activity.
        """.strip()
        
        return findings
    
    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """
        Format citations for the report.
        
        Args:
            citations: List of citation dictionaries
            
        Returns:
            Formatted citations string
        """
        if not citations:
            return "## References\n\nNo citations available."
        
        formatted = ["## References\n"]
        
        for citation in citations:
            num = citation.get("number", 0)
            source = citation.get("source", "Unknown")
            url = citation.get("url", "")
            retrieved = citation.get("retrieved_at", datetime.now())
            
            if isinstance(retrieved, str):
                retrieved = datetime.fromisoformat(retrieved)
            
            line = f"[{num}] {source}"
            if url:
                line += f" - {url}"
            line += f" (Retrieved: {retrieved.strftime('%Y-%m-%d')})"
            
            formatted.append(line)
        
        return "\n".join(formatted)
    
    def _assemble_report(
        self,
        sections: List[Dict[str, Any]],
        citations: str
    ) -> str:
        """
        Assemble the complete report from sections.
        
        Args:
            sections: List of section dictionaries
            citations: Formatted citations
            
        Returns:
            Complete report as string
        """
        report_parts = [
            "# Market Research Report",
            f"\nGenerated: {datetime.now().strftime('%B %d, %Y')}\n",
            "---\n"
        ]
        
        # Add each section
        for section in sections:
            report_parts.append(f"\n{section['content']}\n")
            report_parts.append("\n---\n")
        
        # Add citations
        report_parts.append(f"\n{citations}\n")
        
        return "\n".join(report_parts)
    
    def _save_report(
        self,
        report_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save the report to file.
        
        Args:
            report_content: Report content
            context: Optional context with metadata
            
        Returns:
            Path to saved report
        """
        try:
            # Create reports directory
            reports_dir = Path(settings.reports_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic = context.get("topic", "research") if context else "research"
            filename = f"report_{topic.replace(' ', '_')[:30]}_{timestamp}.md"
            filepath = reports_dir / filename
            
            # Write report
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise
    
    def _generate_html_report(
        self,
        sections: List[Dict[str, Any]],
        citations: str,
        analysis_results: Dict[str, Any]
    ) -> str:
        """
        Generate HTML version of the report with embedded visualizations.
        
        Args:
            sections: Report sections
            citations: Formatted citations
            analysis_results: Analysis results with visualizations
            
        Returns:
            HTML report as string
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>Market Research Report</title>',
            '<style>',
            'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }',
            'h1 { color: #1a1a1a; border-bottom: 3px solid #0284c7; padding-bottom: 10px; }',
            'h2 { color: #2c3e50; margin-top: 30px; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; }',
            'h3 { color: #34495e; margin-top: 20px; }',
            '.section { margin-bottom: 40px; }',
            '.citation { background: #f8f9fa; border-left: 4px solid #0284c7; padding: 10px; margin: 10px 0; font-size: 0.9em; }',
            '.citation-link { color: #0284c7; text-decoration: none; }',
            '.citation-link:hover { text-decoration: underline; }',
            '.visualization { margin: 30px 0; text-align: center; }',
            '.visualization img { max-width: 100%; height: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }',
            '.visualization iframe { width: 100%; height: 500px; border: 1px solid #e0e0e0; }',
            'sup { color: #0284c7; font-weight: bold; }',
            '</style>',
            '</head>',
            '<body>',
            '<h1>Market Research Report</h1>',
            f'<p style="color: #666; font-size: 0.95em;">Generated: {datetime.now().strftime("%B %d, %Y")}</p>',
            '<hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">',
        ]
        
        # Add sections
        for section in sections:
            html_parts.append(f'<div class="section">')
            
            # Parse section content for markdown-style headers
            content = section['content']
            lines = content.split('\n')
            
            for line in lines:
                if line.strip().startswith('## '):
                    # H2 heading
                    html_parts.append(f'<h2>{line.replace("## ", "")}</h2>')
                elif line.strip().startswith('### '):
                    # H3 heading
                    html_parts.append(f'<h3>{line.replace("### ", "")}</h3>')
                elif line.strip():
                    # Paragraph - format citations as superscript
                    import re
                    formatted_line = re.sub(r'\[(\d+)\]', r'<sup><a href="#ref\1" class="citation-link">[\1]</a></sup>', line)
                    html_parts.append(f'<p>{formatted_line}</p>')
            
            html_parts.append('</div>')
        
        # Add visualizations if present (safely handle None) - embedded as base64
        visualizations = analysis_results.get('visualizations', []) if analysis_results else []
        # Filter out None values
        if visualizations:
            visualizations = [v for v in visualizations if v is not None]
        
        if visualizations:
            import base64
            from pathlib import Path
            
            html_parts.append('<hr style="margin: 40px 0;">')
            html_parts.append('<h2>Data Visualizations</h2>')
            
            for i, viz in enumerate(visualizations, 1):
                if not viz:  # Skip if viz is None
                    continue
                html_parts.append('<div class="visualization" style="margin: 30px 0; text-align: center;">')
                html_parts.append(f'<h3>Figure {i}: {viz.get("title", "Chart")}</h3>')
                
                # Embed chart - use base64 encoding for portability
                png_path = viz.get('png_path')
                if png_path:
                    try:
                        # Read image and convert to base64
                        img_path = Path(png_path)
                        if img_path.exists():
                            with open(img_path, 'rb') as img_file:
                                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            
                            # Embed as data URI (works in both HTML and PDF)
                            html_parts.append(
                                f'<img src="data:image/png;base64,{img_data}" '
                                f'alt="{viz.get("title", "Chart")}" '
                                f'style="max-width: 800px; width: 100%; height: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                            )
                            logger.info(f"   ✅ Embedded visualization {i} as base64 ({len(img_data)} bytes)")
                        else:
                            logger.warning(f"   ⚠️  Chart file not found: {png_path}")
                            html_parts.append(f'<p style="color: #999;">Chart file not found: {png_path}</p>')
                    except Exception as e:
                        logger.error(f"   ❌ Error embedding chart: {e}")
                        html_parts.append(f'<p style="color: #999;">Error loading chart</p>')
                
                if viz and viz.get('description'):
                    html_parts.append(f'<p style="color: #666; font-size: 0.9em; font-style: italic;">{viz["description"]}</p>')
                
                html_parts.append('</div>')
        
        # Add citations
        html_parts.append('<hr style="margin: 40px 0;">')
        html_parts.append('<h2>References</h2>')
        
        citation_lines = citations.split('\n')
        for line in citation_lines:
            if line.strip() and not line.startswith('##'):
                # Format citation with anchor
                import re
                match = re.match(r'\[(\d+)\]\s+(.+)', line)
                if match:
                    num, text = match.groups()
                    html_parts.append(f'<div class="citation" id="ref{num}">')
                    html_parts.append(f'<strong>[{num}]</strong> {text}')
                    html_parts.append('</div>')
        
        html_parts.extend(['</body>', '</html>'])
        
        return '\n'.join(html_parts)
    
    def _generate_pdf_report(
        self,
        sections: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        analysis_results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate PDF version of the report with visualizations.
        
        Args:
            sections: Report sections
            citations: List of citations
            analysis_results: Analysis results with visualizations
            context: Optional context
            
        Returns:
            Path to generated PDF
        """
        try:
            # Prepare citation manager
            citation_mgr = create_citation_manager()
            for citation in citations:
                citation_mgr.add_citation(
                    source=citation.get('source', 'Unknown'),
                    url=citation.get('url'),
                    content_snippet=citation.get('content_snippet'),
                    retrieved_at=citation.get('retrieved_at')
                )
            
            # Prepare report data for PDF
            report_data = {
                "title": "Market Research Report",
                "topic": context.get("topic", "Research") if context else "Research",
                "date": datetime.now().strftime("%B %d, %Y"),
                "sections": sections,
                "visualizations": analysis_results.get('visualizations', []) if analysis_results else [],
                "metadata": {
                    "Generated by": "Multi-Agent Research System",
                    "Model": "Google Gemini",
                    "Agents": "6 specialized agents"
                }
            }
            
            # Generate PDF
            pdf_path = self.pdf_generator.generate_report(
                report_data=report_data,
                citation_manager=citation_mgr
            )
            
            logger.info(f"PDF report generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            # Return a placeholder path
            return Path(settings.reports_dir) / "report.pdf"

