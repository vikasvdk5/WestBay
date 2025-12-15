# Prompt Merge and Agent Name Alignment

## Summary
Merged `report_writer.txt` prompt into `synthesizer.txt` and updated all references to align agent names and responsibilities across the codebase.

## Changes Made

### 1. Merged Prompts
- **Merged `report_writer.txt` into `synthesizer.txt`**
  - Added comprehensive report writing phase instructions to `synthesizer.txt`
  - The Synthesizer Agent now handles both:
    - **Phase 1**: Report structure creation (outline/sections)
    - **Phase 2**: Final report synthesis and writing (content generation)
  - Includes instructions for reading research data, synthesizing content, generating sections, formatting citations, creating HTML/PDF reports, and embedding visualizations

### 2. Updated Code References

#### `src/backend/agents/specialized/writer.py`
- Changed prompt loading from `load_agent_prompt('writer')` to `load_agent_prompt('synthesizer')`
- Writer Agent now uses the merged synthesizer prompt which includes both structure creation and report writing instructions

#### `src/backend/agents/prompt_loader.py`
- Updated prompt mapping:
  - `'writer'` → `'synthesizer.txt'` (was `'report_writer.txt'`)
  - Added `'synthesizer'` → `'synthesizer.txt'` mapping
- Both Writer and Synthesizer agents now use the same comprehensive prompt file

### 3. Updated Lead Agent Prompt

#### `prompts/lead_agent.txt`
- Updated to reflect actual agent names used in the codebase:
  - "researcher" → **Data Collector Agent**
  - "report-writer" → **Writer Agent** (uses Synthesizer prompt)
  - Added references to **API Researcher Agent**, **Analyst Agent**, **Synthesizer Agent**
- Updated workflow to reflect actual LangGraph orchestration:
  - Removed references to "Task tool" and "spawning subagents"
  - Added intelligent agent allocation using decision engine
  - Updated workflow order: Synthesizer → Data Collection → API Research → Analysis → Writer
- Updated delegation rules to match actual implementation
- Added agent allocation guidelines with examples based on requirements
- Updated examples to show decision-making process rather than subagent spawning

## Agent Responsibilities (Aligned)

### Synthesizer Agent
- **Phase 1**: Creates dynamic report structure based on requirements
- **Phase 2**: (Via Writer Agent) Synthesizes final report content

### Writer Agent
- Uses Synthesizer prompt (merged)
- Synthesizes all research findings into final report
- Generates Markdown, HTML, and PDF formats
- Embeds visualizations and formats citations

### Lead Researcher Agent
- Analyzes requirements and determines optimal agent allocation
- Uses decision engine to calculate number of agents needed
- Coordinates workflow (LangGraph handles execution)
- Logs all decision-making reasoning

### Data Collector Agent
- Conducts web research and scraping
- Collects data from predefined URLs

### API Researcher Agent
- Discovers and calls relevant public APIs
- Collects structured data from external APIs

### Analyst Agent
- Analyzes collected data
- Generates insights and statistics
- Creates visualizations (charts, graphs)

## Files Modified
1. `prompts/synthesizer.txt` - Merged report writing instructions
2. `prompts/lead_agent.txt` - Updated agent names and workflow
3. `src/backend/agents/specialized/writer.py` - Updated to use synthesizer prompt
4. `src/backend/agents/prompt_loader.py` - Updated prompt mappings

## Files Not Deleted
- `prompts/report_writer.txt` - Kept for reference (can be deleted if desired)

## Verification
- ✅ No linting errors
- ✅ Prompt loader mappings updated correctly
- ✅ Writer Agent loads synthesizer prompt
- ✅ Synthesizer Agent loads synthesizer prompt
- ✅ Lead Agent prompt reflects actual agent names and workflow

## Next Steps
- Test the system to ensure prompts are loaded correctly
- Verify that Writer Agent uses the merged prompt effectively
- Consider deleting `prompts/report_writer.txt` if no longer needed

