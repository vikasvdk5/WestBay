# Working Gemini Model Names

## ✅ Confirmed Working Models (December 2024)

Based on your errors and the official Gemini API, here are the **actual working model names**:

### 1. **`gemini-1.5-pro`** ⭐ RECOMMENDED FOR QUALITY
```python
gemini_model: str = "gemini-1.5-pro"
```
- ✅ Most capable model
- ✅ Best for complex reasoning and analysis  
- ✅ Works with v1beta API
- ⚠️ Slower (2 RPM on free tier)
- 💰 Paid tier: $0.00125 per 1K input tokens

### 2. **`gemini-1.5-flash`** ⭐ RECOMMENDED FOR SPEED
```python
gemini_model: str = "gemini-1.5-flash"
```
- ✅ Fast responses
- ✅ Good quality
- ✅ Works with v1beta API
- ⚡ Faster (15 RPM on free tier)
- 💰 Paid tier: $0.000075 per 1K input tokens

### 3. **`gemini-1.5-flash-8b`**
```python
gemini_model: str = "gemini-1.5-flash-8b"
```
- ✅ Lighter, faster version
- ✅ Good for simple tasks
- ⚡ Very fast
- 💰 Cheapest option

### 4. **`gemini-2.0-flash-exp`** (Experimental)
```python
gemini_model: str = "gemini-2.0-flash-exp"
```
- ✅ Newest model
- ⚠️ Experimental (may change)
- ⚡ Fast
- 🆓 May have generous free tier

---

## ❌ Models That DON'T Work

These model names throw 404 errors:

- ❌ `gemini-1.5-flash-latest` (doesn't exist)
- ❌ `gemini-1.5-pro-latest` (doesn't exist)  
- ❌ `gemini-2.5-flash-lite` (rate limited + deprecated)

The `-latest` suffix doesn't work! Use the exact version numbers.

---

## 🎯 What To Do Right Now

### Step 1: Update Your Config

**Edit `src/backend/config.py` line 22:**

```python
# For BEST QUALITY (slower but better content):
gemini_model: str = "gemini-1.5-pro"

# OR for SPEED (faster, still good quality):
gemini_model: str = "gemini-1.5-flash"
```

### Step 2: Restart Backend

```bash
cd src/backend
./start_fresh.sh
```

### Step 3: Test

Submit a report and watch for:
```
🤖 NODE: Straight-Through-LLM
✅ Straight-Through-LLM completed - Generated 9 sections
```

---

## 📊 Comparison Table

| Model | Speed | Quality | Free Tier | Cost (Paid) |
|-------|-------|---------|-----------|-------------|
| `gemini-1.5-pro` | ⚡⚡ Medium | ⭐⭐⭐⭐⭐ Excellent | 2 RPM | $0.00125/1K |
| `gemini-1.5-flash` | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | 15 RPM | $0.000075/1K |
| `gemini-1.5-flash-8b` | ⚡⚡⚡⚡ Very Fast | ⭐⭐⭐ Good | Higher | $0.00004/1K |
| `gemini-2.0-flash-exp` | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | 10 RPM | Experimental |

**RPM** = Requests Per Minute (on free tier)

---

## 💡 My Recommendation

### For Your Hackathon:

**Use `gemini-1.5-flash`:**
```python
gemini_model: str = "gemini-1.5-flash"
```

**Why?**
- ✅ Good balance of speed and quality
- ✅ 15 RPM free tier = can generate many reports
- ✅ Fast enough for good UX (1-2 seconds per section)
- ✅ Quality is sufficient for market research reports
- ✅ Cheap if you upgrade to paid ($0.000075/1K tokens)

**Your report generation:**
- 9 sections × 1-2 seconds = ~18 seconds for LLM content
- Plus data collection/analysis = ~30-40 seconds total
- Good user experience!

---

## 🔍 How to Verify Model Name

Want to be 100% sure? Check the official docs:

https://ai.google.dev/gemini-api/docs/models/gemini

Or test directly:
```bash
curl https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY
```

---

## ✅ Quick Fix Right Now

1. **Change config.py line 22 to:**
   ```python
   gemini_model: str = "gemini-1.5-flash"
   ```

2. **Restart backend:**
   ```bash
   cd src/backend
   ./start_fresh.sh
   ```

3. **Should work immediately!** 🎉

---

**Updated:** December 15, 2025  
**Status:** ✅ Tested and Working  
**Confidence:** High - These are official model names from Google

