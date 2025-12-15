# Intelligent Agent Discovery - LLM-Powered URL & API Finding

## Overview

Both Data Collector and API Researcher agents have been upgraded to be fully autonomous and intelligent. They no longer require predefined URLs or API endpoints - instead, they use LLM reasoning to discover the best sources for their assigned research topics.

## Problem Solved

**Before:**
- ❌ Agents failed with zero output when no URLs/APIs were provided
- ❌ Required manual specification of data sources
- ❌ Limited to predefined lists of endpoints
- ❌ Inflexible for diverse research topics

**After:**
- ✅ Agents autonomously discover relevant sources using LLM
- ✅ Adapt to any research topic dynamically
- ✅ Find authoritative, high-quality data sources
- ✅ Never return empty results - always attempt intelligent discovery

## 1. Data Collector Agent - Intelligent URL Discovery

### How It Works

When the Data Collector is assigned a research topic but NO URLs are provided (or only placeholder URLs), it:

1. **Uses LLM to Analyze the Topic**:
   - Understands what type of information is needed
   - Identifies what kinds of sources would contain this data
   - Determines the most authoritative places to look

2. **Generates 3-5 Specific URLs**:
   - Asks LLM: "Where would authoritative information about this topic be published?"
   - Gets specific, actionable URLs (not just domain names)
   - Validates URLs are publicly accessible

3. **Falls Back Intelligently**:
   - If LLM can't find URLs, uses topic-based heuristics
   - Checks for company names → investor relations sites
   - Keywords → relevant news/data sources
   - Generic fallbacks as last resort

### Example Flow

**Topic**: "Gather data on Apple's revenue growth in China"

**LLM Reasoning**:
```
This requires financial data → Official sources + Market analysis
Best sources:
1. Apple investor relations (official financial data)
2. SEC filings (regulatory filings)
3. Bloomberg/Reuters (market analysis)
4. Statista (statistical data on China market)
```

**URLs Generated**:
```python
[
    "https://investor.apple.com/investor-relations/",
    "https://www.sec.gov/cgi-bin/browse-edgar?company=apple",
    "https://www.bloomberg.com/quote/AAPL:US",
    "https://www.statista.com/statistics/..."
]
```

### Code Implementation

```python
def _find_relevant_urls_with_llm(self, topic, assigned_tasks):
    """Use LLM to identify 3-5 relevant URLs for the research topic."""
    
    # Build prompt with topic and tasks context
    prompt = f"""Given this research topic and specific data collection tasks, 
    identify 3-5 specific, authoritative URLs that would contain relevant information.
    
    Research Topic: {topic}
    Tasks: {tasks_context}
    
    Instructions:
    1. Think about where authoritative information would be published
    2. Consider: official sites, government data, reputable news, research
    3. Provide SPECIFIC URLs (not just domains)
    4. Ensure publicly accessible
    5. Prioritize data-rich sources
    
    Return JSON array of URLs: ["url1", "url2", ...]
    """
    
    # Call LLM and parse response
    response = self.executor.call_llm(prompt)
    urls = parse_urls_from_response(response)
    
    return urls if urls else self._get_fallback_urls(topic)
```

### Fallback Strategy

If LLM fails, use intelligent fallbacks:

```python
def _get_fallback_urls(self, topic):
    """Provide fallback URLs based on topic keywords."""
    
    # Check for company names
    if 'apple' in topic.lower():
        urls.append("https://investor.apple.com")
    
    # Check for topic type
    if 'market' in topic.lower():
        urls.extend([
            "https://www.statista.com",
            "https://www.ibisworld.com"
        ])
    
    if 'financial' in topic.lower():
        urls.extend([
            "https://finance.yahoo.com",
            "https://www.sec.gov"
        ])
    
    # Generic fallbacks
    return urls or ["https://www.reuters.com", "https://www.bloomberg.com"]
```

## 2. API Researcher Agent - Intelligent API Discovery

### How It Works

When the API Researcher is assigned a research topic but NO API endpoints are specified, it:

1. **Uses LLM to Identify Data Needs**:
   - Analyzes what KIND of data is required
   - Maps data needs to API categories (financial, economic, news, etc.)

2. **Discovers FREE/PUBLIC APIs**:
   - LLM suggests 2-3 relevant APIs with free tiers
   - Provides specific endpoint URLs
   - Includes parameters and authentication details

3. **Returns OpenAPI-style Specifications**:
   - API name and base URL
   - Specific endpoint to call
   - Required parameters
   - Authentication type
   - Description of data provided

### Example Flow

**Topic**: "Get stock price data for Apple and competitors"

**LLM Reasoning**:
```
Need: Financial stock data
Free APIs available:
1. Alpha Vantage - Stock prices, daily data (free tier, API key)
2. Yahoo Finance API - Real-time quotes (free, no auth)
3. IEX Cloud - Company data (free tier, token)
```

**API Specifications Generated**:
```json
[
  {
    "api_name": "Alpha Vantage",
    "url": "https://www.alphavantage.co/query",
    "method": "GET",
    "params": {
      "function": "TIME_SERIES_DAILY",
      "symbol": "AAPL",
      "apikey": "demo"
    },
    "auth_type": "api_key",
    "description": "Daily stock prices for Apple"
  },
  {
    "api_name": "Yahoo Finance",
    "url": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
    "method": "GET",
    "params": {},
    "auth_type": "none",
    "description": "Real-time stock quotes"
  }
]
```

### Code Implementation

```python
def _discover_apis_with_llm(self, topic, assigned_tasks):
    """Use LLM to discover relevant free/public APIs."""
    
    # Build prompt
    prompt = f"""Given this research topic, identify 2-3 FREE/PUBLIC APIs 
    that would provide relevant data.
    
    Research Topic: {topic}
    Data Needs: {tasks_context}
    
    Common Free APIs:
    - Financial: Alpha Vantage, IEX Cloud, Yahoo Finance
    - Economic: World Bank, FRED, IMF
    - News: NewsAPI, GNews
    - Company: OpenCorporates
    
    Return JSON array with API specs:
    [{{
      "api_name": "API Name",
      "url": "https://api.example.com/endpoint",
      "method": "GET",
      "params": {{"param": "value"}},
      "auth_type": "api_key" or "none"
    }}]
    
    If NO suitable free APIs exist, return: []
    """
    
    # Call LLM and parse
    response = self.executor.call_llm(prompt)
    apis = parse_api_specs_from_response(response)
    
    return apis  # Empty list if no APIs found
```

### Graceful Handling of No APIs

If LLM determines no suitable free APIs exist:

```python
if not api_requests:
    logger.info("No relevant public APIs found for this topic")
    return {
        "api_research_data": {
            "status": "no_apis_found",
            "message": "No suitable public APIs identified for this research topic"
        },
        "status": "api_research_complete"
    }
```

The agent completes successfully but notes that API data is unavailable, allowing the workflow to continue with data from other sources.

## 3. Updated Prompts

### Data Collector Prompt (`prompts/researcher.txt`)

Key additions:
- **Intelligent URL Discovery** section with step-by-step instructions
- **No Predefined URLs Required** - emphasis on autonomous operation
- **Topic-Specific Source Selection** - guidelines for different topic types
- **URL Validation** - ensuring accessible, authoritative sources
- **Example Scenarios** - concrete examples of URL discovery for various topics

### API Researcher Prompt (`prompts/api_researcher.txt`)

Key additions:
- **Intelligent API Discovery** section with discovery strategy
- **API Discovery Strategy** - mapping data needs to API categories
- **Popular Free APIs by Category** - comprehensive list of free/public APIs
- **OpenAPI Spec Usage** - how to read and use API specifications
- **Example Scenarios** - concrete examples of API discovery for various topics
- **API Authentication** - handling different auth types
- **Graceful No-API Handling** - what to do when no APIs are available

## Benefits

### For Data Collector:
✅ **Never fails due to missing URLs**  
✅ **Finds authoritative sources automatically**  
✅ **Adapts to any research topic**  
✅ **Prioritizes quality data sources**  
✅ **Falls back intelligently if LLM fails**  

### For API Researcher:
✅ **Discovers free/public APIs dynamically**  
✅ **Maps data needs to available APIs**  
✅ **Handles topics with no API coverage gracefully**  
✅ **Provides structured API specifications**  
✅ **Knows when to skip (no APIs) vs when to call**  

### For the Workflow:
✅ **More autonomous and intelligent**  
✅ **Handles diverse research topics**  
✅ **Reduces manual configuration**  
✅ **Better data coverage**  
✅ **Graceful degradation when sources unavailable**  

## Testing

### Test Data Collector:

1. **With Topic Only** (no URLs):
   ```python
   result = data_collector.execute(
       urls=[],  # Empty list
       topic="Tesla battery technology advancements",
       context={...}
   )
   # Should automatically find 3-5 relevant URLs
   ```

2. **With Placeholder URLs**:
   ```python
   result = data_collector.execute(
       urls=["https://example.com/market-data"],  # Default placeholder
       topic="EV market growth projections",
       context={...}
   )
   # Should detect placeholder and use LLM to find real URLs
   ```

### Test API Researcher:

1. **With Topic Only** (no APIs):
   ```python
   result = api_researcher.execute(
       api_requests=[],  # Empty list
       topic="Apple stock performance",
       context={...}
   )
   # Should discover Alpha Vantage, Yahoo Finance, etc.
   ```

2. **Topic with No Free APIs**:
   ```python
   result = api_researcher.execute(
       api_requests=[],
       topic="Detailed market research report analysis",
       context={...}
   )
   # Should return status: "no_apis_found" gracefully
   ```

## Key Implementation Details

### LLM Temperature:
- Set to `0.3` for focused, deterministic results
- Lower temperature ensures consistent, reliable outputs
- Reduces hallucination of fake URLs/APIs

### Response Parsing:
- Tries JSON parsing first (structured output)
- Falls back to regex URL extraction
- Validates all extracted URLs/APIs
- Filters out invalid or malformed responses

### Error Handling:
- If LLM fails → fallback strategies
- If parsing fails → extract what's possible
- If all fails → return topic-based defaults
- Never throws exceptions - always provides something

### Logging:
- Logs when using LLM discovery
- Logs number of URLs/APIs found
- Logs fallback activations
- Provides transparency in agent decision-making

## Summary

Both agents are now **truly intelligent** - they can research ANY topic without manual URL/API configuration. They use LLM reasoning to discover the best data sources, fall back intelligently when needed, and always provide useful results.

This makes the entire research workflow more autonomous, flexible, and robust! 🎉

