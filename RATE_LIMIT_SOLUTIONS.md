# Gemini API Rate Limit Solutions

## 🚨 Problem

```
429 You exceeded your current quota
Quota exceeded for metric: generate_content_free_tier_requests
Limit: 20 requests/day
Model: gemini-2.5-flash-lite
```

**Current Situation:**
- Free tier: 20 requests per day
- Your app: 8-9 requests per report (one per section)
- **Result**: Can only generate 2-3 reports per day

---

## ✅ Solutions (Choose One)

### Solution 1: Upgrade to Paid Tier (RECOMMENDED) 💳

**Cost:** ~$0.10-0.50 per report (very affordable!)

**Benefits:**
- ✅ 1,500 requests per minute (vs 20 per day)
- ✅ Unlimited reports
- ✅ Better performance
- ✅ No waiting

**How to Upgrade:**

1. **Enable billing in Google Cloud:**
   - Go to: https://console.cloud.google.com/billing
   - Link a payment method
   - Enable billing for your project

2. **That's it!** Your API key automatically gets higher limits

3. **Monitor usage:**
   - https://ai.dev/usage?tab=rate-limit
   - Track costs and usage

**Pricing:**
- Gemini 1.5 Flash: $0.000075 per 1K input tokens, $0.0003 per 1K output tokens
- Typical report: ~26,000 tokens = **~$0.008 per report** (less than 1 cent!)

---

### Solution 2: Switch Model (Quick Fix) 🔄

Try a different Gemini model that might have different quotas.

**Edit `.env` file:**
```bash
# Current (hitting limit):
GEMINI_MODEL=gemini-2.5-flash-lite

# Option A: Try Flash (different quota pool)
GEMINI_MODEL=gemini-1.5-flash

# Option B: Try Pro (more capable, different quota)
GEMINI_MODEL=gemini-1.5-pro
```

**Or edit `config.py` directly:**
```python
# Line 22 in src/backend/config.py
gemini_model: str = "gemini-1.5-flash"  # Changed from gemini-2.5-flash-lite
```

**Then restart:**
```bash
cd src/backend
./start_fresh.sh
```

**Note:** Different models may have different free tier limits, but all free tiers are restrictive.

---

### Solution 3: Wait for Reset ⏰

**Free tier resets daily at midnight UTC**

**Check current time:**
```bash
date -u
```

**Calculate wait time:**
- If it's 04:57 UTC now, you have ~19 hours until midnight UTC
- Then you get another 20 requests

**Not practical for development!** Consider upgrading for smooth testing.

---

### Solution 4: Batch Sections (Reduce Calls) 🔧

Modify the code to generate multiple sections in one LLM call instead of one call per section.

**Current:** 9 sections = 9 LLM calls  
**Optimized:** 9 sections = 1 LLM call

**Implementation:**

Create a new file `src/backend/agents/specialized/straight_through_llm_batch.py`:

```python
def _generate_all_sections_batch(
    self,
    sections: List[Dict[str, Any]],
    user_requirements: Dict[str, Any],
    research_data: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate content for ALL sections in a single LLM call."""
    
    # Build comprehensive prompt
    prompt = f"""Generate comprehensive content for ALL {len(sections)} sections of this report.

REPORT TOPIC: {user_requirements.get('topic', 'Unknown')}
USER REQUIREMENTS: {user_requirements.get('detailed_requirements', '')}

SECTIONS TO GENERATE:
"""
    
    for i, section in enumerate(sections, 1):
        prompt += f"\n{i}. {section.get('title', 'Section')} (ID: {section.get('id')})"
        if section.get('description'):
            prompt += f"\n   Description: {section['description']}"
    
    prompt += """

INSTRUCTIONS:
- Generate 250-400 words for EACH section
- Format as JSON array with this structure:
[
  {
    "section_id": "executive_summary",
    "section_title": "Executive Summary",
    "content": "The Chinese market represents...",
    "word_count": 356
  },
  ...
]

Generate the JSON array now:"""

    # Single LLM call for all sections
    response = self.executor.llm_executor.invoke_with_system_prompt(
        system_prompt=self.system_prompt,
        user_message=prompt
    )
    
    # Parse JSON response
    try:
        section_contents = json.loads(response)
        return section_contents
    except json.JSONDecodeError:
        # Fallback: Extract JSON from response
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            section_contents = json.loads(json_match.group())
            return section_contents
        else:
            # Ultimate fallback: Generate sections one by one
            return [self._generate_section_content(s, user_requirements, research_data, sections) for s in sections]
```

**Update `execute()` method:**
```python
# In execute() method, replace:
section_contents = []
for section in sections:
    content = self._generate_section_content(...)
    section_contents.append(content)

# With:
section_contents = self._generate_all_sections_batch(
    sections=sections,
    user_requirements=user_requirements,
    research_data=research_data
)
```

**Result:** 1 LLM call instead of 9 = 20 reports per day instead of 2!

---

### Solution 5: Use Alternative LLM (Advanced) 🤖

Switch to a different LLM provider with more generous free tiers:

**Option A: OpenAI GPT-3.5 Turbo**
- Free tier: $5 credit
- More generous rate limits
- Update `executor.py` to use OpenAI instead of Gemini

**Option B: Anthropic Claude**
- Developer tier available
- Good rate limits
- Requires account setup

**Option C: Local LLM**
- Ollama + Llama 3
- Completely free
- No rate limits
- Requires local setup

**Not recommended for this hackathon** - stick with Gemini and upgrade to paid tier.

---

## 🎯 Recommended Approach

### For Development/Testing:
1. ✅ **Upgrade to paid tier** (~$0.01 per report)
   - Fastest solution
   - Best experience
   - Minimal cost

2. ✅ **Or implement batch processing** (Solution 4)
   - Reduces calls from 9 to 1
   - Still on free tier
   - More complex code

### For Production:
- ✅ **Always use paid tier**
- ✅ Implement rate limiting in your app
- ✅ Add retry logic with exponential backoff
- ✅ Monitor usage and costs

---

## 📊 Cost Analysis

### Free Tier:
- Cost: $0
- Limit: 20 requests/day
- Reports: 2-3 per day
- **Good for:** Initial testing only

### Paid Tier:
- Cost: ~$0.008-0.02 per report
- Limit: 1,500 requests/minute
- Reports: Unlimited
- **Good for:** Development, testing, production

### Example Costs:
```
10 reports/day   × $0.01 = $0.10/day  = $3/month
100 reports/day  × $0.01 = $1.00/day  = $30/month
1000 reports/day × $0.01 = $10.00/day = $300/month
```

**For a hackathon with 50-100 test reports:** ~$0.50-1.00 total cost!

---

## 🚀 Quick Action Plan

### Right Now (5 minutes):

1. **Enable billing:**
   - Go to https://console.cloud.google.com/billing
   - Add payment method
   - Enable billing for your project

2. **Verify upgrade:**
   ```bash
   # Try generating a report
   # Should work immediately after billing enabled
   ```

3. **Monitor usage:**
   - https://ai.dev/usage?tab=rate-limit
   - Set budget alerts in Google Cloud

### Alternative (if can't upgrade):

1. **Switch model:**
   ```bash
   # Edit .env
   GEMINI_MODEL=gemini-1.5-flash
   
   # Restart backend
   cd src/backend
   ./start_fresh.sh
   ```

2. **Implement batching** (Solution 4)
   - Reduces 9 calls to 1
   - Can generate 20 reports/day instead of 2

---

## 📞 Support Resources

- **Gemini API Docs:** https://ai.google.dev/gemini-api/docs/rate-limits
- **Usage Dashboard:** https://ai.dev/usage?tab=rate-limit
- **Billing Setup:** https://console.cloud.google.com/billing
- **Pricing:** https://ai.google.dev/pricing

---

## ✅ After Upgrading

You should see in logs:
```
🤖 NODE: Straight-Through-LLM (Direct Content Generation)
Generating content for 9 sections
✅ Straight-Through-LLM completed - Generated 9 sections, 2,800 words
```

**No more 429 errors!** 🎉

---

**Summary:** For smooth development, upgrade to paid tier (~$0.01 per report). It's the fastest, easiest, and most cost-effective solution for your hackathon project!

