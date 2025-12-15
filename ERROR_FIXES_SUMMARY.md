# Error Fixes Summary - December 15, 2025

## Issue 1: Writer Agent NoneType Error ✅ FIXED

**Error:**
```
'NoneType' object has no attribute 'get'
```

**Location:** `src/backend/agents/specialized/writer.py`

**Root Cause:**
The `_generate_sections()` method was calling `.get()` on potentially None values in:
1. `llm_sections` list items could be None
2. `section_spec` items could be None
3. `visualizations` list items could be None

**Fix Applied:**
Added defensive None checks throughout the `_generate_sections()` and `_generate_html_report()` methods:

```python
# Filter out None values from llm_sections
if llm_sections:
    llm_sections = [s for s in llm_sections if s is not None]

# Check section_spec before using
for section_spec in section_specs:
    if not section_spec:
        logger.warning("Encountered None section_spec, skipping")
        continue

# Additional safety check in iterator
llm_section = next(
    (s for s in llm_sections if s and s.get("section_id") == section_id),
    None
)

# Filter None values from visualizations
if visualizations:
    visualizations = [v for v in visualizations if v is not None]

# Check viz before using
if viz:  # Additional safety check
    content += f"**Figure {i}: {viz.get('title', 'Chart')}**\n\n"
```

**Files Modified:**
- `src/backend/agents/specialized/writer.py`

**Changes:**
- Lines 229-235: Added None filtering for `llm_sections`
- Lines 238-240: Added None check for `section_spec`
- Line 244: Added None check in `next()` iterator
- Lines 256-259: Added None filtering for visualizations
- Line 261: Added None check before using viz
- Lines 574-578: Added None filtering for HTML visualizations
- Line 580: Added None check before rendering viz in HTML
- Line 610: Added None check before accessing viz description

---

## Issue 2: Straight-Through-LLM Agent Method Error ✅ FIXED

**Error:**
```
'AgentExecutor' object has no attribute 'call_llm'
```

**Location:** `src/backend/agents/specialized/straight_through_llm.py`, line 220

**Root Cause:**
The code was calling a non-existent method `self.executor.call_llm()`. The `AgentExecutor` class doesn't have this method.

**Correct Architecture:**
```
AgentExecutor
  ├── tool_executor: ToolExecutor
  └── llm_executor: LLMExecutor
        ├── invoke(messages, **kwargs)
        └── invoke_with_system_prompt(system_prompt, user_message, **kwargs)
```

**Fix Applied:**
Changed the LLM invocation to use the correct method chain:

**Before:**
```python
content_text = self.executor.call_llm(
    prompt=prompt,
    temperature=0.7,
    max_tokens=800
)
```

**After:**
```python
content_text = self.executor.llm_executor.invoke_with_system_prompt(
    system_prompt=self.system_prompt,
    user_message=prompt,
    temperature=1.0,
    max_tokens=8000
)
```

**Files Modified:**
- `src/backend/agents/specialized/straight_through_llm.py`

**Changes:**
- Lines 220-224: Updated to use correct method path `self.executor.llm_executor.invoke_with_system_prompt()`

---

## Issue 3: Gemini API Parameter Error ✅ FIXED

**Error:**
```
GenerativeServiceClient.generate_content() got an unexpected keyword argument 'temperature'
```

**Location:** `src/backend/agents/specialized/straight_through_llm.py`, line 220

**Root Cause:**
The Gemini API (via `ChatGoogleGenerativeAI`) doesn't accept `temperature` and `max_tokens` as parameters during the `invoke()` call. These parameters must be set during model initialization, not at invocation time.

**Architecture:**
```
LLMExecutor.__init__():
  self.llm = ChatGoogleGenerativeAI(
      model=self.model_name,
      temperature=1.0,        ← Set here (at initialization)
      max_tokens=65536,       ← Set here (at initialization)
  )

invoke_with_system_prompt():
  # Cannot pass temperature/max_tokens here!
  response = self.llm.invoke(messages)  ← Use initialized settings
```

**Fix Applied:**
Removed `temperature` and `max_tokens` parameters from the `invoke_with_system_prompt()` call:

**Before:**
```python
content_text = self.executor.llm_executor.invoke_with_system_prompt(
    system_prompt=self.system_prompt,
    user_message=prompt,
    temperature=1.0,  # ❌ Not allowed at invoke time
    max_tokens=8000   # ❌ Not allowed at invoke time
)
```

**After:**
```python
content_text = self.executor.llm_executor.invoke_with_system_prompt(
    system_prompt=self.system_prompt,
    user_message=prompt
    # ✅ Uses temperature=1.0 and max_tokens=65536 from LLMExecutor initialization
)
```

**Note:** The `LLMExecutor` is already initialized with:
- `temperature=1.0` - Balanced creativity
- `max_tokens=65536` - More than sufficient for 300-400 words per section

**Files Modified:**
- `src/backend/agents/specialized/straight_through_llm.py`

**Changes:**
- Lines 220-225: Removed invalid parameters from invoke call

---

## Testing Status

### ✅ Fixed Issues:
1. Writer agent NoneType errors - comprehensive defensive programming added
2. Straight-Through-LLM agent LLM invocation - corrected method call
3. Gemini API parameter error - removed invalid invoke-time parameters

### 🧪 Ready for Testing:
Both fixes have been applied and the code is ready for end-to-end testing.

### 📋 Test Plan:
1. Restart backend: `cd src/backend && ./start_fresh.sh`
2. Submit test report through frontend
3. Monitor for:
   - Writer agent completing without NoneType errors
   - Straight-Through-LLM agent successfully generating content
   - All sections having real content (no placeholders)
   - Visualizations rendering in HTML and PDF

---

## Impact Assessment

### Risk Level: Low
- Changes are defensive (adding None checks)
- No breaking changes to existing functionality
- Falls back gracefully when data is missing

### Performance Impact: Negligible
- Added checks are simple boolean operations
- No additional I/O or computation
- Filtering None values is O(n) but lists are small (< 10 items typically)

### Code Quality: Improved
- More robust error handling
- Better logging for debugging
- Prevents crashes from unexpected None values
- Maintains backwards compatibility

---

## Root Cause Analysis

### Why Did These Errors Occur?

**Writer Agent Issue:**
- Recent integration of LLM-generated content added new data flows
- `llm_sections` is populated by Straight-Through-LLM agent
- If that agent fails or returns incomplete data, `None` values can appear
- Original code assumed all list items would be valid dictionaries

**Straight-Through-LLM Issue:**
- New agent created based on incorrect API assumptions
- `AgentExecutor` API wasn't fully understood
- Used method name that seemed intuitive but didn't exist
- Should have referenced existing agents' usage patterns

### Lessons Learned:
1. **Always validate external data**: Data from other agents should be validated
2. **Defensive programming**: Check for None before calling methods
3. **API documentation**: Reference actual class definitions, not assumptions
4. **Test incrementally**: Test new agents in isolation before integration

---

## Prevention Measures

### Implemented:
1. ✅ Comprehensive None checking in writer agent
2. ✅ Correct LLM executor usage pattern
3. ✅ Detailed error logging for debugging

### Recommended for Future:
1. Add type validation for agent outputs
2. Create unit tests for each agent's execute() method
3. Document AgentExecutor API usage patterns
4. Add integration tests for multi-agent workflows
5. Implement schema validation for agent state dictionaries

---

## Files Changed

### Modified:
1. `src/backend/agents/specialized/writer.py`
   - Added None filtering and checks
   - ~15 lines modified

2. `src/backend/agents/specialized/straight_through_llm.py`
   - Fixed LLM invocation method
   - ~5 lines modified

### No Changes Required:
- `src/backend/agents/executor.py` - Already correct
- `src/backend/orchestration/graph_builder.py` - Working as designed
- `src/backend/orchestration/state.py` - Correct structure

---

## Verification Checklist

Before marking as complete, verify:

- [ ] Backend restarts without errors
- [ ] Report generation workflow completes end-to-end
- [ ] Writer agent processes LLM content without errors
- [ ] Straight-Through-LLM agent generates content successfully
- [ ] All report sections have real content (250+ words each)
- [ ] Visualizations render in HTML preview
- [ ] Visualizations appear in downloaded PDF
- [ ] Agent contribution files created for all agents
- [ ] No NoneType errors in logs
- [ ] No "attribute 'call_llm'" errors in logs

---

**Fix Date:** December 15, 2025 04:25 AM  
**Status:** ✅ Fixes Applied - Ready for Testing  
**Confidence Level:** High - Both issues had clear root causes and straightforward fixes

