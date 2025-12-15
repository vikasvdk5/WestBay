# System Architecture

## Overview

This Multi-Agent AI Market Research System is built on a sophisticated orchestrator-worker pattern using **LangGraph** for workflow management and **Google Gemini** as the primary LLM. The system coordinates 8 specialized agents to produce comprehensive market research reports with visualizations and citations.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    React Frontend (TypeScript + Vite)                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Report Input     │→ │Report Preview│→ │Report Viewer          │  │
│  │ Form             │  │              │  │  • HTML Preview       │  │
│  │  • Topic         │  │  • Structure │  │  • PDF Download       │  │
│  │  • Requirements  │  │  • Cost Est  │  │  • Citations         │  │
│  │  • Complexity    │  │              │  │  • Visualizations    │  │
│  └──────────────────┘  └──────────────┘  └───────────────────────┘  │
│           │ Dark/Light Theme Toggle                   ↑              │
└───────────┼─────────────────────────────────────────

───┼──────────────┘
            │ REST API (JSON)                           │
┌───────────▼───────────────────────────────────────────┴──────────────┐
│                      FastAPI Backend (Python 3.10+)                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │               LangGraph Workflow Orchestrator                   │  │
│  │                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │                  Cost Calculator Agent                    │  │  │
│  │  │          (Estimates tokens & costs pre-generation)        │  │  │
│  │  └─────────────────────────┬────────────────────────────────┘  │  │
│  │                            ↓                                    │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │              Lead Researcher Agent ⭐                     │  │  │
│  │  │   • Plans research strategy                              │  │  │
│  │  │   • Allocates agents dynamically                         │  │  │
│  │  │   • Determines agent count based on complexity           │  │  │
│  │  └─────────────────────────┬────────────────────────────────┘  │  │
│  │                            ↓                                    │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │                Synthesizer Agent                          │  │  │
│  │  │   • Creates dynamic report structure                     │  │  │
│  │  │   • 4 mandatory + dynamic sections                       │  │  │
│  │  └─────────────────────────┬────────────────────────────────┘  │  │
│  │                            ↓                                    │  │
│  │      ┌──────────────────────┼──────────────────────┐           │  │
│  │      ↓                      ↓                      ↓           │  │
│  │  ┌──────────┐      ┌──────────────┐      ┌────────────────┐  │  │
│  │  │   Data   │      │     API      │      │    Analyst     │  │  │
│  │  │Collector │      │  Researcher  │      │     Agent      │  │  │
│  │  │  Agent   │      │    Agent     │      │  • Analyzes    │  │  │
│  │  │ • Web    │      │  • Finds APIs│      │  • Charts      │  │  │
│  │  │  Scraping│      │  • Calls APIs│      │  • Insights    │  │  │
│  │  │ • LLM URL│      │  • LLM-driven│      │                │  │  │
│  │  │  Finding │      │              │      │                │  │  │
│  │  └────┬─────┘      └──────┬───────┘      └────────┬───────┘  │  │
│  │       └────────────────────┼──────────────────────┘           │  │
│  │                            ↓                                    │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │           Straight-Through-LLM Agent 🆕                   │  │  │
│  │  │   • Guarantees comprehensive content (250-400 words/sec) │  │  │
│  │  │   • Always executes regardless of other agents           │  │  │
│  │  │   • Generates professional narrative                     │  │  │
│  │  └─────────────────────────┬────────────────────────────────┘  │  │
│  │                            ↓                                    │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │                    Writer Agent                           │  │  │
│  │  │   • Merges all agent outputs                             │  │  │
│  │  │   • Generates Markdown, HTML, PDF                        │  │  │
│  │  │   • Embeds visualizations (base64)                       │  │  │
│  │  │   • Formats citations                                    │  │  │
│  │  └──────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Tools & Utilities                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌─────────────┐  │  │
│  │  │  Gemini  │  │   Web    │  │    API     │  │Contribution │  │  │
│  │  │   LLM    │  │ Scraper  │  │   Caller   │  │  Tracker    │  │  │
│  │  └──────────┘  └──────────┘  └────────────┘  └─────────────┘  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌─────────────┐  │  │
│  │  │   PDF    │  │Citation  │  │Visualization│  │   Memory    │  │  │
│  │  │Generator │  │ Manager  │  │  Generator  │  │ (ChromaDB)  │  │  │
│  │  └──────────┘  └──────────┘  └────────────┘  └─────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Data Persistence                             │  │
│  │  • Reports (Markdown, HTML, PDF)       • Research Notes        │  │
│  │  • Agent Contributions (JSON)          • Session State (JSON)  │  │
│  │  • Visualizations (PNG, HTML)          • Vector Store (ChromaDB)│ │
│  └────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
                                   ↓
┌───────────────────────────────────────────────────────────────────────┐
│                       External Services                                │
│  • Google Gemini API (LLM)                                            │
│  • LangSmith (Observability & Tracing)                                │
│  • External APIs (Market Data, Financial, etc.)                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Breakdown

### 1. Frontend Layer (React + TypeScript)

#### Component Structure
```typescript
App.tsx
├── Layout.tsx (Header, Footer, Theme Toggle)
├── ReportInputForm.tsx
│   ├── Topic Input
│   ├── Requirements Textarea
│   ├── Complexity Selector (Simple/Medium/Complex)
│   ├── Page Count (1-100)
│   ├── Source Count (0-30)
│   ├── Analysis Toggle
│   └── Visualization Toggle
├── ReportViewer.tsx
│   ├── HTML Preview (with base64 charts)
│   ├── PDF Download Button
│   ├── Citations Panel
│   └── Progress Indicator
└── services/api.ts (HTTP Client)
```

#### Key Features
- **Dark/Light Mode**: Full theme switching with Tailwind CSS
- **Real-time Progress**: WebSocket-style polling for status updates
- **Responsive Design**: Works on desktop, tablet, mobile
- **Citation Highlighting**: Click content → highlights source
- **PDF Preview**: Embedded PDF viewer or download

### 2. Backend Layer (FastAPI + Python)

#### API Routes (`api/routes.py`)
```python
POST   /api/submit-requirements      # Submit report requirements
GET    /api/cost-estimate/{sid}      # Get token/cost estimate
POST   /api/generate-report           # Start generation
GET    /api/report-status/{sid}      # Poll generation status
GET    /api/report/{sid}              # Get HTML report
GET    /api/report/{sid}/pdf          # Download PDF
GET    /api/sessions                  # List active sessions
GET    /api/health                    # Health check
```

#### Configuration (`config.py`)
```python
class Settings(BaseSettings):
    # Gemini Configuration
    gemini_api_key: str                          # From .env
    gemini_model: str = "gemini-2.5-pro"         # Current model
    
    # LangSmith (Observability)
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "market-research-agent"
    langchain_tracing_v2: bool = True
    
    # Storage Directories
    reports_dir: str = "./data/reports"
    research_notes_dir: str = "./data/research_notes"
    vector_store_path: str = "./data/vector_store"
    
    # API Configuration
    max_tokens_per_request: int = 100000
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
```

### 3. LangGraph Orchestration

#### State Management (`orchestration/state.py`)

```python
class AgentState(TypedDict):
    # Input
    user_request: str
    report_requirements: Dict[str, Any]
    
    # Workflow State
    session_id: str
    status: Annotated[str, take_last_status]  # Reducer for parallel updates
    current_agent: Annotated[Optional[str], take_last_agent]
    
    # Research Plan & Structure
    research_plan: Optional[Dict[str, Any]]
    cost_estimate: Optional[Dict[str, Any]]
    report_structure: Optional[Dict[str, Any]]
    
    # Research Data
    web_research_data: Optional[Dict[str, Any]]
    api_research_data: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    llm_generated_content: Optional[Dict[str, Any]]  # From Straight-Through-LLM
    
    # Final Output
    report_content: Optional[Any]
    report_path: Optional[str]
    pdf_path: Optional[str]
    citations: Annotated[List[Dict[str, Any]], add]
    
    # Task Tracking
    agent_tasks: Optional[Dict[str, List[Dict[str, Any]]]]
    agent_completion_status: Annotated[Optional[Dict[str, bool]], merge_completion_status]
    required_agents: Optional[List[str]]
    completed_tasks: Annotated[List[str], add]
    errors: Annotated[List[Dict[str, Any]], add]
    
    # Timestamps
    started_at: str
    updated_at: str
```

**Key Features:**
- **Reducer Functions**: Handle concurrent updates from parallel agents
- **Persistent State**: Saved to `data/sessions/` for recovery
- **Type Safety**: TypedDict ensures proper state structure

#### Workflow Graph (`orchestration/graph_builder.py`)

```python
def _build_graph(self):
    workflow = StateGraph(AgentState)
    
    # Add nodes for each agent
    workflow.add_node("cost_calculator", self._cost_calculator_node)
    workflow.add_node("lead_researcher", self._lead_researcher_node)
    workflow.add_node("synthesizer", self._synthesizer_node)
    workflow.add_node("data_collector", self._data_collector_node)
    workflow.add_node("api_researcher", self._api_researcher_node)
    workflow.add_node("analyst", self._analyst_node)
    workflow.add_node("straight_through_llm", self._straight_through_llm_node)
    workflow.add_node("check_completion", self._check_completion_node)
    workflow.add_node("writer", self._writer_node)
    
    # Define workflow edges
    workflow.set_entry_point("cost_calculator")
    workflow.add_edge("cost_calculator", "lead_researcher")
    workflow.add_edge("lead_researcher", "synthesizer")
    
    # Sequential execution with conditional routing
    workflow.add_edge("synthesizer", "data_collector")
    workflow.add_conditional_edges(
        "data_collector",
        self._route_after_data_collector,
        {"to_api": "api_researcher", "to_analyst": "analyst", 
         "to_llm": "straight_through_llm", "to_check": "check_completion"}
    )
    
    # Similar conditional routing for api_researcher and analyst
    workflow.add_edge("straight_through_llm", "check_completion")
    
    # Writer executes only after all required agents complete
    workflow.add_conditional_edges(
        "check_completion",
        self._route_to_writer_or_end,
        {"to_writer": "writer", "end": END}
    )
    
    workflow.add_edge("writer", END)
    
    return workflow.compile()
```

**Execution Flow:**
1. **Sequential Base**: `cost_calculator → lead_researcher → synthesizer`
2. **Conditional Execution**: Agents execute based on requirements
3. **Completion Check**: Ensures all agents finish before writer
4. **Final Synthesis**: Writer combines all outputs

### 4. Specialized Agents

#### 🎯 Agent 1: Cost Calculator Agent
- **File**: `agents/specialized/cost_calculator.py`
- **Prompt**: `prompts/cost_calculator.txt`
- **Purpose**: Pre-estimates token usage and costs
- **Logic**:
  ```python
  tokens = (page_count * 1000) + (source_count * 5000) * complexity_multiplier
  cost = (tokens * input_price) + (tokens * 0.5 * output_price)
  ```
- **Output**: Token estimate, cost estimate, recommendations

#### 🧠 Agent 2: Lead Researcher Agent
- **File**: `agents/specialized/lead_researcher.py`
- **Prompt**: `prompts/lead_agent.txt`
- **Purpose**: Orchestrates research strategy and agent allocation
- **Intelligence**: 
  - Analyzes topic complexity
  - Determines agent count (1-3 data collectors, 0-2 API researchers, 1-5 analysts)
  - Distributes tasks to agents
  - Creates comprehensive research plan
- **Decision Engine**: `lead_researcher_decision.py` with smart allocation logic

#### 📋 Agent 3: Synthesizer Agent
- **File**: `agents/specialized/synthesizer.py`
- **Prompt**: `prompts/synthesizer.txt`
- **Purpose**: Creates dynamic report structure
- **Features**:
  - 4 mandatory sections (Executive Summary, Market Overview, Key Findings, Conclusion)
  - Dynamic sections based on report type (Market Research, Technology Analysis, etc.)
  - Adjusts sections based on page count and complexity

#### 🌐 Agent 4: Data Collector Agent
- **File**: `agents/specialized/data_collector.py`
- **Prompt**: `prompts/researcher.txt`
- **Purpose**: Gathers data from web sources
- **LLM-Driven URL Discovery**: 
  - Uses Gemini to find top 3 relevant URLs for each sub-topic
  - Falls back to predefined URLs if needed
- **Web Scraping**: BeautifulSoup4 for content extraction
- **Citation Tracking**: Stores source URL, timestamp, content snippet

#### 🔌 Agent 5: API Researcher Agent
- **File**: `agents/specialized/api_researcher.py`
- **Prompt**: `prompts/api_researcher.txt`
- **Purpose**: Collects data from external APIs
- **LLM-Driven API Discovery**:
  - Uses Gemini to discover free/public APIs for the topic
  - Maps topics to relevant APIs (12+ predefined APIs available)
  - Uses OpenAPI specs to invoke APIs correctly
- **Handles**: Authentication, rate limiting, retries

#### 📊 Agent 6: Analyst Agent
- **File**: `agents/specialized/analyst.py`
- **Prompt**: `prompts/analyst.txt`
- **Purpose**: Analyzes data and generates visualizations
- **Capabilities**:
  - Extracts insights and trends
  - Generates chart specifications
  - Creates PNG charts (for PDF) and HTML charts (for web)
  - Saves to `data/reports/charts/`
- **Visualization Types**: Line, Bar, Pie, Scatter, Heatmap

#### 🤖 Agent 7: Straight-Through-LLM Agent (NEW!)
- **File**: `agents/specialized/straight_through_llm.py`
- **Prompt**: `prompts/straight-through-llm.txt`
- **Purpose**: **Guarantees comprehensive content generation**
- **Why Needed**: Ensures zero placeholder text even when other agents fail
- **How It Works**:
  - Receives report structure from Synthesizer
  - Generates 250-400 words per section using Gemini
  - Uses LLM's knowledge base for facts, trends, analysis
  - Provides citations for all claims
  - Always executes regardless of other agents' success
- **Output**: Complete section content for entire report (2,000-3,500 words)

#### ✍️ Agent 8: Writer Agent
- **File**: `agents/specialized/writer.py`
- **Prompt**: `prompts/synthesizer.txt` (merged)
- **Purpose**: Final report synthesis and formatting
- **Content Strategy**:
  1. **Prioritizes LLM content**: Uses Straight-Through-LLM content as base
  2. **Enhances with data**: Adds facts from Data Collector
  3. **Inserts statistics**: Incorporates API Researcher data
  4. **Embeds visualizations**: Integrates Analyst's charts
- **Output Formats**:
  - **Markdown**: Clean text for version control
  - **HTML**: With base64-encoded charts for preview
  - **PDF**: Professional formatting with embedded visualizations

### 5. Tools & Utilities

#### Gemini LLM Tool (`tools/gemini_llm.py`)
```python
class GeminiLLM:
    def __init__(self, model="gemini-2.5-pro"):
        self.model = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.gemini_api_key,
            temperature=1.0,
            max_tokens=65536
        )
    
    def generate(self, prompt, system_prompt="", **kwargs):
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        return self.model.invoke(messages, **kwargs)
```

#### Web Scraper Tool (`tools/web_scraper.py`)
- **Library**: BeautifulSoup4 + Requests
- **Features**: JavaScript-rendered page support, retry logic, timeout handling
- **Output**: Clean text, title, metadata, citations

#### API Caller Tool (`tools/api_caller.py`)
- **Auth Methods**: API Key, Bearer Token, Basic Auth, OAuth
- **Retry Logic**: Exponential backoff (3 attempts)
- **Rate Limiting**: Respect 429 responses with delays

#### Visualization Generator (`tools/visualization.py`)
- **Libraries**: Plotly (interactive), Matplotlib (static)
- **Output**: PNG (for PDF embedding), HTML (for web display)
- **Chart Types**: Line, Bar, Pie, Scatter, Area, Heatmap

#### PDF Generator (`utils/pdf_generator.py`)
- **Library**: ReportLab
- **Features**: Professional formatting, clickable citations, embedded images
- **Base64 Support**: Decodes base64 images from HTML for PDF embedding

#### Citation Manager (`utils/citation_manager.py`)
- **Deduplication**: Tracks unique sources by URL
- **Numbering**: Sequential [1], [2], [3]
- **Formats**: Numbered, APA, MLA
- **Linking**: Citations link to sources in reference section

#### Contribution Tracker (`utils/contribution_tracker.py`)
- **Purpose**: Full audit trail of agent actions
- **Tracks**:
  - Agent start/end times
  - Tools used with parameters
  - Token usage and costs
  - Output files generated
  - Errors and warnings
- **Output**: JSON files in `data/agent-contribution/{session_id}/`
- **File Naming**: `{agent_name}_{YYYYMMDD_HHMMSS}_{topic}.json`

### 6. Data Flow & Lifecycle

```
User Input → Session Creation → Cost Estimation
                                       ↓
                              Lead Researcher Planning
                                       ↓
                              Synthesizer (Structure)
                                       ↓
              ┌────────────────────────┼────────────────────────┐
              ↓                        ↓                        ↓
      Data Collector           API Researcher              Analyst
       (Web Data)                (API Data)              (Analysis)
              └────────────────────────┼────────────────────────┘
                                       ↓
                          Straight-Through-LLM
                          (Comprehensive Content)
                                       ↓
                              Check All Complete?
                                       ↓
                                   Writer
                                       ↓
                          Markdown + HTML + PDF
                                       ↓
                              User Downloads
```

### 7. Key Design Decisions

#### Why 8 Agents?
- **Specialization**: Each agent has a focused, well-defined purpose
- **Modularity**: Easy to add/remove agents without breaking the system
- **Parallelization**: Multiple agents can work simultaneously
- **Resilience**: Failure of one agent doesn't stop the entire workflow

#### Why Straight-Through-LLM?
- **Guarantee**: Ensures no placeholder text ever appears
- **Reliability**: Works even when web scraping/API calls fail
- **Quality**: Professional content from Gemini's knowledge base
- **Fallback**: Acts as safety net for the entire system

#### Why Base64 Embedding for Charts?
- **Portability**: HTML file is self-contained
- **Reliability**: No broken image links
- **Simplicity**: No need for image serving endpoints
- **PDF Compatibility**: Works in both HTML preview and PDF export

#### Why Sequential with Conditional Routing?
- **Predictability**: Easier to debug and trace
- **State Management**: Simpler than complex parallel merging
- **Dependencies**: Some agents need others' output
- **Observability**: Clear execution path in LangSmith

#### Why Prompt Files?
- **Separation of Concerns**: Agent logic separate from instructions
- **Easy Updates**: Modify behavior without touching code
- **Version Control**: Track prompt evolution independently
- **Consistency**: Standardized format across all agents

### 8. Observability & Monitoring

#### LangSmith Integration
```python
# In observability/langsmith_config.py
@trace_agent_call("agent_name")
def execute(self, ...):
    # Agent logic here
    pass
```

**Traced Information:**
- All LLM calls with prompts and responses
- Agent execution times
- Tool invocations
- State transitions
- Errors and exceptions

#### Contribution Tracking
Every agent logs:
- Start and end timestamps
- Input parameters
- Tools used
- Tokens consumed
- Costs incurred
- Output files
- Success/failure status

**Example Output** (`data/agent-contribution/{session_id}/SUMMARY.json`):
```json
{
  "session_id": "abc123",
  "total_duration": 45.2,
  "total_cost": 0.0234,
  "agents_executed": 8,
  "tools_used": 15,
  "output_files": ["report.pdf", "report.html", "chart_1.png"],
  "agent_contributions": [...],
  "status": "success"
}
```

### 9. Performance Characteristics

**Typical 15-page Report:**
- **Execution Time**: 30-60 seconds
- **Token Usage**: ~26,000 tokens
- **Cost**: ~$0.01-0.15 (depends on model)
- **Word Count**: 2,000-3,500 words
- **Citations**: 10-30 sources
- **Visualizations**: 2-5 charts

**Scaling:**
- 1-page report: ~15 seconds, $0.005
- 100-page report: ~5 minutes, $1.50

### 10. Security & Privacy

- **API Keys**: Stored in `.env`, never committed
- **Session Isolation**: Each session has unique ID
- **Data Persistence**: Optional, can be disabled
- **Rate Limiting**: Respects external API limits
- **Error Handling**: No sensitive data in error messages

### 11. Future Enhancements

- **Parallel Agent Execution**: Run data collectors in parallel
- **Streaming Responses**: Real-time content generation
- **Multi-Model Support**: Use different LLMs for different agents
- **Caching**: Cache LLM responses for similar queries
- **Advanced Visualizations**: Interactive charts in HTML
- **Export Formats**: PowerPoint, Word, Excel
- **Collaboration**: Multi-user editing of report structure

---

**This architecture demonstrates a production-ready multi-agent system with robust orchestration, comprehensive observability, and intelligent resource allocation—perfectly showcasing the power of agentic AI with Google Gemini.**
