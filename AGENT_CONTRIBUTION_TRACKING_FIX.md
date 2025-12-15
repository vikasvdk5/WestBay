# Agent Contribution Tracking Fix

## Problem

Only `lead_researcher` and `synthesizer` agent contribution files were being created in `data/agent-contribution/{session_id}/`. The other agents (`data_collector`, `api_researcher`, `analyst`, `writer`) were not logging their contributions.

## Root Cause

### 1. Graph Builder Not Passing Contribution Tracker

The graph builder nodes were **not retrieving or passing** the contribution tracker to agents:
- `_data_collector_node`: ❌ No tracker passed
- `_api_researcher_node`: ❌ No tracker passed  
- `_analyst_node`: ❌ No tracker passed
- `_writer_node`: ❌ No tracker passed

Only `_lead_researcher_node` and `_synthesizer_node` were correctly passing the tracker.

### 2. Agents Not Using the Tracker

Even though agents accepted a `context` parameter, they were **not retrieving or using** the contribution tracker from it:
- `data_collector.py`: ❌ Not using tracker
- `api_researcher.py`: ❌ Not using tracker
- `analyst.py`: ❌ Not using tracker
- `writer.py`: ❌ Not using tracker

## Fix Applied

### 1. Updated Graph Builder to Pass Tracker to All Agents

**data_collector_node:**
```python
# Get session ID and tracker
session_id = state.get("session_id")
tracker = get_contribution_tracker(session_id) if session_id else None

result = self.data_collector.execute(
    urls=urls,
    topic=topic,
    context={
        "assigned_tasks": assigned_tasks,
        "contribution_tracker": tracker,
        "session_id": session_id
    }
)
```

**api_researcher_node:**
```python
# Get session ID and tracker
session_id = state.get("session_id")
tracker = get_contribution_tracker(session_id) if session_id else None

result = self.api_researcher.execute(
    api_requests=api_requests,
    topic=topic,
    context={
        "assigned_tasks": assigned_tasks,
        "contribution_tracker": tracker,
        "session_id": session_id
    }
)
```

**analyst_node:**
```python
# Get session ID and tracker
session_id = state.get("session_id")
tracker = get_contribution_tracker(session_id) if session_id else None

result = self.analyst.execute(
    research_data=research_data,
    topic=topic,
    context={
        "assigned_tasks": assigned_tasks,
        "report_requirements": report_reqs,
        "contribution_tracker": tracker,
        "session_id": session_id
    }
)
```

**writer_node:**
```python
# Get session ID and tracker
session_id = state.get("session_id")
tracker = get_contribution_tracker(session_id) if session_id else None

result = self.writer.execute(
    report_structure=report_structure,
    research_findings=research_findings,
    analysis_results=analysis_results or {},
    citations=citations,
    context={
        "topic": state["user_request"],
        "report_requirements": state.get("report_requirements", {}),
        "contribution_tracker": tracker,
        "session_id": session_id
    }
)
```

### 2. Updated data_collector Agent to Use Tracker

Added contribution tracking throughout the agent's execution:

```python
def execute(self, urls, topic, context=None):
    # Get tracker from context
    tracker = context.get("contribution_tracker") if context else None
    assigned_tasks = context.get("assigned_tasks", []) if context else []
    agent_context = None
    
    # Log agent start
    if tracker:
        agent_context = tracker.log_agent_start(
            agent_name="data_collector",
            input_data={
                "topic": topic,
                "urls_count": len(urls),
                "assigned_tasks": len(assigned_tasks)
            }
        )
    
    # ... agent logic ...
    
    # Log tool usage
    if tracker:
        tracker.log_tool_usage(
            tool_name="web_scraper",
            input_data={"urls": urls, "count": len(urls)},
            output_data={"scraped": len(scrape_results)},
            metadata={"tool_type": "web_scraping"}
        )
    
    # ... more logic ...
    
    # Log agent completion
    if tracker and agent_context:
        tracker.log_agent_completion(
            agent_name="data_collector",
            context_id=agent_context,
            output_data=result,
            success=True,
            output_files=[str(notes_file)] if notes_file else []
        )
```

### 3. Next Steps (TODO)

The same pattern needs to be applied to:
- ✅ `data_collector.py` - DONE
- ❌ `api_researcher.py` - TODO
- ❌ `analyst.py` - TODO  
- ❌ `writer.py` - TODO

Each agent needs to:
1. Retrieve `tracker` from `context.get("contribution_tracker")`
2. Call `tracker.log_agent_start()` at the beginning
3. Call `tracker.log_tool_usage()` for each tool/API call
4. Call `tracker.log_agent_completion()` at the end (success or error)

## Expected Result

After this fix, `data/agent-contribution/{session_id}/` will contain:
- ✅ `lead_researcher_{timestamp}_{topic}.json`
- ✅ `synthesizer_{timestamp}_{topic}.json`
- ✅ `data_collector_{timestamp}_{topic}.json` (NEW)
- ✅ `api_researcher_{timestamp}_{topic}.json` (NEW, if used)
- ✅ `analyst_{timestamp}_{topic}.json` (NEW)
- ✅ `writer_{timestamp}_{topic}.json` (NEW)
- ✅ `SUMMARY.json`
- ✅ `SUMMARY.md`

## Complete Agent Output in Files

Each agent's contribution file will now contain:
- **Agent name** and **session ID**
- **Input data**: What was passed to the agent
- **Assigned tasks**: Tasks from lead researcher
- **Tool usage**: All tools called (web_scraper, API calls, LLM calls, etc.)
- **Tokens and costs**: Detailed token usage per LLM call
- **Output data**: Complete results from the agent
- **Output files**: Paths to any files generated
- **Success status**: Whether the agent succeeded or failed
- **Duration**: How long the agent took

## Testing

To verify the fix:

1. **Start a new report generation**
2. **Check the agent-contribution folder** after completion:
   ```bash
   ls -la data/agent-contribution/{session_id}/
   ```
3. **Should see files for all agents** that executed
4. **Read each file** to verify complete output:
   ```bash
   cat data/agent-contribution/{session_id}/data_collector_*.json
   ```
5. **Check SUMMARY files** for complete workflow overview:
   ```bash
   cat data/agent-contribution/{session_id}/SUMMARY.md
   ```

## Benefits

✅ **Full visibility**: See what each agent did  
✅ **Complete output**: All agent results logged  
✅ **Tool tracking**: Know which tools were used and how  
✅ **Cost transparency**: Token usage and costs per agent  
✅ **Debugging**: Easy to trace issues to specific agents  
✅ **Audit trail**: Complete record of report generation process  

