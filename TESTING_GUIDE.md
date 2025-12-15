# Testing Guide: Straight-Through-LLM & Visualization Fixes

## Quick Start Testing

### Step 1: Restart Backend
```bash
cd /Users/vikaskundalpady/Hackathons/WestBay/codebase/agentic-hackathon-westbay/src/backend
./start_fresh.sh
```

Wait for: `INFO: Application startup complete.`

### Step 2: Open Frontend
```bash
# In a new terminal
cd /Users/vikaskundalpady/Hackathons/WestBay/codebase/agentic-hackathon-westbay/src/frontend
npm run dev
```

Open: `http://localhost:5173`

### Step 3: Submit Test Report

**Test Case 1: Simple Report**
```
Research Topic: Apple Inc Market Analysis
Detailed Requirements: Analyze Apple's market position in China
Report Complexity: Simple
Page Count: 10
Number of Sources: 5
☑ Include detailed analysis
☑ Include visualizations and charts
```

Click "Submit Requirements"

### Step 4: Monitor Progress

**Watch Backend Logs For:**
```
🤖 NODE: Straight-Through-LLM (Direct Content Generation)
Generating comprehensive content for: Apple Inc Market Analysis
Report structure: 8 sections
✅ Straight-Through-LLM completed - Generated 8 sections, 2,800 words
```

**Watch Frontend For:**
- Progress bar advancing
- Agent names changing: cost_calculator → lead_researcher → synthesizer → data_collector → api_researcher → analyst → straight_through_llm → writer
- "Completed Tasks" list growing

### Step 5: Verify Results

#### 5a. Check Content Quality
**What to look for:**
- ✅ Every section has 200-400 words of professional content
- ✅ NO "content will be generated based on research findings" placeholders
- ✅ Content reads like a business report (not generic filler)
- ✅ Multiple paragraphs per section

**Example of good content:**
> "The Chinese market represents a critical frontier for Apple Inc., contributing approximately 18-20% of the company's total revenue in recent years..."

**Bad (placeholder text):**
> "Content for Market Overview section will be generated based on research findings."

#### 5b. Check Visualizations
**What to look for:**
- ✅ Charts appear in the HTML preview (not broken image icons)
- ✅ Charts have titles and descriptions
- ✅ Charts are properly formatted (not tiny or huge)

**How to verify:**
1. Scroll through report preview
2. Look for section titled "Data Visualizations" or similar
3. Should see bar charts, line charts, etc. rendered inline
4. Right-click on chart → "Inspect" → should see `<img src="data:image/png;base64,..."`

#### 5c. Check PDF Export
**What to look for:**
- ✅ Click "Download PDF" button
- ✅ PDF opens with all content
- ✅ Charts are visible in the PDF (not blank spaces)
- ✅ Professional formatting maintained

#### 5d. Check Agent Contributions
**Terminal command:**
```bash
# Find the latest session directory
cd data/agent-contribution
ls -lt | head -n 5

# Enter the session directory (replace with actual session ID)
cd <session_id>

# List all agent contributions
ls -l
```

**Expected files:**
```
lead_researcher_20251215_143022_apple_inc_market_analysis.json
synthesizer_20251215_143023_apple_inc_market_analysis.json
data_collector_20251215_143025_apple_inc_market_analysis.json
api_researcher_20251215_143027_apple_inc_market_analysis.json
analyst_20251215_143029_apple_inc_market_analysis.json
straight_through_llm_20251215_143031_apple_inc_market_analysis.json ← NEW!
writer_20251215_143033_apple_inc_market_analysis.json
SUMMARY.json
SUMMARY.md
```

**Check Straight-Through-LLM contribution:**
```bash
cat straight_through_llm_*.json | jq .
```

**Expected structure:**
```json
{
  "agent_name": "straight_through_llm",
  "session_id": "...",
  "start_time": "...",
  "end_time": "...",
  "status": "completed",
  "tools_used": [...],
  "output_files": [],
  "summary": {
    "sections_generated": 8,
    "total_word_count": 2847,
    "section_contents": [
      {
        "section_id": "executive_summary",
        "section_title": "Executive Summary",
        "content": "The Chinese market represents...",
        "word_count": 356,
        "citations": [...]
      },
      ...
    ]
  }
}
```

## Test Cases

### Test Case 1: Simple Report ✓
**Purpose**: Verify basic functionality
```
Topic: Apple Inc Market Analysis
Pages: 10
Sources: 5
Complexity: Simple
Analysis: Yes
Visualizations: Yes
```
**Expected**: ~2,500 words, 2 charts, 8 sections, ~30 seconds

### Test Case 2: Complex Report
**Purpose**: Verify scaling
```
Topic: Global Electric Vehicle Market Trends 2024
Pages: 25
Sources: 15
Complexity: Complex
Analysis: Yes
Visualizations: Yes
```
**Expected**: ~6,000 words, 4-5 charts, 10+ sections, ~60 seconds

### Test Case 3: Minimal Requirements
**Purpose**: Verify minimum viable report
```
Topic: Coffee Industry Overview
Pages: 1
Sources: 0
Complexity: Simple
Analysis: No
Visualizations: No
```
**Expected**: Still generates ~400 words, no charts, basic sections

### Test Case 4: Obscure Topic (Resilience Test)
**Purpose**: Verify LLM agent compensates for limited data
```
Topic: Quantum Computing Applications in Agriculture
Pages: 15
Sources: 10
Complexity: Complex
Analysis: Yes
Visualizations: Yes
```
**Expected**: 
- Data collector may find limited URLs
- API researcher may find no APIs
- BUT: Straight-Through-LLM still generates comprehensive content
- Report is still professional and complete

### Test Case 5: Visualization-Heavy Report
**Purpose**: Verify chart embedding
```
Topic: Financial Performance Analysis - Tesla Inc
Pages: 20
Sources: 10
Complexity: Complex
Analysis: Yes
Visualizations: Yes
```
**Expected**: 
- 4-5 charts generated
- All charts visible in HTML preview
- All charts in PDF download
- Charts have proper titles and descriptions

## Troubleshooting

### Issue 1: "Content will be generated..." still appears
**Cause**: Straight-Through-LLM agent didn't execute or failed
**Check**:
```bash
# Backend logs - search for:
grep "Straight-Through-LLM" backend.log
grep "straight_through_llm" backend.log
```
**Expected to see**:
```
🤖 NODE: Straight-Through-LLM (Direct Content Generation)
✅ Straight-Through-LLM completed - Generated X sections, Y words
```
**If missing**: Agent didn't run - check required_agents in state

### Issue 2: Charts not visible in HTML preview
**Cause**: Base64 embedding failed or paths incorrect
**Check**:
```bash
# Backend logs - search for:
grep "Embedded visualization" backend.log
```
**Expected to see**:
```
✅ Embedded visualization 1 as base64 (150234 bytes)
✅ Embedded visualization 2 as base64 (148932 bytes)
```
**If see warnings**:
```
⚠️  Chart file not found: ./data/reports/charts/chart_1.png
```
**Fix**: Check analyst agent generated charts:
```bash
ls -l data/reports/charts/
```

### Issue 3: Workflow hangs at "straight_through_llm"
**Cause**: Agent not marked as complete
**Check**:
```bash
# Check state file
cat data/sessions/states.json | jq '.[] | select(.current_agent == "straight_through_llm")'
```
**Look for**: `"agent_completion_status": {"straight_through_llm": true}`
**If false**: Check backend logs for errors in the agent

### Issue 4: No agent contribution file for straight_through_llm
**Cause**: ContributionTracker not passed to agent
**Check**:
```bash
# Backend logs
grep "ContributionTracker" backend.log | grep "straight_through_llm"
```
**Expected**: Should see tracker being created and used
**If missing**: Check graph_builder._straight_through_llm_node passes tracker

### Issue 5: Old Python bytecode running
**Symptom**: Changes not reflecting, old errors persist
**Fix**:
```bash
cd src/backend
# Remove all bytecode
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Restart with fresh code
./start_fresh.sh
```

## Success Indicators

### ✅ All Green (Success):
- [x] Report generates within 20-40 seconds
- [x] All sections have 200+ words of content
- [x] No placeholder text anywhere
- [x] Visualizations appear in HTML preview
- [x] Visualizations appear in PDF download
- [x] Agent contribution file created for straight_through_llm
- [x] Backend logs show "Straight-Through-LLM completed"
- [x] Frontend shows "Report generation complete"

### ⚠️ Partial (Needs Investigation):
- [ ] Some sections have content, others don't
- [ ] Only 1-2 agents have contribution files
- [ ] Charts generated but not visible
- [ ] Workflow completes but report is short
- [ ] Backend logs show warnings

### ❌ Red (Failure):
- [ ] Workflow hangs indefinitely
- [ ] All sections are placeholders
- [ ] No charts generated at all
- [ ] Backend crashes with errors
- [ ] Frontend shows error message

## Performance Benchmarks

### Expected Timings (10-page report):
```
Cost Calculator: 2-3 seconds
Lead Researcher: 3-5 seconds
Synthesizer: 2-3 seconds
Data Collector: 5-8 seconds (web scraping)
API Researcher: 3-5 seconds
Analyst: 4-6 seconds (analysis + chart generation)
Straight-Through-LLM: 10-15 seconds (8 sections × 1-2s each)
Writer: 4-6 seconds (assembly + HTML + PDF)

Total: 30-45 seconds
```

### Token Usage (10-page report):
```
Cost Calculator: ~1,000 tokens
Lead Researcher: ~3,000 tokens
Synthesizer: ~2,000 tokens
Data Collector: ~2,000 tokens
API Researcher: ~2,000 tokens
Analyst: ~3,000 tokens
Straight-Through-LLM: ~8,000 tokens ← NEW
Writer: ~5,000 tokens

Total: ~26,000 tokens (~$0.0039 at Gemini pricing)
```

### File Sizes:
```
Markdown Report: ~15-25 KB
HTML Report (with base64 charts): ~250-400 KB
PDF Report: ~200-350 KB
Agent Contribution Files: ~5-10 KB each
```

## Quick Validation Commands

### One-liner to check if implementation is working:
```bash
cd src/backend && \
grep -q "straight_through_llm" orchestration/graph_builder.py && \
grep -q "llm_generated_content" orchestration/state.py && \
grep -q "llm_content" agents/specialized/writer.py && \
echo "✅ Implementation files updated" || echo "❌ Files missing changes"
```

### Check if agent is being allocated:
```bash
cd src/backend && \
python3 -c "
from agents.specialized.lead_researcher_decision import LeadResearcherDecisionEngine
engine = LeadResearcherDecisionEngine()
strategy = engine.analyze_requirements(
    topic='Test',
    detailed_requirements='Test report',
    page_count=10,
    source_count=5,
    complexity='simple',
    include_analysis=True,
    include_visualizations=True
)
agents = [alloc.agent_type for alloc in strategy.agent_allocations]
print('✅ straight_through_llm included' if 'straight_through_llm' in agents else '❌ straight_through_llm MISSING')
print(f'Agents allocated: {agents}')
"
```

### Check latest report for content quality:
```bash
cd src/backend && \
LATEST_REPORT=$(ls -t data/reports/*.md | head -1) && \
WORD_COUNT=$(wc -w < "$LATEST_REPORT") && \
PLACEHOLDER_COUNT=$(grep -c "will be generated" "$LATEST_REPORT" || echo 0) && \
echo "Report: $LATEST_REPORT" && \
echo "Word count: $WORD_COUNT" && \
echo "Placeholders: $PLACEHOLDER_COUNT" && \
if [ $WORD_COUNT -gt 2000 ] && [ $PLACEHOLDER_COUNT -eq 0 ]; then \
    echo "✅ Report quality: GOOD"; \
else \
    echo "⚠️  Report quality: NEEDS IMPROVEMENT"; \
fi
```

## Contact Points

If issues persist:
1. Check `STRAIGHT_THROUGH_LLM_IMPLEMENTATION_COMPLETE.md` for implementation details
2. Check `IMPLEMENTATION_PLAN_STRAIGHT_THROUGH_LLM.md` for design rationale
3. Review backend logs at `src/backend/*.log` (if logging to file)
4. Check terminal output for real-time error messages

---

**Happy Testing! 🚀**

Report any issues with:
- Exact error messages
- Backend log excerpts
- Session ID of failing report
- Steps to reproduce
