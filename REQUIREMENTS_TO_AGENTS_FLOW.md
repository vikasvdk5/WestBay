# Requirements to Agents Flow - Complete Implementation

## Overview

This document explains how all form fields from the frontend flow through to the backend and influence the Lead Agent's decision-making on which agents to spawn and how many.

---

## ✅ Frontend Form Fields

### Fields Implemented in `ReportInputForm.tsx`:

1. **Research Topic** (Text Input) 
   - Field: `topic`
   - Required: Yes
   - Purpose: Main subject of research

2. **Detailed Requirements** (Textarea)
   - Field: `userRequest`
   - Required: Yes  
   - Purpose: Detailed description of what to research

3. **Page Count** (Integer Input)
   - Field: `pageCount`
   - Range: 10-60
   - Default: 20
   - Purpose: Target report length

4. **Number of Sources** (Integer Input)
   - Field: `sourceCount`
   - Range: 5-30
   - Default: 10
   - Purpose: How many sources to collect

5. **Report Complexity** (Select Dropdown)
   - Field: `complexity`
   - Options: **Low, Medium, High**
   - Default: Medium
   - Purpose: Determines depth and agent allocation

6. **Include Detailed Analysis** (Checkbox)
   - Field: `includeAnalysis`
   - Type: Boolean
   - Default: true
   - Purpose: Whether to deploy analyst agents

7. **Include Visualizations and Charts** (Checkbox)
   - Field: `includeVisualizations`
   - Type: Boolean
   - Default: true
   - Purpose: Whether analysts should create charts

---

## 🔄 Data Flow

### 1. Frontend Submission

When user clicks "Submit Requirements":

```typescript
const response = await apiService.submitRequirements(
  formData.userRequest,  // Detailed requirements
  {
    topic: formData.topic,
    page_count: formData.pageCount,
    source_count: formData.sourceCount,
    complexity: formData.complexity,  // "simple", "medium", or "complex"
    include_analysis: formData.includeAnalysis,
    include_visualizations: formData.includeVisualizations,
  }
)
```

### 2. Backend API Receives (`/api/submit-requirements`)

All fields are received and stored in:
- `user_request`: Detailed requirements text
- `report_requirements`: Object containing all configuration fields

### 3. Workflow Execution

When report generation starts:
1. Workflow creates `ContributionTracker`
2. Passes all requirements to Lead Researcher Agent
3. Lead Researcher analyzes requirements and makes decisions

---

## 🧠 Lead Researcher Decision Engine

### Decision Logic (`lead_researcher_decision.py`)

The Lead Researcher Agent uses **ALL** form fields to determine agent allocation:

#### Input Analysis:

```python
def analyze_requirements(
    topic: str,                    # From form
    detailed_requirements: str,    # From form
    page_count: int,              # From form
    source_count: int,            # From form
            complexity: str,              # From form: "simple", "medium", "complex"
    include_analysis: bool,       # From form
    include_visualizations: bool  # From form
) -> ResearchStrategy:
```

#### Decision Rules:

##### 1. **Data Collectors** (Based on Sources + Complexity)

```python
# Complexity multipliers
- Simple:  1.0x (easier = fewer agents needed)
- Medium:  1.5x
- Complex: 2.0x (harder = more agents needed)

# Sources per collector
sources_per_collector = max(3, int(5 / multiplier))

# Number of collectors
data_collectors = ceiling(source_count / sources_per_collector)

# Examples:
# - 10 sources, Simple complexity:  5 sources/collector  = 2 collectors
# - 10 sources, Medium complexity:  3-4 sources/collector = 3 collectors  
# - 20 sources, Complex complexity: 2-3 sources/collector = 7-10 collectors
```

##### 2. **API Researchers** (Based on Topic + Complexity)

```python
# Check if topic needs API data
api_keywords = ["market", "financial", "crypto", "stock", "economy", "technology"]
needs_api = any(keyword in topic or keyword in detailed_requirements)

if needs_api:
    if complexity == "medium":
        api_researchers = 1
    elif complexity == "complex":
        api_researchers = 2
    else:
        api_researchers = 0
else:
    api_researchers = 0

# Examples:
# - Topic: "Electric Vehicle Market" + Medium = 1 API researcher
# - Topic: "Crypto Market Analysis" + Complex = 2 API researchers
# - Topic: "History of Art" + Any = 0 API researchers
```

##### 3. **Analysts** (Based on Analysis Flag + Page Count + Visualizations)

```python
if include_analysis:
    # 1 analyst per 20 pages
    analysts = max(1, page_count // 20)
    
    # If visualizations requested, analysts create charts
    if include_visualizations:
        num_charts = max(2, page_count // 10)
        # Analysts will generate these charts
else:
    analysts = 0

# Examples:
# - 20 pages + Analysis = 1 analyst
# - 50 pages + Analysis = 2-3 analysts
# - 30 pages + Analysis + Viz = 1 analyst creating ~3 charts
# - No analysis flag = 0 analysts (data summarized directly)
```

---

## 📊 Example Decision Scenarios

### Scenario 1: Simple Report

**Input:**
- Topic: "History of Electric Cars"
- Detailed Requirements: "Brief overview of EV development"
- Page Count: 10
- Sources: 5
- Complexity: **Simple**
- Analysis: No
- Visualizations: No

**Lead Researcher Decision:**
```
✓ Data Collectors: 1 (5 sources, simple complexity)
✓ API Researchers: 0 (not a market topic)
✓ Analysts: 0 (no analysis requested)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Agents: 1
```

**Reasoning Logged:**
1. "Based on 5 sources and simple complexity, need 1 data collector (each handling ~5 sources)"
2. "Topic doesn't require external API data - using web sources only"
3. "No detailed analysis requested - data will be summarized directly"

---

### Scenario 2: Medium Market Research

**Input:**
- Topic: "Electric Vehicle Market Analysis"
- Detailed Requirements: "Analyze market size, growth, key players..."
- Page Count: 20
- Sources: 10
- Complexity: **Medium**
- Analysis: Yes
- Visualizations: Yes

**Lead Researcher Decision:**
```
✓ Data Collectors: 3 (10 sources ÷ 3-4 per collector)
✓ API Researchers: 1 (market topic detected)
✓ Analysts: 1 (20 pages, analysis requested)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Agents: 5
```

**Reasoning Logged:**
1. "Based on 10 sources and medium complexity, need 3 data collectors (each handling ~3-4 sources)"
2. "Topic mentions market/financial data - deploying 1 API researcher for external data sources"
3. "Analysis requested for 20-page report - deploying 1 analyst"
4. "Visualizations requested - analyst will generate 2 charts"

---

### Scenario 3: Complex Financial Report

**Input:**
- Topic: "Cryptocurrency Market Trends 2025"
- Detailed Requirements: "Deep dive into crypto markets, DeFi, regulatory impacts..."
- Page Count: 50
- Sources: 25
- Complexity: **Complex**
- Analysis: Yes
- Visualizations: Yes

**Lead Researcher Decision:**
```
✓ Data Collectors: 10 (25 sources ÷ 2-3 per collector, complex complexity)
✓ API Researchers: 2 (financial + crypto keywords detected)
✓ Analysts: 2 (50 pages ÷ 20 = 2-3 analysts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Agents: 14
```

**Reasoning Logged:**
1. "Based on 25 sources and complex complexity, need 10 data collectors (each handling ~2-3 sources)"
2. "Topic mentions market/financial data - deploying 2 API researchers for external data sources"
3. "Analysis requested for 50-page report - deploying 2 analysts"
4. "Visualizations requested - analysts will generate 5 charts"

---

## 📝 Comprehensive Logging

### Application Logs

Every decision is logged with `logger.info()`:

```
================================================================================
LEAD RESEARCHER DECISION ENGINE - ANALYZING REQUIREMENTS
================================================================================

📋 REQUIREMENT ANALYSIS:
   Topic: Electric Vehicle Market Analysis
   Page Count: 20
   Sources Needed: 10
   Complexity: medium
   Include Analysis: True
   Include Visualizations: True

🔍 DATA COLLECTION STRATEGY:
   Sources per collector: 3
   Data collectors needed: 3
   Reasoning: Based on 10 sources and medium complexity, need 3 data collectors

🌐 API RESEARCH STRATEGY:
   API researchers needed: 1
   Reasoning: Topic mentions market/financial data - deploying 1 API researcher

📊 ANALYSIS STRATEGY:
   Analysts needed: 1
   Reasoning: Analysis requested for 20-page report - deploying 1 analyst
   Visualizations: ~2 charts will be generated

================================================================================
FINAL RESEARCH STRATEGY
================================================================================
   Total agents to deploy: 5
   - Data Collectors: 3
   - API Researchers: 1
   - Analysts: 1

   REASONING SUMMARY:
   1. Based on 10 sources and medium complexity, need 3 data collectors
   2. Topic mentions market/financial data - deploying 1 API researcher  
   3. Analysis requested for 20-page report - deploying 1 analyst
   4. Visualizations requested - analyst will generate 2 charts
================================================================================
```

### Contribution Tracker Logs

The Lead Researcher also logs to the contribution tracker:

**File**: `data/agent-contribution/<session_id>/lead_researcher_YYYYMMDD_HHMMSS.json`

```json
{
  "agent_name": "lead_researcher",
  "agent_type": "lead_researcher",
  "status": "completed",
  "duration": 2.5,
  "task_description": "Analyze requirements and create research strategy",
  "actions_taken": [
    "Extracted report requirements from context",
    "Running decision engine to determine optimal agent configuration",
    "Decision: Deploy 5 agents total (3 collectors, 1 API researchers, 1 analysts)",
    "Creating detailed research plan with task allocation",
    "Created plan with 8 tasks",
    "Estimated cost: $0.0250"
  ],
  "output_summary": "Created research strategy: 5 agents (3 collectors, 1 API, 1 analysts)",
  "metrics": {
    "total_agents_allocated": 5,
    "data_collectors": 3,
    "api_researchers": 1,
    "analysts": 1,
    "complexity_level": "medium",
    "page_count": 20,
    "source_count": 10,
    "include_analysis": true,
    "include_visualizations": true,
    "estimated_sources_per_collector": 3,
    "total_subtasks": 8
  },
  "tools_used": [],
  "tokens_used": 2500,
  "estimated_cost": 0.025
}
```

### Summary Report

**File**: `data/agent-contribution/<session_id>/SUMMARY.md`

```markdown
## 🤖 Agent Contributions

### lead_researcher (lead_researcher)

- **Status:** completed
- **Duration:** 2.50s
- **Output:** Created research strategy: 5 agents (3 collectors, 1 API, 1 analysts)
- **Files Generated:** 0
- **Tools Used:** 0
- **Tokens:** 2,500
- **Cost:** $0.0250

**Decision Reasoning:**
1. Based on 10 sources and medium complexity, need 3 data collectors
2. Topic mentions market/financial data - deploying 1 API researcher
3. Analysis requested for 20-page report - deploying 1 analyst
4. Visualizations requested - analyst will generate 2 charts
```

---

## 🔍 Where to Find Logs

### 1. Application Console Logs
```bash
tail -f logs/app.log | grep "LEAD RESEARCHER"
```

### 2. Contribution Tracker Files
```bash
# View all agent contributions
ls -la data/agent-contribution/<session_id>/

# View lead researcher decision
cat data/agent-contribution/<session_id>/lead_researcher_*.json

# View summary
cat data/agent-contribution/<session_id>/SUMMARY.md
```

### 3. LangSmith Dashboard
- If LangSmith is configured, view traces at: https://smith.langchain.com
- Search for traces with tag: `lead_researcher`

---

## ✅ Implementation Complete

### What's Working:

1. ✅ **Frontend**: All 7 fields captured and sent to backend
2. ✅ **Backend API**: Receives and stores all fields
3. ✅ **Decision Engine**: Analyzes ALL fields to determine agent allocation
4. ✅ **Lead Researcher**: Uses decision engine and logs everything
5. ✅ **Contribution Tracker**: Captures all decisions and reasoning
6. ✅ **Application Logs**: Comprehensive logging of decision process
7. ✅ **Summary Reports**: Human-readable and machine-readable outputs

### Decision Factors:

- **Topic + Detailed Requirements** → Determine if API researchers needed
- **Source Count + Complexity** → Determine number of data collectors
- **Page Count + Analysis Flag** → Determine number of analysts
- **Visualizations Flag** → Determine if charts should be generated
- **Complexity** → Multiplier affecting all agent counts

---

## 🧪 Testing

To see the decision-making in action:

```bash
# 1. Start backend with logging
cd src/backend
python main.py | grep -E "LEAD RESEARCHER|DECISION ENGINE|STRATEGY"

# 2. Submit a report request from frontend

# 3. View the logs to see:
#    - Requirement analysis
#    - Decision logic
#    - Agent allocation
#    - Reasoning for each decision

# 4. Check contribution tracker:
ls -la data/agent-contribution/<session_id>/
cat data/agent-contribution/<session_id>/SUMMARY.md
```

---

## 📚 Key Files

1. **Frontend Form**: `src/frontend/src/components/ReportInputForm.tsx`
2. **Decision Engine**: `src/backend/agents/specialized/lead_researcher_decision.py`
3. **Lead Researcher**: `src/backend/agents/specialized/lead_researcher.py`
4. **Contribution Tracker**: `src/backend/utils/contribution_tracker.py`

---

**The complete flow from user input to intelligent agent allocation is now implemented with comprehensive logging and tracking!** 🚀

