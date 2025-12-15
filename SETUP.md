# Setup & Installation Guide

## Multi-Agent Market Research System

This guide will help you set up and run the complete multi-agent market research application.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **LangSmith API Key** (Optional, for observability)

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd src/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file with your keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here  # Optional
LANGSMITH_PROJECT=market-research-agent
```

### 5. Start Backend Server

```bash
python main.py
```

Backend will start on `http://localhost:8000`

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd src/frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment (Optional)

```bash
cp .env.example .env
```

Default configuration:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 4. Start Frontend Development Server

```bash
npm run dev
```

Frontend will start on `http://localhost:5173`

## Usage

### 1. Access the Application

Open your browser to `http://localhost:5173`

### 2. Create a Market Research Report

1. **Input Form**:
   - Enter research topic (e.g., "Electric Vehicle Market Analysis")
   - Provide detailed requirements
   - Configure page count, sources, complexity
   - Choose to include analysis and visualizations

2. **Preview & Cost Estimate**:
   - Review report structure
   - Check cost estimate (token usage and USD cost)
   - Confirm or adjust settings
   - Click "Generate Report"

3. **Report Generation**:
   - System coordinates multiple agents:
     - Lead Researcher creates plan
     - Data Collector scrapes web sources
     - API Researcher calls external APIs
     - Analyst analyzes data and creates insights
     - Writer generates final report
   - Real-time status updates show progress

4. **View Report**:
   - Read generated report
   - Browse citations and sources
   - Download as Markdown or PDF
   - View embedded visualizations

## Architecture Highlights

### Backend (Python + FastAPI + LangGraph)

- **6 Specialized Agents**: Lead Researcher, Data Collector, API Researcher, Analyst, Writer, Cost Calculator
- **LangGraph Orchestration**: Manages agent workflow with state persistence
- **Google Gemini Integration**: Primary LLM for all agent operations
- **Tools**: Web scraper, API caller, PDF generator, visualization creator
- **LangSmith Observability**: Complete tracing of agent interactions

### Frontend (React + TypeScript + Vite)

- **Modern UI**: Dark/light mode support, responsive design
- **Real-time Updates**: Polling for generation status
- **Cost Transparency**: Shows estimated costs before generation
- **Citation Tracking**: All claims linked to sources

## Project Structure

```
src/
├── backend/
│   ├── agents/
│   │   ├── planner.py              # Custom LangGraph planner
│   │   ├── executor.py             # LLM & tool execution
│   │   ├── memory.py               # Vector store & citations
│   │   ├── prompt_loader.py        # Loads prompts from prompts/
│   │   └── specialized/            # 6 specialized agents
│   ├── orchestration/
│   │   ├── graph_builder.py        # LangGraph workflow
│   │   └── state.py                # State management
│   ├── tools/
│   │   ├── gemini_llm.py          # Gemini API wrapper
│   │   ├── web_scraper.py         # BeautifulSoup scraper
│   │   └── api_caller.py          # External API client
│   ├── utils/
│   │   ├── visualization.py        # Chart generation
│   │   ├── pdf_generator.py       # PDF creation
│   │   └── citation_manager.py    # Citation tracking
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints
│   ├── observability/
│   │   └── langsmith_config.py    # LangSmith setup
│   ├── config.py                  # Configuration
│   └── main.py                    # FastAPI app
│
└── frontend/
    └── src/
        ├── components/
        │   ├── Layout.tsx          # Main layout with theme toggle
        │   ├── ReportInputForm.tsx # Requirements input
        │   ├── ReportPreview.tsx   # Structure preview & cost
        │   └── ReportViewer.tsx    # Final report display
        ├── services/
        │   └── api.ts              # Backend API client
        └── store/
            └── reportStore.ts      # Zustand state management
```

## Key Features

### ✅ Multi-Agent Architecture
- 6 specialized agents with clear responsibilities
- LangGraph orchestration with conditional routing
- Parallel execution where possible (data collection)

### ✅ Comprehensive Research
- Web scraping from multiple sources
- External API integration
- Data analysis with trend identification
- Visualization generation

### ✅ Cost Transparency
- Pre-generation cost estimates
- Token usage breakdown by agent
- Budget status indicators (green/yellow/red)
- Optimization recommendations

### ✅ Citation Tracking
- All sources tracked with URLs
- Automatic deduplication
- Clickable citation markers in reports
- Multiple citation styles

### ✅ Professional Output
- PDF generation with formatting
- Embedded visualizations
- Table of contents
- References section

### ✅ Observability
- LangSmith tracing (optional)
- Detailed logging
- Real-time status updates
- Error tracking

## Troubleshooting

### Backend Issues

**"GEMINI_API_KEY not found"**
- Ensure `.env` file exists in `src/backend/`
- Check that `GEMINI_API_KEY` is set correctly

**"Module not found" errors**
- Verify virtual environment is activated
- Run `pip install -r requirements.txt` again

**Port 8000 already in use**
- Change port in `.env`: `BACKEND_PORT=8001`
- Or kill process using port: `lsof -ti:8000 | xargs kill`

### Frontend Issues

**"Cannot connect to backend"**
- Ensure backend is running on port 8000
- Check CORS settings in `src/backend/main.py`

**"npm install" fails**
- Try `npm install --legacy-peer-deps`
- Clear npm cache: `npm cache clean --force`

**Port 5173 already in use**
- Vite will automatically try next available port
- Or specify port: `npm run dev -- --port 3000`

## Development Tips

### Adding New Agents

1. Create prompt file: `prompts/my_agent.txt`
2. Create agent class: `src/backend/agents/specialized/my_agent.py`
3. Load prompt: `load_agent_prompt('my_agent')`
4. Add to orchestration: `src/backend/orchestration/graph_builder.py`

### Modifying Agent Behavior

- Edit prompt files in `prompts/` directory
- No code changes needed for behavior adjustments
- Prompts are cached, so restart backend to see changes

### Debugging with LangSmith

1. Set `LANGSMITH_API_KEY` in `.env`
2. Visit [LangSmith dashboard](https://smith.langchain.com/)
3. View traces for each session
4. Inspect LLM prompts, responses, and execution flow

## Next Steps

1. **Test with Simple Query**: Start with a basic research topic
2. **Review Generated Report**: Check quality and citations
3. **Customize Prompts**: Adjust agent instructions in `prompts/`
4. **Add Custom Tools**: Extend functionality in `src/backend/tools/`
5. **Deploy**: Consider containerization with Docker

## Support

For issues or questions:
- Check `ARCHITECTURE.md` for system design
- Review `EXPLANATION.md` for technical details
- Examine `DEMO.md` for video walkthrough (after recording)

## License

See `LICENSE` file for details.

---

**Built for WestBay Hackathon 2025**
Powered by Google Gemini & LangGraph

