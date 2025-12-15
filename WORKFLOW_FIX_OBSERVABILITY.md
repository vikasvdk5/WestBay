# Workflow Fix and Observability Guide

## Issue Fixed

The workflow was getting stuck in a "Generating Report..." loop because:
1. **Parallel execution routing problem**: When multiple agents executed in parallel and one routed to END (waiting), the entire workflow stopped before other agents could complete.
2. **State update conflicts**: Multiple agents updating the same state fields concurrently caused LangGraph errors.
3. **Completion checking logic**: The completion checker wasn't properly waiting for all agents.

## Changes Made

### 1. Fixed Workflow Execution Pattern

**Changed from parallel to sequential execution:**
- **Before**: Synthesizer → (data_collector, api_researcher, analyst in parallel) → check → writer
- **After**: Synthesizer → data_collector → api_researcher → analyst → check_completion → writer

**Why Sequential?**
- LangGraph's `invoke()` method doesn't handle true parallel execution well when paths route to END
- Sequential execution ensures all agents complete before checking
- State updates are properly merged using reducers
- More predictable and debuggable

**Conditional Routing Added:**
- Agents are skipped if not needed (e.g., API researcher skipped if no APIs)
- Routing logic determines next agent based on `required_agents` list

### 2. Enhanced State Management

**Added Reducer Functions:**
- `take_last_status`: Merges concurrent status updates
- `take_last_agent`: Merges current_agent updates
- `merge_completion_status`: Merges agent completion status dictionaries

**State Fields Updated:**
- `status`: `Annotated[str, take_last_status]`
- `current_agent`: `Annotated[Optional[str], take_last_agent]`
- `agent_completion_status`: `Annotated[Optional[Dict[str, bool]], merge_completion_status]`

### 3. Improved Logging and Error Handling

**Enhanced Logging:**
- Added detailed logging at each workflow step
- Logs completion status checks with agent-by-agent breakdown
- Logs workflow start/end with state information

**Better Error Handling:**
- Background tasks now log full tracebacks
- Errors are stored in state with detailed information
- Debug endpoint added for troubleshooting

### 4. Added Debug Endpoint

**New Endpoint**: `GET /api/debug/workflow-state/{session_id}`

Returns detailed workflow state including:
- Current status and agent
- Required agents and completion status
- Agent tasks distribution
- Data availability flags
- Errors and timestamps

**Usage:**
```bash
curl http://localhost:8000/api/debug/workflow-state/{session_id}
```

## LangSmith Observability

### Setup

LangSmith is already configured in the codebase. To enable it:

1. **Get LangSmith API Key:**
   - Sign up at https://smith.langchain.com
   - Go to Settings → API Keys
   - Create a new API key

2. **Configure Environment Variable:**
   ```bash
   # Add to .env file
   LANGSMITH_API_KEY=your_api_key_here
   LANGSMITH_PROJECT=market-research-agent
   LANGCHAIN_TRACING_V2=true
   ```

3. **Restart Backend:**
   ```bash
   python main.py
   ```

### Accessing LangSmith UI

1. **Go to LangSmith Dashboard:**
   - Visit: https://smith.langchain.com
   - Login with your account

2. **View Traces:**
   - Select your project: `market-research-agent`
   - View all runs and traces
   - Filter by session_id, agent name, or timestamp

3. **What You Can See:**
   - **Agent Calls**: Each agent execution with inputs/outputs
   - **LLM Calls**: Gemini API calls with prompts and responses
   - **Tool Calls**: Web scraping, API calls, visualization generation
   - **State Transitions**: How state changes through the workflow
   - **Timing**: Duration of each step
   - **Errors**: Any failures with stack traces
   - **Token Usage**: Token consumption per call

4. **Filtering and Search:**
   - Filter by session_id to see all steps for a specific report
   - Search by agent name to see all executions of a specific agent
   - Filter by errors to find problematic runs

### LangSmith Features

**Real-time Monitoring:**
- See workflow progress in real-time
- Monitor agent execution times
- Track token usage and costs

**Debugging:**
- View exact inputs/outputs for each agent
- See state at each step
- Identify bottlenecks and failures

**Analytics:**
- Token usage trends
- Cost analysis
- Performance metrics
- Success/failure rates

## Debugging Stuck Workflows

### 1. Check Debug Endpoint

```bash
curl http://localhost:8000/api/debug/workflow-state/{session_id}
```

Look for:
- `agent_completion_status`: Are all required agents marked as complete?
- `required_agents`: Which agents should have executed?
- `errors`: Any errors in the workflow?
- `has_report`: Is the report generated?

### 2. Check Logs

Look for:
- `✅ ALL REQUIRED AGENTS COMPLETED` - Writer should start
- `✍️ NODE: Writer` - Writer is executing
- `✅ Writer completed` - Report generation finished

### 3. Check LangSmith

- Filter by session_id
- See which agents executed
- Check for errors in any step
- Verify state transitions

### 4. Check Agent Contribution Files

```bash
ls -la data/agent-contribution/{session_id}/
```

Should see files for:
- lead_researcher
- synthesizer
- data_collector
- api_researcher (if needed)
- analyst (if needed)
- writer

## Workflow Execution Flow (Fixed)

```
START
  ↓
cost_calculator
  ↓
lead_researcher (creates strategy, distributes tasks)
  ↓
synthesizer (creates report structure)
  ↓
data_collector (marks complete)
  ↓
api_researcher (if needed, marks complete)
  ↓
analyst (if needed, marks complete)
  ↓
check_completion (verifies all agents completed)
  ↓
writer (generates final report)
  ↓
END
```

## Verification Steps

After the fix, verify:

1. **All agents execute**: Check logs for each agent's completion message
2. **Completion status updates**: Check `agent_completion_status` in debug endpoint
3. **Writer executes**: Look for "Writer (Report Generation)" log
4. **Report generated**: Check `report_path` and `pdf_path` in final state
5. **Contribution files created**: Check `data/agent-contribution/{session_id}/`

## Known Limitations

1. **Sequential Execution**: Agents now execute sequentially instead of truly in parallel. This is more reliable but slower. Future optimization could use LangGraph's streaming API for true parallelism.

2. **LangSmith Required**: For full observability, LangSmith API key must be configured. Without it, basic logging still works but advanced tracing is unavailable.

3. **State Persistence**: State is persisted to disk, but if the server crashes mid-execution, the workflow will restart from the beginning (not resume).

## Next Steps for True Parallel Execution

To implement true parallel execution in the future:

1. Use LangGraph's `stream()` method instead of `invoke()`
2. Implement a proper join pattern for parallel branches
3. Use LangGraph's built-in parallel execution support
4. Consider using async/await for agent execution

## Summary

The workflow is now fixed to execute sequentially, ensuring all agents complete before the writer starts. This resolves the stuck workflow issue. LangSmith provides comprehensive observability when configured, and the new debug endpoint helps troubleshoot any remaining issues.

