"""
API Researcher Agent - Calls external APIs for data collection.
Processes API responses and tracks sources for citations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from agents.memory import CitationTracker
from tools.api_caller import APICallerTool, HTTPMethod
from observability.langsmith_config import trace_agent_call
from config import settings

logger = logging.getLogger(__name__)


class APIResearcherAgent:
    """
    API researcher agent that collects data from external APIs.
    Handles authentication, retries, and response processing.
    """
    
    def __init__(self):
        """Initialize the API researcher agent."""
        # Load agent prompt
        self.system_prompt = load_agent_prompt('api_researcher')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="api_researcher",
            system_prompt=self.system_prompt
        )
        
        # Initialize API caller tool
        self.api_caller = APICallerTool()
        
        # Initialize citation tracker
        self.citation_tracker = CitationTracker()
        
        logger.info("API Researcher Agent initialized")
    
    @trace_agent_call("api_researcher")
    def execute(
        self,
        api_requests: List[Dict[str, Any]],
        topic: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the API researcher agent.
        
        Args:
            api_requests: List of API request specifications
            topic: Research topic
            context: Optional context with contribution_tracker and assigned_tasks
            
        Returns:
            Dictionary with API data and citations
        """
        try:
            # Get tracker from context
            tracker = context.get("contribution_tracker") if context else None
            assigned_tasks = context.get("assigned_tasks", []) if context else []
            agent_context = None
            
            # Log agent start
            if tracker:
                agent_context = tracker.log_agent_start(
                    agent_name="api_researcher",
                    agent_type="api_researcher",
                    task=f"Call {len(api_requests)} APIs for topic: {topic[:80]}"
                )
            
            logger.info(f"API Researcher calling {len(api_requests)} APIs for topic: {topic}")
            
            # Make all API calls
            api_results = []
            for req in api_requests:
                result = self.api_caller.call_api(**req)
                api_results.append(result)
                
                # Log each API call
                if tracker:
                    tracker.log_tool_usage(
                        tool_name="api_caller",
                        tool_type="api_caller",
                        data_collected=f"API call to {req.get('url', 'unknown')}",
                        execution_time=0.0,
                        success=result["status"] == "success",
                        metadata={"url": req.get("url"), "method": req.get("method", "GET"), "status_code": result.get("status_code")}
                    )
            
            # Process results and track citations
            processed_data = []
            for result in api_results:
                if result["status"] == "success":
                    # Add citation
                    citation_num = self.citation_tracker.add_citation(
                        source=f"API: {result['url']}",
                        url=result["url"],
                        content_snippet=str(result["data"])[:200],
                        retrieved_at=datetime.fromisoformat(result["retrieved_at"])
                    )
                    
                    processed_data.append({
                        "url": result["url"],
                        "data": result["data"],
                        "citation_num": citation_num,
                        "retrieved_at": result["retrieved_at"],
                        "status_code": result["status_code"]
                    })
                else:
                    logger.warning(f"API call failed for {result['url']}: {result.get('error_message')}")
            
            # Save research notes
            notes_file = self._save_research_notes(topic, processed_data)
            
            result = {
                "agent": "api_researcher",
                "status": "completed",
                "topic": topic,
                "apis_called": len(processed_data),
                "apis_failed": len(api_results) - len(processed_data),
                "data": processed_data,
                "citations": self.citation_tracker.get_all_citations(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Log agent completion
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Called {len(processed_data)} APIs successfully, {len(api_results) - len(processed_data)} failed",
                    output_files=[str(notes_file)] if notes_file else [],
                    metrics={"apis_called": len(processed_data), "apis_failed": len(api_results) - len(processed_data)},
                    actions_taken=["api_calling", "data_collection", "citation_tracking"]
                )
            
            logger.info(f"API research completed: {len(processed_data)}/{len(api_requests)} successful")
            return result
            
        except Exception as e:
            # Log agent error
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Error during API research: {str(e)}",
                    errors=[str(e)]
                )
            logger.error(f"Error in API researcher agent: {e}")
            raise
    
    def _discover_apis_with_llm(
        self,
        topic: str,
        assigned_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to discover relevant free/public APIs for the research topic.
        
        Args:
            topic: Research topic
            assigned_tasks: Tasks assigned by lead researcher
            
        Returns:
            List of API request specifications
        """
        try:
            # Build context from assigned tasks
            tasks_context = "\n".join([
                f"- {task.get('description', '')}"
                for task in assigned_tasks[:3]
            ])
            
            # Create prompt for LLM to identify relevant APIs
            prompt = f"""Given this research topic and data collection tasks, identify 2-3 FREE/PUBLIC APIs that would provide relevant data.

Research Topic: {topic}

Specific Data Needs:
{tasks_context if tasks_context else "General research data on the topic"}

Instructions:
1. Think about what KIND of data is needed (financial, market, company, economic, etc.)
2. Identify FREE public APIs that provide this data (with free tiers or no authentication)
3. For each API, provide:
   - API name
   - Specific endpoint URL
   - Required parameters
   - Authentication type (if any)

Common Free APIs by category:
- Financial: Alpha Vantage, IEX Cloud, Yahoo Finance, Finnhub
- Company: OpenCorporates, Companies House  
- Economic: World Bank, FRED, IMF, OECD
- News: NewsAPI, GNews
- Technology: GitHub, Stack Exchange
- Market: No simple free APIs for detailed market research

Return a JSON array with 2-3 API specifications. Format:
[
  {{
    "api_name": "API Name",
    "url": "https://api.example.com/endpoint",
    "method": "GET",
    "params": {{"param1": "value1"}},
    "auth_type": "api_key" or "none",
    "description": "What data this provides"
  }}
]

If NO suitable free APIs exist for this topic, return an empty array: []

APIs:"""

            # Call LLM
            response = self.executor.call_llm(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # Parse response
            import json
            import re
            
            # Try to find JSON array
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                try:
                    apis = json.loads(json_match.group())
                    if isinstance(apis, list) and len(apis) > 0:
                        logger.info(f"LLM identified {len(apis)} relevant APIs")
                        return apis
                except json.JSONDecodeError:
                    logger.warning("Could not parse JSON from LLM response")
            
            # Check if LLM explicitly said no APIs available
            if "no suitable" in response.lower() or "not available" in response.lower() or response.strip() == "[]":
                logger.info("LLM determined no suitable public APIs available")
                return []
            
            logger.warning("Could not parse API specifications from LLM response")
            return []
            
        except Exception as e:
            logger.error(f"Error discovering APIs with LLM: {e}")
            return []
    
    def _save_research_notes(
        self,
        topic: str,
        data: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """
        Save API research notes to file.
        
        Args:
            topic: Research topic
            data: Collected API data
            
        Returns:
            Path to saved notes file
        """
        try:
            # Create research notes directory
            notes_dir = Path(settings.research_notes_dir)
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_research_{topic.replace(' ', '_')[:30]}_{timestamp}.txt"
            filepath = notes_dir / filename
            
            # Write notes
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== API RESEARCH NOTES ===\n")
                f.write(f"Topic: {topic}\n")
                f.write(f"Date: {datetime.now().isoformat()}\n")
                f.write(f"APIs Called: {len(data)}\n\n")
                
                for item in data:
                    f.write(f"--- API Source [{item['citation_num']}] ---\n")
                    f.write(f"URL: {item['url']}\n")
                    f.write(f"Status: {item['status_code']}\n")
                    f.write(f"Retrieved: {item['retrieved_at']}\n\n")
                    f.write(f"Data:\n{item['data']}\n\n")
                    f.write("-" * 80 + "\n\n")
            
            logger.info(f"API research notes saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving API research notes: {e}")
            return None
    
    def call_single_api(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convenience method to call a single API.
        
        Args:
            url: API endpoint URL
            method: HTTP method
            **kwargs: Additional arguments for API call
            
        Returns:
            API response dictionary
        """
        http_method = HTTPMethod[method.upper()]
        return self.api_caller.call_api(url, method=http_method, **kwargs)

