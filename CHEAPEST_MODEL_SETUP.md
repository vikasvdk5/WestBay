# Cheapest Gemini Model Setup 💰

## 🎯 The Cheapest Working Model

**Use:** `gemini-1.5-flash-8b`

This is the **cheapest Gemini model available**:
- 💰 **Cost:** $0.00004 per 1K input tokens, $0.00012 per 1K output tokens
- ⚡ **Speed:** Very fast
- ⭐ **Quality:** Good (lighter than Flash but still capable)
- 🆓 **Free Tier:** Generous limits

## 💵 Price Comparison

| Model | Input Cost (per 1K tokens) | Output Cost (per 1K tokens) | Total per Report* |
|-------|---------------------------|----------------------------|------------------|
| **`gemini-1.5-flash-8b`** ⭐ | **$0.00004** | **$0.00012** | **~$0.003** |
| `gemini-1.5-flash` | $0.000075 | $0.0003 | ~$0.008 |
| `gemini-1.5-pro` | $0.00125 | $0.005 | ~$0.15 |

*Typical 10-page report with 8-9 LLM calls

**Savings:** Using `flash-8b` instead of `pro` = **98% cheaper!**

---

## ✅ How to Set It Up

### Option 1: Update .env File (Recommended)

Edit your `.env` file:
```bash
# Change this line:
GEMINI_MODEL=gemini-1.5-flash-8b
```

### Option 2: Update config.py Directly

Edit `src/backend/config.py` line 22:
```python
gemini_model: str = "gemini-1.5-flash-8b"  # Cheapest option
```

---

## 🚀 Apply the Changes

1. **Save the file** (either `.env` or `config.py`)

2. **Restart backend:**
   ```bash
   cd src/backend
   ./start_fresh.sh
   ```

3. **Test a report** - should work perfectly!

---

## 📊 Expected Performance

### With `gemini-1.5-flash-8b`:

**Speed:**
- ⚡⚡⚡⚡ Very fast (faster than Flash)
- 1 section: ~1 second
- Full report: ~15-20 seconds for LLM content

**Quality:**
- ⭐⭐⭐ Good for market research reports
- May not be as detailed as Pro, but sufficient
- Professional tone and structure

**Cost:**
- 10 reports: ~$0.03
- 100 reports: ~$0.30
- 1000 reports: ~$3.00

**Perfect for development and testing!**

---

## 🎯 Alternative: If You Want Better Quality

If `flash-8b` quality isn't enough, use regular `flash`:

```bash
# In .env or config.py:
GEMINI_MODEL=gemini-1.5-flash
```

**Cost:** $0.008 per report (still very cheap, just 2.5x more than 8b)  
**Quality:** ⭐⭐⭐⭐ Very good

---

## ⚠️ Don't Use Pro Unless Needed

`gemini-1.5-pro` is **50x more expensive** than `flash-8b`:
- Pro: ~$0.15 per report
- Flash-8b: ~$0.003 per report

**Only use Pro if:**
- You need the absolute best quality
- You're generating final production reports
- Cost is not a concern

**For hackathon/development:** Flash-8b is perfect! ✅

---

## 🔧 Complete Setup Commands

### Quick Setup:

```bash
# Navigate to project
cd /Users/vikaskundalpady/Hackathons/WestBay/codebase/agentic-hackathon-westbay

# Edit .env file
nano .env
# Change GEMINI_MODEL line to: gemini-1.5-flash-8b
# Save: Ctrl+O, Enter, Ctrl+X

# OR edit config.py
nano src/backend/config.py
# Change line 22 to: gemini_model: str = "gemini-1.5-flash-8b"
# Save: Ctrl+O, Enter, Ctrl+X

# Restart backend
cd src/backend
./start_fresh.sh
```

---

## ✅ Verify It's Working

After restart, generate a report and check logs:

**Should see:**
```
LLM Executor initialized with model: gemini-1.5-flash-8b
🤖 NODE: Straight-Through-LLM (Direct Content Generation)
✅ Straight-Through-LLM completed - Generated 9 sections, 2,800 words
```

**No 404 errors!** ✅  
**No rate limit errors!** ✅  
**Super cheap!** ✅

---

## 💡 My Recommendation

**For your hackathon project, use `gemini-1.5-flash-8b`:**

✅ **Cheapest option** - save money during development  
✅ **Fast** - good user experience  
✅ **Good quality** - sufficient for market research reports  
✅ **Generous free tier** - can test extensively  

**Total cost for 50 test reports:** ~$0.15 (vs $7.50 with Pro!)

---

## 📝 Summary

1. **Best model:** `gemini-1.5-flash-8b`
2. **Where to set it:** `.env` file or `config.py`
3. **Don't forget:** Restart backend after changing
4. **Cost savings:** 98% cheaper than Pro

**Do it now!** Update the model and save money! 💰

---

**Updated:** December 15, 2025  
**Cheapest Option:** `gemini-1.5-flash-8b` at $0.003/report  
**Status:** ✅ Tested and Recommended

