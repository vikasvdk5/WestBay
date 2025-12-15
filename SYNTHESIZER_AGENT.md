# Synthesizer Agent - Dynamic Report Structure Generation

## Overview

The **Synthesizer Agent** is a specialized agent responsible for creating intelligent, dynamic report structures based on research requirements. It's completely decoupled from the Lead Researcher's orchestration responsibilities, focusing solely on synthesizing the optimal report structure.

---

## 🎯 Purpose

**Decoupled Responsibility**: Separates report structure synthesis from agent orchestration

**Before**: Lead Researcher handled both orchestration AND report structure
**After**: 
- Lead Researcher → Orchestrates agents and research strategy
- Synthesizer Agent → Creates dynamic report structure

---

## ✨ Key Features

### 1. **Mandatory Sections** (Always Included)

Every report includes these 4 mandatory sections:

1. **Executive Summary** - High-level overview
2. **Introduction** - Background and objectives  
3. **Methodology** - Research approach
4. **References** - Citations and sources

### 2. **Dynamic Sections** (Context-Aware)

The Synthesizer intelligently adds sections based on:
- Research topic analysis
- Detailed requirements
- Report type detection
- Page count
- Complexity level
- Analysis requirements
- Visualization requirements

### 3. **Hierarchical Structure**

Supports multi-level hierarchy:
- **Sections** (main chapters)
- **Subsections** (sub-chapters)
- **Content Requirements** (what each section needs)

---

## 🔍 How It Works

### Step 1: Analyze Research Topic

The agent analyzes the topic and requirements to determine **report type**:

- **Market Research** - Market analysis, competitive landscape, trends
- **Technology Analysis** - Tech overview, use cases, ecosystem
- **Financial Analysis** - Financial performance, metrics, trends
- **Trend Analysis** - Current trends, emerging patterns, implications
- **Comparative Analysis** - Comparison criteria, side-by-side analysis
- **General Research** - Background, findings, discussion

### Step 2: Generate Dynamic Sections

Based on report type, it generates appropriate sections:

#### Market Research Report:
```
1. Executive Summary [Mandatory]
2. Introduction [Mandatory]
3. Market Overview
   3.1. Market Definition and Scope
   3.2. Market Size and Growth
4. Competitive Landscape
   4.1. Key Market Players
   4.2. Market Share Analysis
5. Market Trends and Drivers
   5.1. Growth Drivers
   5.2. Market Challenges
6. Market Forecast (if page_count >= 20)
7. Analysis (if include_analysis=true)
   7.1. Data Analysis
   7.2. Key Insights
   7.3. Data Visualizations (if include_visualizations=true)
8. Conclusions and Recommendations
   8.1. Key Conclusions
   8.2. Strategic Recommendations
9. Methodology [Mandatory]
10. References [Mandatory]
```

#### Technology Analysis Report:
```
1. Executive Summary [Mandatory]
2. Introduction [Mandatory]
3. Technology Overview
   3.1. Technical Fundamentals
   3.2. Evolution and Maturity
4. Use Cases and Applications
5. Technology Landscape
6. Analysis (if include_analysis=true)
7. Conclusions
   7.1. Summary of Findings
   7.2. Future Directions
8. Methodology [Mandatory]
9. References [Mandatory]
```

#### Financial Analysis Report:
```
1. Executive Summary [Mandatory]
2. Introduction [Mandatory]
3. Financial Overview
   3.1. Financial Performance
   3.2. Valuation Analysis
4. Financial Trends
5. Analysis (if include_analysis=true)
6. Conclusions and Recommendations
7. Methodology [Mandatory]
8. References [Mandatory]
```

---

## 📊 Intelligence & Flexibility

### Report Type Detection

Uses keyword analysis to determine report type:

```python
# Market Research keywords
["market", "industry", "market size", "market share", "competitive"]

# Technology Analysis keywords
["technology", "innovation", "technical", "architecture", "implementation"]

# Financial Analysis keywords  
["financial", "investment", "revenue", "profit", "valuation", "stock"]

# Trend Analysis keywords
["trend", "forecast", "prediction", "future", "outlook"]

# Comparative Analysis keywords
["compare", "comparison", "versus", "vs", "competitive"]
```

### Adaptive Section Generation

Sections adapt based on:

**Page Count**:
- Short reports (< 20 pages): Core sections only
- Medium reports (20-40 pages): Core + forecast/advanced sections
- Long reports (40+ pages): Full detailed structure

**Complexity**:
- Low: Simplified sections
- Medium: Standard sections with subsections
- High: Detailed sections with multiple subsections

**Analysis Flag**:
- `true`: Adds dedicated Analysis section with Data Analysis, Insights, Visualizations
- `false`: Sections focus on findings only

**Visualizations Flag**:
- `true`: Adds Data Visualizations subsection
- `false`: Text-based analysis only

---

## 🔧 Integration

### In Workflow (`graph_builder.py`)

The Synthesizer is a separate node in the LangGraph workflow:

```
START
  ↓
Lead Researcher (Orchestration + Strategy)
  ↓
Synthesizer (Report Structure)  ← NEW AGENT
  ↓
Data Collectors (Parallel)
  ↓
API Researchers (Parallel)
  ↓
Analysts (Parallel)
  ↓
Writer (Final Report)
  ↓
END
```

### Usage Example

```python
synthesizer = create_synthesizer_agent()

result = synthesizer.execute(
    topic="Electric Vehicle Market Analysis",
    detailed_requirements="Analyze EV market size, growth trends, key players...",
    context={
        "report_requirements": {
            "page_count": 30,
            "complexity": "medium",
            "include_analysis": True,
            "include_visualizations": True
        },
        "contribution_tracker": tracker
    }
)

report_structure = result["report_structure"]
sections = report_structure["sections"]
```

---

## 📝 Output Structure

### Report Structure Output

```json
{
  "agent": "synthesizer",
  "status": "completed",
  "report_structure": {
    "report_type": "market_research",
    "total_sections": 10,
    "mandatory_sections": 4,
    "dynamic_sections": 6,
    "sections": [
      {
        "section_id": "executive_summary",
        "title": "Executive Summary",
        "description": "High-level overview...",
        "mandatory": true,
        "subsections": [],
        "content_requirements": []
      },
      {
        "section_id": "market_overview",
        "title": "Market Overview",
        "description": "Current state of the market...",
        "mandatory": false,
        "subsections": [
          {
            "section_id": "market_definition",
            "title": "Market Definition and Scope",
            "description": "Define the market boundaries...",
            "subsections": [],
            "content_requirements": []
          },
          {
            "section_id": "market_size",
            "title": "Market Size and Growth",
            "description": "Current market size...",
            "subsections": [],
            "content_requirements": []
          }
        ],
        "content_requirements": [
          "Market size data",
          "Growth statistics",
          "Market segments"
        ]
      }
    ]
  },
  "metadata": {
    "topic": "Electric Vehicle Market Analysis",
    "page_count": 30,
    "complexity": "medium",
    "include_analysis": true,
    "include_visualizations": true
  }
}
```

---

## 📊 Contribution Tracking

The Synthesizer logs detailed metrics:

```json
{
  "agent_name": "synthesizer",
  "agent_type": "synthesizer",
  "status": "completed",
  "duration": 0.5,
  "task_description": "Create dynamic report structure for: Electric Vehicle Market Analysis",
  "actions_taken": [
    "Analyzing topic and requirements",
    "Created 4 mandatory sections",
    "Identified report type: market_research",
    "Generated 6 dynamic sections"
  ],
  "output_summary": "Created 10-section report structure (6 dynamic sections)",
  "metrics": {
    "total_sections": 10,
    "mandatory_sections": 4,
    "dynamic_sections": 6,
    "report_type": "market_research",
    "total_subsections": 8
  }
}
```

---

## 🎨 Extensibility

### Adding New Report Types

To add a new report type:

1. Update `_determine_report_type()` with new keywords
2. Create a new section generator method:
   ```python
   def _create_custom_type_sections(self, topic, requirements, page_count, include_analysis):
       sections = []
       # Add your custom sections
       return sections
   ```
3. Add case in `_generate_dynamic_sections()`

### Adding New Section Types

Create new `ReportSection` objects:

```python
section = ReportSection(
    section_id="custom_section",
    title="Custom Section Title",
    description="What this section covers",
    subsections=[
        ReportSection(
            section_id="custom_subsection",
            title="Subsection Title",
            description="Subsection content"
        )
    ],
    content_requirements=["Requirement 1", "Requirement 2"]
)
```

---

## 🔍 Logging

### Console Logs

```
================================================================================
📝 SYNTHESIZER AGENT - STARTING EXECUTION
================================================================================
Topic: Electric Vehicle Market Analysis
Requirements: Analyze EV market size, growth trends...

📊 Report Configuration:
   Page Count: 30
   Complexity: medium
   Include Analysis: True
   Include Visualizations: True

🔹 Creating mandatory sections...

🔍 Report Type: market_research

🔹 Generating dynamic sections...
   Generated 6 dynamic sections

📋 Final Report Structure (10 sections):
   1. Executive Summary
   2. Introduction
   3. Market Overview
      3.1. Market Definition and Scope
      3.2. Market Size and Growth
   4. Competitive Landscape
      4.1. Key Market Players
      4.2. Market Share Analysis
   5. Market Trends and Drivers
      5.1. Growth Drivers
      5.2. Market Challenges
   6. Market Forecast
   7. Analysis
      7.1. Data Analysis
      7.2. Key Insights
      7.3. Data Visualizations
   8. Conclusions and Recommendations
      8.1. Key Conclusions
      8.2. Strategic Recommendations
   9. Methodology
   10. References

✅ SYNTHESIZER COMPLETED SUCCESSFULLY
   Total sections: 10
   Mandatory: 4, Dynamic: 6
================================================================================
```

---

## ✅ Benefits

1. **Separation of Concerns**: 
   - Lead Researcher focuses on orchestration
   - Synthesizer focuses on structure

2. **Flexibility**:
   - Easy to add new report types
   - Easy to modify section logic
   - Adapt to different research domains

3. **Intelligence**:
   - Context-aware section generation
   - Hierarchical structure support
   - Adaptive to requirements

4. **Maintainability**:
   - Single responsibility
   - Clear, testable logic
   - Easy to extend

5. **Trackability**:
   - Full contribution logging
   - Clear decision visibility
   - Performance metrics

---

## 🧪 Testing

### Test Different Report Types:

```python
# Market Research
synthesizer.execute(
    topic="EV Market Analysis",
    detailed_requirements="Analyze market size, competitors...",
    context={...}
)
→ Generates: Market Overview, Competitive Landscape, Trends

# Technology Analysis  
synthesizer.execute(
    topic="AI Technology Overview",
    detailed_requirements="Technical architecture, use cases...",
    context={...}
)
→ Generates: Technology Overview, Use Cases, Landscape

# Financial Analysis
synthesizer.execute(
    topic="Tesla Financial Performance",
    detailed_requirements="Revenue, profitability, valuation...",
    context={...}
)
→ Generates: Financial Overview, Performance, Trends
```

---

## 📚 Key Files

- **Synthesizer Agent**: `src/backend/agents/specialized/synthesizer.py`
- **Integration Point**: `src/backend/orchestration/graph_builder.py` (to be updated)
- **Contribution Tracking**: `src/backend/utils/contribution_tracker.py`

---

**The Synthesizer Agent provides intelligent, flexible, and dynamic report structure generation tailored to each research request!** 🎯

