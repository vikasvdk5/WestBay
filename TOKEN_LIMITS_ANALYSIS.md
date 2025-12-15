# Token Limits Analysis

## Summary

Analysis of hard-coded token limits per agent and tool in the codebase.

---

## 🔍 Current Token Limits

### 1. **Config Setting (Not Currently Used)**

**File**: `src/backend/config.py`
```python
max_tokens_per_request: int = 100000
```

**Status**: ⚠️ **Defined but NOT used anywhere in the codebase**

This setting exists in the config but is never referenced. It appears to be a placeholder for future use.

---

### 2. **Gemini LLM Tool - Default Limit**

**File**: `src/backend/tools/gemini_llm.py`
```python
def __init__(self, ..., max_tokens: Optional[int] = None):
    self.max_tokens = max_tokens or 8192  # ← HARD DEFAULT LIMIT
```

**Limit**: **8,192 tokens per LLM call**

**How it works**:
- If `max_tokens` is provided → Uses that value
- If `max_tokens` is `None` → Defaults to **8,192 tokens**
- This limit applies to **each individual LLM API call**

**Usage**: All agents that use `GeminiLLM` directly can override this, but if they don't, they get 8,192 tokens.

---

### 3. **Agent Executor - Hardcoded Limit**

**File**: `src/backend/agents/executor.py`
```python
self.llm = ChatGoogleGenerativeAI(
    model=self.model_name,
    google_api_key=settings.gemini_api_key,
    temperature=0.7,
    max_tokens=8192,  # ← HARDCODED LIMIT
)
```

**Limit**: **8,192 tokens per LLM call**

**How it works**:
- This is **hardcoded** - cannot be overridden
- All agents using `AgentExecutor` are limited to 8,192 tokens per call
- This affects: Lead Researcher, Synthesizer, Data Collector, API Researcher, Analyst, Writer

---

## 📊 Impact Analysis

### Per-Agent Token Limits:

| Agent | Tool Used | Max Tokens Per Call | Can Override? |
|-------|-----------|---------------------|---------------|
| **Lead Researcher** | AgentExecutor | 8,192 | ❌ No (hardcoded) |
| **Synthesizer** | AgentExecutor | 8,192 | ❌ No (hardcoded) |
| **Data Collector** | AgentExecutor | 8,192 | ❌ No (hardcoded) |
| **API Researcher** | AgentExecutor | 8,192 | ❌ No (hardcoded) |
| **Analyst** | AgentExecutor | 8,192 | ❌ No (hardcoded) |
| **Writer** | AgentExecutor | 8,192 | ❌ No (hardcoded) |
| **Cost Calculator** | AgentExecutor | 8,192 | ❌ No (hardcoded) |

### Tools:

| Tool | Max Tokens | Can Override? |
|------|------------|---------------|
| **GeminiLLM** (direct) | 8,192 (default) | ✅ Yes (via parameter) |
| **AgentExecutor** | 8,192 | ❌ No (hardcoded) |

---

## ⚠️ Potential Issues

### 1. **8,192 Token Limit May Be Too Low**

For complex reports:
- **Writer Agent**: May need more tokens for long reports (10-60 pages)
- **Analyst Agent**: May need more tokens for complex analysis
- **Lead Researcher**: May need more tokens for detailed planning

**Example**:
- 30-page report ≈ 15,000-20,000 words ≈ 20,000-25,000 tokens
- Single LLM call limited to 8,192 tokens → May truncate output

### 2. **Config Setting Not Used**

`max_tokens_per_request: 100000` exists but is never applied. This could be:
- Used to override the hardcoded 8,192 limit
- Used for validation/checking before API calls
- Used for cost estimation

### 3. **No Per-Agent Customization**

All agents use the same 8,192 token limit, even though:
- Writer needs more tokens (long reports)
- Cost Calculator needs fewer tokens (simple calculations)
- Analyst may need more tokens (complex analysis)

---

## 🔧 Recommendations

### Option 1: Use Config Setting

Update `AgentExecutor` to use config:

```python
# executor.py
from config import settings

self.llm = ChatGoogleGenerativeAI(
    model=self.model_name,
    google_api_key=settings.gemini_api_key,
    temperature=0.7,
    max_tokens=settings.max_tokens_per_request,  # Use config
)
```

**Benefit**: Centralized control, easy to adjust

### Option 2: Per-Agent Limits

Allow agents to specify their own limits:

```python
# executor.py
def __init__(self, agent_name: str, system_prompt: str, max_tokens: Optional[int] = None):
    self.llm = ChatGoogleGenerativeAI(
        ...
        max_tokens=max_tokens or settings.max_tokens_per_request,
    )

# writer.py
self.executor = AgentExecutor(
    agent_name="writer",
    system_prompt=self.system_prompt,
    max_tokens=32000  # Higher limit for long reports
)
```

**Benefit**: Optimized limits per agent type

### Option 3: Dynamic Limits Based on Requirements

Adjust limits based on report requirements:

```python
# executor.py
def __init__(self, agent_name: str, system_prompt: str, context: Optional[Dict] = None):
    # Calculate max_tokens based on report requirements
    if context:
        page_count = context.get("report_requirements", {}).get("page_count", 20)
        complexity = context.get("report_requirements", {}).get("complexity", "medium")
        
        # Higher limit for longer/complex reports
        if page_count >= 40 or complexity == "complex":
            max_tokens = 32000
        elif page_count >= 20:
            max_tokens = 16384
        else:
            max_tokens = 8192
    else:
        max_tokens = 8192
    
    self.llm = ChatGoogleGenerativeAI(..., max_tokens=max_tokens)
```

**Benefit**: Adaptive limits based on actual needs

---

## 📋 Current Behavior

### What Happens Now:

1. **All LLM calls** are limited to **8,192 tokens output**
2. If an agent needs more tokens:
   - Response may be truncated
   - Agent may need to make multiple calls
   - May result in incomplete outputs

### Example Scenario:

**Writer Agent** generating a 30-page report:
- Estimated tokens needed: ~20,000
- Current limit: 8,192 tokens
- **Result**: Response will be truncated at 8,192 tokens
- **Impact**: Report may be incomplete

---

## ✅ Verification Commands

### Check Current Limits:

```bash
# Find all max_tokens settings
grep -r "max_tokens" src/backend/ --include="*.py"

# Check config usage
grep -r "max_tokens_per_request" src/backend/ --include="*.py"
```

### Test Token Limits:

```python
# Test if limit is enforced
from agents.executor import AgentExecutor

executor = AgentExecutor(agent_name="test", system_prompt="Test")
print(f"Max tokens: {executor.llm.max_tokens}")  # Should print: 8192
```

---

## 🎯 Summary

**Current State**:
- ✅ **Hard limit exists**: 8,192 tokens per LLM call
- ⚠️ **Applied to all agents**: Via AgentExecutor
- ⚠️ **Config setting unused**: `max_tokens_per_request: 100000` not applied
- ⚠️ **No per-agent customization**: All agents use same limit

**Recommendations**:
1. Use `settings.max_tokens_per_request` in AgentExecutor
2. Consider per-agent limits (Writer needs more, Calculator needs less)
3. Consider dynamic limits based on report requirements
4. Document token limits in agent documentation

---

**Current hard limit: 8,192 tokens per agent/tool LLM call** (via AgentExecutor)

