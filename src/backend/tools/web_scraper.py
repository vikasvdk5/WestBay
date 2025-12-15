"""
Web scraping tool for extracting content from predefined URLs.
Handles errors gracefully and tracks sources for citations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse
import time

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class WebScraperTool:
    """
    Tool for scraping web content from predefined URLs.
    Extracts text content and tracks sources for citations.
    """
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize web scraper tool.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        
        logger.info("Web Scraper Tool initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def scrape_url(
        self,
        url: str,
        extract_text_only: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            extract_text_only: If True, extract only text content
            
        Returns:
            Dictionary with scraped content and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text().strip() if title else urlparse(url).netloc
            
            # Extract main content
            content = self._extract_content(soup, extract_text_only)
            
            # Calculate scraping time
            scrape_time = time.time() - start_time
            
            result = {
                "url": url,
                "title": title_text,
                "content": content,
                "retrieved_at": datetime.now().isoformat(),
                "scrape_time": round(scrape_time, 2),
                "status": "success",
                "content_length": len(content)
            }
            
            logger.info(f"Successfully scraped {url} ({len(content)} chars in {scrape_time:.2f}s)")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            return self._error_result(url, "Timeout")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            return self._error_result(url, f"HTTP Error: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return self._error_result(url, str(e))
    
    def scrape_multiple_urls(
        self,
        urls: List[str],
        delay_between_requests: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs with delay between requests.
        
        Args:
            urls: List of URLs to scrape
            delay_between_requests: Delay in seconds between requests
            
        Returns:
            List of scraping results
        """
        results = []
        
        logger.info(f"Scraping {len(urls)} URLs")
        
        for i, url in enumerate(urls):
            result = self.scrape_url(url)
            results.append(result)
            
            # Add delay between requests (except for last one)
            if i < len(urls) - 1:
                time.sleep(delay_between_requests)
        
        successful = len([r for r in results if r["status"] == "success"])
        logger.info(f"Scraped {successful}/{len(urls)} URLs successfully")
        
        return results
    
    def _extract_content(
        self,
        soup: BeautifulSoup,
        text_only: bool = True
    ) -> str:
        """
        Extract content from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup parsed HTML
            text_only: If True, extract only text
            
        Returns:
            Extracted content as string
        """
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        if text_only:
            # Extract text from main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if main_content:
                # Get text with some structure
                paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
                content_parts = []
                
                for elem in paragraphs:
                    text = elem.get_text().strip()
                    if text:
                        # Add heading markers
                        if elem.name in ['h1', 'h2', 'h3']:
                            content_parts.append(f"\n## {text}\n")
                        else:
                            content_parts.append(text)
                
                return '\n'.join(content_parts)
            else:
                return soup.get_text(separator='\n', strip=True)
        else:
            return str(soup)
    
    def _error_result(self, url: str, error_message: str) -> Dict[str, Any]:
        """
        Create error result dictionary.
        
        Args:
            url: URL that failed
            error_message: Error message
            
        Returns:
            Error result dictionary
        """
        return {
            "url": url,
            "title": None,
            "content": None,
            "retrieved_at": datetime.now().isoformat(),
            "status": "error",
            "error": error_message
        }
    
    def extract_links(
        self,
        url: str,
        filter_domain: bool = True
    ) -> List[str]:
        """
        Extract links from a webpage.
        
        Args:
            url: URL to extract links from
            filter_domain: If True, only return links from same domain
            
        Returns:
            List of URLs
        """
        try:
            result = self.scrape_url(url, extract_text_only=False)
            
            if result["status"] != "success":
                return []
            
            soup = BeautifulSoup(result["content"], 'html.parser')
            links = []
            base_domain = urlparse(url).netloc
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = f"{urlparse(url).scheme}://{base_domain}{href}"
                elif not href.startswith('http'):
                    continue
                
                # Filter by domain if requested
                if filter_domain:
                    if urlparse(href).netloc == base_domain:
                        links.append(href)
                else:
                    links.append(href)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return []


# Predefined URLs for common market research sources
PREDEFINED_SOURCES = {
    "market_research": [
        "https://www.statista.com",
        "https://www.marketsandmarkets.com",
        "https://www.mordorintelligence.com",
    ],
    "industry_news": [
        "https://www.reuters.com",
        "https://www.bloomberg.com",
    ],
    "technology": [
        "https://techcrunch.com",
        "https://www.theverge.com",
    ]
}


def create_web_scraper(
    timeout: int = 30,
    max_retries: int = 3
) -> WebScraperTool:
    """
    Factory function to create a web scraper tool.
    
    Args:
        timeout: Request timeout
        max_retries: Maximum retries
        
    Returns:
        WebScraperTool instance
    """
    return WebScraperTool(timeout=timeout, max_retries=max_retries)

