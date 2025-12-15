# Fix: ContributionTracker Serialization Error

## Problem

**Error**: `Type is not msgpack serializable: ContributionTracker`

**Root Cause**: 
- LangGraph uses msgpack to serialize state for checkpointing
- `ContributionTracker` was stored directly in `AgentState`
- `ContributionTracker` is not serializable (contains file handles, complex objects)

## Solution

**Approach**: Store trackers outside of state in a registry, retrieve by session_id

### Changes Made:

1. **Created Tracker Registry** (`utils/contribution_tracker.py`)
   - Module-level dictionary: `_tracker_registry: Dict[str, ContributionTracker]`
   - `get_contribution_tracker(session_id)` - Retrieve tracker
   - `remove_contribution_tracker(session_id)` - Cleanup

2. **Removed from State** (`orchestration/state.py`)
   - Removed `contribution_tracker: Optional[Any]` from `AgentState`
   - Removed from `create_initial_state()`

3. **Updated Graph Builder** (`orchestration/graph_builder.py`)
   - Tracker created and stored in registry (not state)
   - Nodes retrieve tracker from registry using `session_id`
   - Pass tracker to agents via context (not state)

## How It Works Now

### Flow:

```
1. Workflow.execute() creates tracker
   ↓
2. Tracker stored in registry: _tracker_registry[session_id] = tracker
   ↓
3. Initial state created WITHOUT tracker
   ↓
4. Each node retrieves tracker: tracker = get_contribution_tracker(session_id)
   ↓
5. Tracker passed to agents via context (not state)
   ↓
6. Agents use tracker for logging
   ↓
7. Workflow completes, tracker saved to disk
```

### Code Pattern:

**In graph_builder.py nodes:**
```python
def _lead_researcher_node(self, state: AgentState) -> Dict[str, Any]:
    # Get tracker from registry (not from state)
    session_id = state.get("session_id")
    tracker = get_contribution_tracker(session_id) if session_id else None
    
    result = self.lead_researcher.execute(
        user_request=state["user_request"],
        context={
            "contribution_tracker": tracker,  # Pass via context
            "session_id": session_id
        }
    )
```

**In agents:**
```python
def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
    tracker = context.get("contribution_tracker")  # Get from context
    if tracker:
        tracker.log_agent_start(...)
```

## Benefits

1. ✅ **State is Serializable**: No complex objects in state
2. ✅ **LangGraph Works**: Checkpointing and state persistence work correctly
3. ✅ **Agents Still Get Tracker**: Via context, not state
4. ✅ **Clean Separation**: Runtime objects separate from persistent state
5. ✅ **Easy Cleanup**: Can remove trackers after session completes

## Testing

### Verify Fix:

```python
# Should work without serialization error
from orchestration.graph_builder import create_workflow

workflow = create_workflow()
result = workflow.execute(
    user_request="Test topic",
    report_requirements={"topic": "Test"},
    session_id="test-123"
)

# Should complete successfully
assert result["status"] == "completed"
```

### Verify Tracker Still Works:

```python
from utils.contribution_tracker import get_contribution_tracker

tracker = get_contribution_tracker("test-123")
assert tracker is not None
assert tracker.session_id == "test-123"
```

## Files Changed

1. ✅ `utils/contribution_tracker.py` - Added registry functions
2. ✅ `orchestration/state.py` - Removed tracker from state
3. ✅ `orchestration/graph_builder.py` - Updated to use registry

## Status

✅ **Fixed**: Tracker no longer stored in state
✅ **Working**: Agents still access tracker via context
✅ **Serializable**: State can be checkpointed by LangGraph
✅ **No Breaking Changes**: Agent interfaces unchanged

---

**The serialization error is now fixed!** 🎉

