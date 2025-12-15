# Session Persistence Fix

## Problem

**Error**: `127.0.0.1:61469 - "GET /api/report-status/280bd232-92c3-46cf-951f-13e1a6a097d7 HTTP/1.1" 404 Not Found`

**Root Cause**: 
- The `StateManager` was storing sessions in memory only (`self.states: Dict[str, AgentState] = {}`)
- When the server restarted (due to dependency installation or code changes), all sessions were lost
- Frontend tried to check status of a session that no longer exists

## Solution

### 1. Added Persistent Storage to StateManager

Updated `src/backend/orchestration/state.py` to save session state to disk:

**Key Changes**:
- Added `persistence_file` parameter (defaults to `data/sessions/states.json`)
- Added `_load_states()` method - loads existing sessions on startup
- Added `_save_states()` method - saves sessions to JSON file
- Updated `create_state()`, `update_state()`, `delete_state()` to persist immediately after each operation
- Added `list_sessions()` - helper to list all active sessions
- Added `cleanup_old_sessions()` - cleanup sessions older than 7 days

**Before** (In-Memory Only):
```python
class StateManager:
    def __init__(self):
        self.states: Dict[str, AgentState] = {}
        # Lost on restart! ❌
```

**After** (Persistent):
```python
class StateManager:
    def __init__(self, persistence_file: Optional[Path] = None):
        self.states: Dict[str, AgentState] = {}
        self.persistence_file = Path(settings.data_dir) / "sessions" / "states.json"
        self._load_states()  # Load existing sessions ✅
    
    def _save_states(self):
        with open(self.persistence_file, 'w') as f:
            json.dump(self.states, f, indent=2, default=str)
```

### 2. Added Debugging Endpoint

Added `GET /api/sessions` endpoint to list all active sessions:

**Usage**:
```bash
curl http://localhost:8000/api/sessions
```

**Response**:
```json
{
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "280bd232-92c3-46cf-951f-13e1a6a097d7",
      "status": "generating",
      "topic": "Electric Vehicle Market Analysis",
      "started_at": "2025-12-14T18:45:00",
      "updated_at": "2025-12-14T18:46:30"
    },
    {
      "session_id": "abc123...",
      "status": "completed",
      "topic": "Hydrogen Market",
      "started_at": "2025-12-14T17:00:00",
      "updated_at": "2025-12-14T17:15:00"
    }
  ]
}
```

### 3. Enhanced Error Messages

Updated 404 error response to be more helpful:
```python
raise HTTPException(
    status_code=404, 
    detail=f"Session '{session_id}' not found. Available sessions: {len(available_sessions)}"
)
```

## Benefits

### ✅ Sessions Survive Server Restarts
- Sessions are now persisted to `data/sessions/states.json`
- When server restarts, all sessions are automatically restored
- No more lost progress!

### ✅ Better Debugging
- New `/api/sessions` endpoint to see all active sessions
- Enhanced error messages show how many sessions exist
- Can inspect session state directly from JSON file

### ✅ Automatic Cleanup
- `cleanup_old_sessions(days=7)` removes stale sessions
- Prevents disk space issues from accumulating old sessions
- Can be called manually or scheduled

## How It Works

### Session Lifecycle with Persistence

```
1. User submits requirements
   ↓
2. create_state() → Save to memory + disk
   ↓
3. Background task starts
   ↓
4. update_state() called by agents → Save to disk after each update
   ↓
5. Server restarts (code change, deployment, etc.)
   ↓
6. StateManager.__init__() → _load_states() from disk
   ↓
7. All sessions restored! ✅
   ↓
8. User polls /report-status/{session_id} → Works! ✅
```

### File Structure

```
data/
└── sessions/
    └── states.json         # All session states
```

**Example `states.json`**:
```json
{
  "280bd232-92c3-46cf-951f-13e1a6a097d7": {
    "session_id": "280bd232-92c3-46cf-951f-13e1a6a097d7",
    "status": "generating",
    "user_request": "Electric Vehicle Market Analysis",
    "report_requirements": {
      "topic": "Electric Vehicle Market Analysis",
      "page_count": 20,
      "source_count": 10
    },
    "current_agent": "analyst",
    "completed_tasks": ["data_collection", "api_research"],
    "started_at": "2025-12-14T18:45:00",
    "updated_at": "2025-12-14T18:46:30"
  }
}
```

## Testing

### 1. Verify Persistence Works

```bash
# Start server
cd src/backend
python main.py

# In another terminal: Create a session
curl -X POST http://localhost:8000/api/submit-requirements \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Test report",
    "requirements": {
      "topic": "Test Topic",
      "page_count": 10,
      "source_count": 5,
      "complexity": "simple"
    }
  }'

# Note the session_id from response
# Example: "280bd232-92c3-46cf-951f-13e1a6a097d7"

# Restart the server (Ctrl+C, then python main.py again)

# Check if session still exists
curl http://localhost:8000/api/sessions

# Should show your session! ✅
```

### 2. List All Sessions

```bash
curl http://localhost:8000/api/sessions | jq
```

### 3. Check Session Status (Should Work After Restart)

```bash
curl http://localhost:8000/api/report-status/280bd232-92c3-46cf-951f-13e1a6a097d7
```

## Migration Notes

### Existing Sessions
- **Old sessions (before this fix)**: Lost - they were in memory only
- **New sessions (after this fix)**: Persisted automatically
- **Current behavior**: Server loads from `data/sessions/states.json` on startup

### For Production
Consider upgrading to a proper database:
- SQLite for single-server deployments
- PostgreSQL/MongoDB for multi-server deployments
- Redis for fast in-memory + persistence

Current JSON-based persistence is suitable for:
- ✅ Development and testing
- ✅ Small deployments (< 1000 sessions)
- ✅ Single-server setups
- ❌ NOT ideal for: High-concurrency, distributed systems

## Cleanup

To manually clean up old sessions:

```python
# In Python shell or script
from orchestration.state import get_state_manager

state_manager = get_state_manager()
state_manager.cleanup_old_sessions(days=7)  # Remove sessions older than 7 days
```

## Troubleshooting

### Issue: "Session not found" after restart
**Solution**: Session might have been created before persistence was added
- Check `data/sessions/states.json` exists
- Create a new session to test

### Issue: Permission error writing to data/sessions/
**Solution**: Ensure the backend process has write permissions
```bash
chmod -R 755 src/backend/data/sessions/
```

### Issue: Corrupted states.json
**Solution**: Backup and regenerate
```bash
mv data/sessions/states.json data/sessions/states.json.backup
# Restart server - creates new empty states.json
```

## Summary

✅ **Problem Solved**: Sessions now persist across server restarts
✅ **Better UX**: Users don't lose progress when server restarts
✅ **Debugging**: New `/api/sessions` endpoint for visibility
✅ **Automatic Cleanup**: Prevents accumulation of old sessions
✅ **Zero Config**: Works out of the box with sensible defaults

The server will now maintain session state even through restarts, deployments, or code changes!

