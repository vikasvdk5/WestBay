"""
Straight-Through-LLM Agent - Direct content generation using LLM foundational knowledge.
Ensures every report section has comprehensive, meaningful content.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from observability.langsmith_config import trace_agent_call
from config import settings

logger = logging.getLogger(__name__)


class StraightThroughLLMAgent:
    """
    Straight-through-LLM agent that generates report content directly using LLM.
    Acts as a reliability guarantee - always provides content even when other agents fail.
    """
    
    def __init__(self):
        """Initialize the straight-through-LLM agent."""
        # Load agent prompt
        self.system_prompt = load_agent_prompt('straight_through_llm')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="straight_through_llm",
            system_prompt=self.system_prompt
        )
        
        logger.info("Straight-Through-LLM Agent initialized")
    
    @trace_agent_call("straight_through_llm")
    def execute(
        self,
        report_structure: Dict[str, Any],
        user_requirements: Dict[str, Any],
        research_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the straight-through-LLM agent.
        
        Args:
            report_structure: Report structure from synthesizer
            user_requirements: User's complete requirements
            research_data: Optional data from other agents
            context: Optional context with contribution_tracker
            
        Returns:
            Dictionary with generated content for all sections
        """
        try:
            # Get tracker from context
            tracker = context.get("contribution_tracker") if context else None
            agent_context = None
            
            # Log agent start
            if tracker:
                agent_context = tracker.log_agent_start(
                    agent_name="straight_through_llm",
                    agent_type="straight_through_llm",
                    task=f"Generate comprehensive content for {len(report_structure.get('sections', []))} report sections"
                )
            
            logger.info(f"Straight-Through-LLM generating content for report: {user_requirements.get('topic', 'Unknown')}")
            
            # Extract sections from report structure
            sections = report_structure.get("sections", [])
            if not sections:
                logger.warning("No sections found in report structure, using default")
                sections = [
                    {"id": "executive_summary", "title": "Executive Summary"},
                    {"id": "market_overview", "title": "Market Overview"},
                    {"id": "key_findings", "title": "Key Findings"}
                ]
            
            logger.info(f"Generating content for {len(sections)} sections")
            
            # Generate content for all sections
            section_contents = []
            for section in sections:
                content = self._generate_section_content(
                    section=section,
                    user_requirements=user_requirements,
                    research_data=research_data,
                    all_sections=sections
                )
                section_contents.append(content)
                
                # Log LLM usage for each section
                if tracker:
                    tracker.log_tool_usage(
                        tool_name="llm_content_generation",
                        tool_type="llm",
                        data_collected=f"Generated {content['word_count']} words for {content['section_title']}",
                        execution_time=0.0,
                        success=True,
                        metadata={"section_id": content["section_id"], "word_count": content["word_count"]}
                    )
            
            # Save generated content
            content_file = self._save_generated_content(
                user_requirements.get("topic", "report"),
                section_contents
            )
            
            result = {
                "agent": "straight_through_llm",
                "status": "completed",
                "section_contents": section_contents,
                "sections_generated": len(section_contents),
                "total_word_count": sum(s["word_count"] for s in section_contents),
                "content_file": str(content_file) if content_file else None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log agent completion
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Generated {len(section_contents)} sections with {result['total_word_count']} total words",
                    output_files=[str(content_file)] if content_file else [],
                    metrics={
                        "sections_generated": len(section_contents),
                        "total_word_count": result['total_word_count']
                    },
                    actions_taken=["content_generation", "llm_reasoning", "section_structuring"]
                )
            
            logger.info(f"Content generation completed: {len(section_contents)} sections, {result['total_word_count']} words")
            return result
            
        except Exception as e:
            # Log agent error
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Error during content generation: {str(e)}",
                    errors=[str(e)]
                )
            logger.error(f"Error in straight-through-LLM agent: {e}")
            raise
    
    def _generate_section_content(
        self,
        section: Dict[str, Any],
        user_requirements: Dict[str, Any],
        research_data: Optional[Dict[str, Any]],
        all_sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate content for a specific section.
        
        Args:
            section: Section specification
            user_requirements: User requirements
            research_data: Available research data
            all_sections: All sections for context
            
        Returns:
            Section content dictionary
        """
        section_id = section.get("id", "unknown")
        section_title = section.get("title", "Section")
        section_description = section.get("description", "")
        
        # Build context from research data
        research_context = ""
        if research_data:
            if research_data.get("web_data"):
                research_context += "\nAvailable web research data exists."
            if research_data.get("api_data"):
                research_context += "\nAvailable API data exists."
            if research_data.get("analysis"):
                research_context += "\nAvailable analysis insights exist."
        
        # Build prompt for content generation
        prompt = f"""Generate comprehensive,professional content for this report section.

REPORT TOPIC: {user_requirements.get('topic', 'Unknown')}

USER REQUIREMENTS:
{user_requirements.get('detailed_requirements', 'General analysis requested')}

Report Context:
- Page Count Target: {user_requirements.get('page_count', 10)} pages
- Complexity: {user_requirements.get('complexity', 'medium')}
- Include Analysis: {user_requirements.get('include_analysis', True)}
- Include Visualizations: {user_requirements.get('include_visualizations', True)}

SECTION TO GENERATE:
Title: {section_title}
ID: {section_id}
{f"Description: {section_description}" if section_description else ""}

{research_context}

INSTRUCTIONS:
1. Generate 250-400 words of substantial, professional content for this section
2. Use your knowledge base to provide factual, insightful information
3. Be specific with examples and details
4. Maintain professional business tone
5. Structure with clear paragraphs
6. NO placeholder text - provide complete, final content
7. If this is executive summary, synthesize key findings across all sections
8. Ensure content is directly relevant to the report topic and requirements

Generate ONLY the section content text, no JSON, no metadata, just the actual prose content for the section."""

        # Call LLM to generate content
        # Note: temperature and max_tokens are set at LLMExecutor initialization
        content_text = self.executor.llm_executor.invoke_with_system_prompt(
            system_prompt=self.system_prompt,
            user_message=prompt
        )
        
        # Clean up the content
        content_text = content_text.strip()
        
        # Remove any JSON-like artifacts if present
        if content_text.startswith('{') or content_text.startswith('['):
            # Try to extract just the content field
            try:
                parsed = json.loads(content_text)
                if isinstance(parsed, dict) and "content" in parsed:
                    content_text = parsed["content"]
            except:
                pass  # Keep original if parsing fails
        
        # Calculate word count
        word_count = len(content_text.split())
        
        # Extract key points (first few sentences)
        sentences = content_text.split('. ')
        key_points = [s.strip() + '.' for s in sentences[:3] if s.strip()]
        
        return {
            "section_id": section_id,
            "section_title": section_title,
            "content": content_text,
            "word_count": word_count,
            "key_points": key_points,
            "generated_by": "straight_through_llm",
            "confidence": "high"
        }
    
    def _save_generated_content(
        self,
        topic: str,
        section_contents: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """
        Save generated content to file.
        
        Args:
            topic: Research topic
            section_contents: Generated section contents
            
        Returns:
            Path to saved file
        """
        try:
            # Create directory
            content_dir = Path(settings.research_notes_dir)
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_content_{topic.replace(' ', '_')[:30]}_{timestamp}.json"
            filepath = content_dir / filename
            
            # Prepare data
            output_data = {
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "sections": section_contents,
                "total_sections": len(section_contents),
                "total_words": sum(s["word_count"] for s in section_contents)
            }
            
            # Write as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Generated content saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving generated content: {e}")
            return None

