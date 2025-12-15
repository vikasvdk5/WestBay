# Agent Contribution Tracking System

## Overview

The contribution tracking system logs detailed information about what each agent and tool contributes during report generation. After every agent's run, a contribution log is saved to `./data/agent-contribution/<session_id>/`.

## Architecture

### Components

1. **ContributionTracker** (`utils/contribution_tracker.py`)
   - Tracks agent and tool contributions
   - Saves individual agent logs
   - Generates comprehensive summaries

2. **Integration Points**
   - Initialized in `graph_builder.py` during workflow execution
   - Passed through AgentState to all agents
   - Each agent logs its contribution
   - Summary generated at end of workflow

### Output Structure

```
data/
└── agent-contribution/
    └── <session_id>/
        ├── lead_researcher_20251214_120000.json
        ├── data_collector_20251214_120030.json
        ├── api_researcher_20251214_120045.json
        ├── analyst_20251214_120100.json
        ├── writer_20251214_120130.json
        ├── cost_calculator_20251214_115959.json
        ├── SUMMARY.json
        └── SUMMARY.md
```

## Agent Types and Their Contributions

### 1. Lead Researcher Agent
- **Type**: `lead_researcher`
- **Contributions**:
  - Research plan breakdown
  - Subtopics identified
  - Task delegation decisions
- **Tools Used**: Gemini LLM
- **Metrics**:
  - Number of subtopics
  - Number of researchers spawned
  - Planning time

### 2. Data Collector Agent
- **Type**: `data_collector`
- **Contributions**:
  - Web pages scraped
  - Raw data extracted
  - Source URLs collected
- **Tools Used**: Web Scraper, Gemini LLM
- **Metrics**:
  - Pages scraped
  - Data points collected
  - Scraping success rate

### 3. API Researcher Agent
- **Type**: `api_researcher`
- **Contributions**:
  - APIs called
  - External data retrieved
  - API response processing
- **Tools Used**: API Caller, Gemini LLM
- **Metrics**:
  - APIs called
  - Data points retrieved
  - API success rate

### 4. Analyst Agent
- **Type**: `analyst`
- **Contributions**:
  - Data analysis performed
  - Insights generated
  - Visualizations created
- **Tools Used**: Gemini LLM, Visualization Tool
- **Metrics**:
  - Insights generated
  - Charts created
  - Analysis depth

### 5. Writer Agent
- **Type**: `writer`
- **Contributions**:
  - Report sections written
  - Citations formatted
  - Final report generated
- **Tools Used**: Gemini LLM, PDF Generator
- **Metrics**:
  - Sections written
  - Word count
  - Citations included

### 6. Cost Calculator Agent
- **Type**: `cost_calculator`
- **Contributions**:
  - Token usage estimated
  - Cost calculated
  - Budget recommendations
- **Tools Used**: None (calculation only)
- **Metrics**:
  - Estimated tokens
  - Estimated cost
  - Actual vs estimated

## How to Integrate in Agents

### Step 1: Access the Tracker

Each agent receives the tracker through the state:

```python
def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # Get tracker from state
    tracker = context.get("contribution_tracker")
    if not tracker:
        logger.warning("Contribution tracker not available")
        # Continue without tracking
        return self._execute_without_tracking(context)
```

### Step 2: Log Agent Start

```python
# Log when agent starts
agent_context = tracker.log_agent_start(
    agent_name="data_collector",
    agent_type="data_collector",
    task="Collect web research data on Electric Vehicles"
)
```

### Step 3: Log Tool Usage

```python
# When using a tool
import time

start_time = time.time()
result = web_scraper.scrape(url)
execution_time = time.time() - start_time

tool_contrib = tracker.log_tool_usage(
    tool_name="web_scraper",
    tool_type="web_scraper",
    data_collected=f"Scraped {len(result)} pages",
    execution_time=execution_time,
    success=True,
    output_files=[output_file_path],
    metadata={"urls": urls, "pages": len(result)}
)
```

### Step 4: Log Agent End

```python
# Log when agent completes
tracker.log_agent_end(
    context=agent_context,
    status="completed",
    output_summary=f"Collected data from {pages_scraped} web pages",
    output_files=[output_file1, output_file2],
    tools_used=[tool_contrib],
    tokens_used=estimated_tokens,
    estimated_cost=estimated_cost,
    metrics={
        "pages_scraped": pages_scraped,
        "data_points": data_points,
        "success_rate": success_rate
    },
    actions_taken=[
        "Scraped 5 URLs",
        "Extracted 120 data points",
        "Saved to research_notes"
    ],
    errors=errors_list
)
```

## Example: Updating Data Collector Agent

Here's a complete example of integrating the tracker:

```python
class DataCollectorAgent:
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Get tracker
        tracker = context.get("contribution_tracker")
        
        # Log agent start
        agent_context = None
        if tracker:
            agent_context = tracker.log_agent_start(
                agent_name="data_collector",
                agent_type="data_collector",
                task=f"Collect web research data on {context.get('topic')}"
            )
        
        actions_taken = []
        tools_used = []
        output_files = []
        errors = []
        
        try:
            # Do the work
            urls = self._get_urls(context)
            actions_taken.append(f"Identified {len(urls)} URLs to scrape")
            
            # Use web scraper tool
            import time
            start_time = time.time()
            scrape_results = self.web_scraper.scrape_all(urls)
            execution_time = time.time() - start_time
            
            # Log tool usage
            if tracker:
                tool_contrib = tracker.log_tool_usage(
                    tool_name="web_scraper",
                    tool_type="web_scraper",
                    data_collected=f"Scraped {len(scrape_results)} pages successfully",
                    execution_time=execution_time,
                    success=True,
                    output_files=[str(output_path)],
                    metadata={
                        "urls_attempted": len(urls),
                        "urls_succeeded": len(scrape_results),
                        "total_data_size": sum(len(r) for r in scrape_results)
                    }
                )
                tools_used.append(tool_contrib)
            
            actions_taken.append(f"Scraped {len(scrape_results)} pages")
            
            # Save results
            output_path = self._save_results(scrape_results, context)
            output_files.append(str(output_path))
            actions_taken.append(f"Saved results to {output_path}")
            
            # Estimate tokens used
            tokens_used = self._estimate_tokens(scrape_results)
            estimated_cost = tokens_used * 0.00001  # Example rate
            
            # Log agent completion
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="completed",
                    output_summary=f"Successfully collected data from {len(scrape_results)} web pages",
                    output_files=output_files,
                    tools_used=tools_used,
                    tokens_used=tokens_used,
                    estimated_cost=estimated_cost,
                    metrics={
                        "urls_attempted": len(urls),
                        "pages_scraped": len(scrape_results),
                        "data_points": sum(len(r) for r in scrape_results),
                        "success_rate": len(scrape_results) / len(urls) if urls else 0
                    },
                    actions_taken=actions_taken,
                    errors=errors
                )
            
            return {
                "status": "success",
                "data": scrape_results,
                "output_path": str(output_path)
            }
            
        except Exception as e:
            errors.append(str(e))
            
            # Log agent failure
            if tracker and agent_context:
                tracker.log_agent_end(
                    context=agent_context,
                    status="failed",
                    output_summary=f"Failed to collect data: {str(e)}",
                    output_files=output_files,
                    tools_used=tools_used,
                    tokens_used=0,
                    estimated_cost=0.0,
                    metrics={"pages_scraped": 0},
                    actions_taken=actions_taken,
                    errors=errors
                )
            
            raise
```

## Summary Report Format

### JSON Summary (`SUMMARY.json`)

```json
{
  "session_id": "abc-123",
  "topic": "Electric Vehicle Market Analysis",
  "start_time": "2025-12-14T12:00:00",
  "end_time": "2025-12-14T12:05:30",
  "total_duration": 330.0,
  "agents": {
    "total_agents": 5,
    "successful": 5,
    "failed": 0,
    "contributions": [
      {
        "agent": "lead_researcher",
        "type": "lead_researcher",
        "duration": 15.2,
        "status": "completed",
        "output": "Created research plan with 3 subtopics",
        "files_generated": 1,
        "tools_used": 1,
        "tokens": 1500,
        "cost": 0.015
      }
    ]
  },
  "tools": {
    "total_tools": 4,
    "total_invocations": 12,
    "total_execution_time": 85.5,
    "contributions": [
      {
        "tool": "web_scraper",
        "type": "web_scraper",
        "invocations": 5,
        "execution_time": 45.2,
        "success": true,
        "data_collected": "Scraped 15 web pages",
        "files_generated": 5
      }
    ]
  },
  "totals": {
    "total_tokens": 25000,
    "total_cost": 0.25,
    "total_files_generated": 12,
    "total_errors": 0
  }
}
```

### Markdown Summary (`SUMMARY.md`)

See example output in the generated files.

## Benefits

1. **Transparency**: See exactly what each agent contributed
2. **Debugging**: Identify which agent failed or underperformed
3. **Optimization**: Understand which agents take longest
4. **Cost Tracking**: Monitor token usage and costs per agent
5. **Audit Trail**: Complete record of research process
6. **Tool Analytics**: See which tools are most used/effective

## Next Steps

1. ✅ System created and integrated into workflow
2. ⏳ Update each agent to log contributions (see example above)
3. ⏳ Add tool tracking to web scraper
4. ⏳ Add tool tracking to API caller
5. ⏳ Add tool tracking to visualization generator
6. ⏳ Add tool tracking to PDF generator

## Testing

To test the system:

```bash
# Run a report generation
curl -X POST http://localhost:8000/api/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "requirements": {
      "topic": "Test Topic",
      "page_count": 10,
      "source_count": 5
    }
  }'

# Check the contribution logs
ls -la data/agent-contribution/test-123/

# View the summary
cat data/agent-contribution/test-123/SUMMARY.md
```

## Implementation Status

- ✅ ContributionTracker class created
- ✅ Integrated into workflow
- ✅ State updated to include tracker
- ✅ Summary generation implemented
- ⏳ Individual agents need to be updated (see example above)

The system is ready to use! Each agent just needs to add the logging calls as shown in the examples.

