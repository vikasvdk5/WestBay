# Writer NoneType Error Fix

## Error

```
agents.specialized.writer - ERROR - Error in writer agent: 'NoneType' object has no attribute 'get'
```

## Root Cause

The writer agent was calling `.get()` on parameters that could be None:
- `report_structure.get("sections", [])`
- `analysis_results.get("visualizations", [])`

While the graph_builder attempted to provide defaults, there were edge cases where None values could still be passed, especially:
1. When `state.get("analysis_results")` returns None explicitly
2. When agents fail to update the state properly
3. When the workflow is in an inconsistent state from a previous execution

## Fix Applied

### 1. Added Defensive Checks in Writer.execute()

```python
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
```

### 2. Added Safe `.get()` Calls

Updated all places where `.get()` is called on potentially None objects:

```python
# Before
for section_spec in report_structure.get("sections", []):

# After
section_specs = report_structure.get("sections", []) if report_structure else []
for section_spec in section_specs:
```

```python
# Before
visualizations = analysis_results.get('visualizations', [])

# After
visualizations = analysis_results.get('visualizations', []) if analysis_results else []
```

### 3. Enhanced Graph Builder Logging

Added detailed logging before calling the writer to help diagnose issues:

```python
logger.info(f"   Report structure: {report_structure is not None} (sections: {len(report_structure.get('sections', [])) if report_structure else 0})")
logger.info(f"   Research findings: web_data={research_findings.get('web_data') is not None}, api_data={research_findings.get('api_data') is not None}")
logger.info(f"   Analysis results: {analysis_results is not None}")
logger.info(f"   Citations count: {len(citations)}")
```

### 4. Ensured Non-None Defaults in Graph Builder

```python
result = self.writer.execute(
    report_structure=report_structure,
    research_findings=research_findings,
    analysis_results=analysis_results or {},  # Ensure not None
    citations=citations,
    context={"topic": state["user_request"]}
)
```

## Why This Happened

Looking at the session state from the previous issue:
- The workflow completed with errors
- Some agents failed to properly update their results
- The state had inconsistent data (analyst marked incomplete but had analysis results)
- When the writer tried to access this inconsistent state, it received None values

## Prevention

These defensive checks ensure that even if:
1. An agent fails to produce results
2. The state is inconsistent
3. A previous execution left bad data

The writer will still be able to generate a basic report instead of crashing with a NoneType error.

## Testing

To verify the fix:

1. **Start a fresh report generation**
2. **Check logs for writer execution**:
   ```
   ✍️  NODE: Writer (Report Generation)
   Report structure: True (sections: 5)
   Research findings: web_data=True, api_data=True
   Analysis results: True
   Citations count: 3
   Writer generating report...
   ✅ Writer completed
   ```
3. **If any values are None**, you'll see warning logs:
   ```
   report_structure is None, using default
   analysis_results is None, using empty dict
   ```

## Summary

- **Before**: Writer crashed with NoneType error if any input was None
- **After**: Writer handles None inputs gracefully with defaults and warnings
- **Benefit**: More robust error handling, better debugging information
- **Trade-off**: Report may be less complete if data is missing, but won't crash

The fix ensures the writer is more resilient to unexpected state conditions while providing clear logging about what data is missing.

