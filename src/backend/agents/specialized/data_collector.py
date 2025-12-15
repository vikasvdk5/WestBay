"""
Data Collector Agent - Performs web scraping to collect research data.
Extracts content from URLs and tracks sources for citations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agents.prompt_loader import load_agent_prompt
from agents.executor import AgentExecutor
from agents.memory import CitationTracker
from tools.web_scraper import WebScraperTool
from observability.langsmith_config import trace_agent_call
from config import settings

logger = logging.getLogger(__name__)


class DataCollectorAgent:
    """
    Data collector agent that scrapes web content for research.
    Uses predefined URLs and tracks sources for proper citation.
    """
    
    def __init__(self):
        """Initialize the data collector agent."""
        # Load agent prompt
        self.system_prompt = load_agent_prompt('data_collector')
        
        # Initialize executor
        self.executor = AgentExecutor(
            agent_name="data_collector",
            system_prompt=self.system_prompt
        )
        
        # Initialize web scraper tool
        self.web_scraper = WebScraperTool()
        
        # Initialize citation tracker
        self.citation_tracker = CitationTracker()
        
        logger.info("Data Collector Agent initialized")
    
    @trace_agent_call("data_collector")
    def execute(
        self,
        urls: List[str],
        topic: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the data collector agent.
        
        Args:
            urls: List of URLs to scrape
            topic: Research topic
            context: Optional context with contribution_tracker and assigned_tasks
            
        Returns:
            Dictionary with scraped data and citations
        """
        try:
            # Get tracker from context
            tracker = context.get("contribution_tracker") if context else None
            assigned_tasks = context.get("assigned_tasks", []) if context else []
            agent_context = None
            
            # Log agent start
            if tracker:
                agent_context = tracker.log_agent_start(
                    agent_name="data_collector",
                    agent_type="data_collector",
                    task=f"Scrape {len(urls)} URLs for topic: {topic[:80]}"
                )
            
            logger.info(f"Data Collector scraping {len(urls)} URLs for topic: {topic}")
            
            # If no URLs provided, use LLM to find relevant URLs
            if not urls or urls == ["https://example.com/market-data"]:
                logger.info("No valid URLs provided, using LLM to find relevant sources...")
                urls = self._find_relevant_urls_with_llm(topic, assigned_tasks)
                logger.info(f"LLM identified {len(urls)} relevant URLs to scrape")
            
            # Scrape all URLs
            scrape_results = self.web_scraper.scrape_multiple_urls(urls)
            
            # Log tool usage
            if tracker:
                tracker.log_tool_usage(
                    tool_name="web_scraper",
                    tool_type="web_scraper",
                    data_collected=f"Scraped {len(scrape_results)} URLs",
                    execution_time=0.0,  # Would need to track actual time
                    success=True,
                    metadata={"urls_count": len(urls), "success_count": len(scrape_results)}
                )
            
            # Process results and track citations
            processed_data = []
            for result in scrape_results:
                if result["status"] == "success":
                    # Add citation
                    citation_num = self.citation_tracker.add_citation(
                        source=result["title"],
                        url=result["url"],
                        content_snippet=result["content"][:200] if result["content"] else None,
                        retrieved_at=datetime.fromisoformat(result["retrieved_at"])
                    )
                    
                    processed_data.append({
                        "url": result["url"],
                        "title": result["title"],
                        "content": result["content"],
                        "citation_num": citation_num,
                        "retrieved_at": result["retrieved_at"]
                    })
                else:
                    logger.warning(f"Failed to scrape {result['url']}: {result.get('error')}")
            
            # Save research notes
            notes_file = self._save_research_notes(topic, processed_data)
            
            result = {
                "agent": "data_collector",
                "status": "completed",
                "topic": topic,
                "urls_scraped": len(processed_data),
                "urls_failed": len(scrape_results) - len(processed_data),
                "data": processed_data,
                "citations": self.citation_tracker.get_all_citations(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Log agent completion
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Scraped {len(processed_data)} URLs successfully, {len(urls) - len(processed_data)} failed",
                    output_files=[str(notes_file)] if notes_file else [],
                    metrics={"urls_scraped": len(processed_data), "urls_failed": len(urls) - len(processed_data)},
                    actions_taken=["web_scraping", "citation_tracking", "data_processing"]
                )
            
            logger.info(f"Data collection completed: {len(processed_data)}/{len(urls)} successful")
            return result
            
        except Exception as e:
            # Log agent error
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Error during data collection: {str(e)}",
                    errors=[str(e)]
                )
            logger.error(f"Error in data collector agent: {e}")
            raise
    
    def _find_relevant_urls_with_llm(
        self,
        topic: str,
        assigned_tasks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Use LLM to identify 3-5 relevant URLs for the research topic.
        
        Args:
            topic: Research topic
            assigned_tasks: Tasks assigned by lead researcher
            
        Returns:
            List of relevant URLs to scrape
        """
        try:
            # Build context from assigned tasks
            tasks_context = "\n".join([
                f"- {task.get('description', '')}"
                for task in assigned_tasks[:3]  # Use first 3 tasks for context
            ])
            
            # Create prompt for LLM to find relevant URLs
            prompt = f"""Given this research topic and specific data collection tasks, identify 3-5 specific, authoritative URLs that would contain relevant information.

Research Topic: {topic}

Specific Tasks:
{tasks_context if tasks_context else "General research on the topic"}

Instructions:
1. Think about where authoritative information on this topic would be published
2. Consider: official company sites, government data, reputable news, research papers, industry reports
3. Provide SPECIFIC URLs (not just domain names)
4. Ensure URLs are likely to be publicly accessible (avoid paywalls)
5. Prioritize data-rich sources over general information pages

Return ONLY a JSON array of 3-5 URLs, nothing else.
Example format: ["https://example.com/article1", "https://example2.com/data", ...]

URLs:"""

            # Call LLM to get URLs
            response = self.executor.call_llm(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more focused results
                max_tokens=500
            )
            
            # Parse response to extract URLs
            import json
            import re
            
            # Try to find JSON array in response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                try:
                    urls = json.loads(json_match.group())
                    # Validate URLs
                    valid_urls = [
                        url for url in urls
                        if isinstance(url, str) and url.startswith(('http://', 'https://'))
                    ]
                    if valid_urls:
                        logger.info(f"LLM found {len(valid_urls)} valid URLs")
                        return valid_urls[:5]  # Limit to 5 URLs
                except json.JSONDecodeError:
                    logger.warning("Could not parse JSON from LLM response")
            
            # Fallback: extract any URLs from the response
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            found_urls = re.findall(url_pattern, response)
            if found_urls:
                # Clean and validate URLs
                cleaned_urls = []
                for url in found_urls:
                    if not url.startswith('http'):
                        url = 'https://' + url
                    cleaned_urls.append(url.rstrip('.,;:)]}'))
                logger.info(f"Extracted {len(cleaned_urls)} URLs from LLM response")
                return cleaned_urls[:5]
            
            # If LLM couldn't find URLs, return some generic fallbacks based on topic
            logger.warning("LLM could not identify specific URLs, using topic-based defaults")
            return self._get_fallback_urls(topic)
            
        except Exception as e:
            logger.error(f"Error using LLM to find URLs: {e}")
            # Return fallback URLs
            return self._get_fallback_urls(topic)
    
    def _get_fallback_urls(self, topic: str) -> List[str]:
        """
        Provide fallback URLs based on topic keywords.
        
        Args:
            topic: Research topic
            
        Returns:
            List of fallback URLs
        """
        topic_lower = topic.lower()
        urls = []
        
        # Check for company names and add investor relations
        companies = ['apple', 'google', 'microsoft', 'amazon', 'tesla', 'meta', 'netflix']
        for company in companies:
            if company in topic_lower:
                urls.append(f"https://investor.{company}.com")
                break
        
        # Add general research sources
        if 'market' in topic_lower or 'industry' in topic_lower:
            urls.extend([
                "https://www.statista.com",
                "https://www.ibisworld.com"
            ])
        
        if 'financial' in topic_lower or 'stock' in topic_lower:
            urls.extend([
                "https://finance.yahoo.com",
                "https://www.sec.gov"
            ])
        
        if 'technology' in topic_lower or 'tech' in topic_lower:
            urls.extend([
                "https://techcrunch.com",
                "https://www.theverge.com"
            ])
        
        # Generic fallbacks if nothing specific found
        if not urls:
            urls = [
                "https://www.reuters.com",
                "https://www.bloomberg.com",
                "https://www.wsj.com"
            ]
        
        return urls[:3]  # Return top 3
    
    def _save_research_notes(
        self,
        topic: str,
        data: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """
        Save research notes to file.
        
        Args:
            topic: Research topic
            data: Collected data
            
        Returns:
            Path to saved notes file
        """
        try:
            # Create research notes directory
            notes_dir = Path(settings.research_notes_dir)
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_research_{topic.replace(' ', '_')[:30]}_{timestamp}.txt"
            filepath = notes_dir / filename
            
            # Write notes
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== WEB RESEARCH NOTES ===\n")
                f.write(f"Topic: {topic}\n")
                f.write(f"Date: {datetime.now().isoformat()}\n")
                f.write(f"Sources: {len(data)}\n\n")
                
                for item in data:
                    f.write(f"--- Source [{item['citation_num']}] ---\n")
                    f.write(f"Title: {item['title']}\n")
                    f.write(f"URL: {item['url']}\n")
                    f.write(f"Retrieved: {item['retrieved_at']}\n\n")
                    f.write(f"{item['content']}\n\n")
                    f.write("-" * 80 + "\n\n")
            
            logger.info(f"Research notes saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving research notes: {e}")
            return None
    
    def search_specific_content(
        self,
        url: str,
        search_terms: List[str]
    ) -> Dict[str, Any]:
        """
        Search for specific content within a scraped page.
        
        Args:
            url: URL to scrape
            search_terms: Terms to search for
            
        Returns:
            Dictionary with matching content
        """
        result = self.web_scraper.scrape_url(url)
        
        if result["status"] != "success":
            return {"status": "error", "error": result.get("error")}
        
        content = result["content"]
        matches = []
        
        for term in search_terms:
            if term.lower() in content.lower():
                # Find context around the term (100 chars before and after)
                pos = content.lower().find(term.lower())
                start = max(0, pos - 100)
                end = min(len(content), pos + len(term) + 100)
                context = content[start:end]
                matches.append({
                    "term": term,
                    "context": context
                })
        
        return {
            "url": url,
            "matches": matches,
            "match_count": len(matches)
        }

