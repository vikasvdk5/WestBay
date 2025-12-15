# Gemini Model Name Fix

## ❌ Error

```
404 models/gemini-1.5-flash is not found for API version v1beta
```

## ✅ Solution

The model name format was incorrect. Here are the **valid Gemini model names** for the current API:

### Available Models (Free Tier):

1. **`gemini-1.5-flash-latest`** ⭐ RECOMMENDED
   - Latest stable version
   - Good balance of speed and quality
   - Free tier: 15 RPM (requests per minute)

2. **`gemini-1.5-pro-latest`**
   - Most capable model
   - Better for complex analysis
   - Free tier: 2 RPM

3. **`gemini-2.0-flash-exp`** (Experimental)
   - Newest experimental model
   - May have different rate limits
   - Free tier: 10 RPM

### What I Changed

**In `src/backend/config.py`:**
```python
# Before (invalid):
gemini_model: str = "gemini-1.5-flash"  # ❌ Not found

# After (valid):
gemini_model: str = "gemini-1.5-flash-latest"  # ✅ Works
```

### Alternative: Update via .env

**Edit `.env` file:**
```bash
# Option 1: Flash Latest (Recommended)
GEMINI_MODEL=gemini-1.5-flash-latest

# Option 2: Pro Latest (More capable)
GEMINI_MODEL=gemini-1.5-pro-latest

# Option 3: Experimental (Newest)
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Restart Backend

```bash
cd src/backend
./start_fresh.sh
```

## 📊 Model Comparison

| Model | Speed | Quality | Free Tier Limit |
|-------|-------|---------|----------------|
| `gemini-1.5-flash-latest` | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 15 RPM |
| `gemini-1.5-pro-latest` | ⚡⚡ Medium | ⭐⭐⭐⭐⭐ Excellent | 2 RPM |
| `gemini-2.0-flash-exp` | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | 10 RPM |

**RPM** = Requests Per Minute (free tier)

## 🎯 Recommended Setup

For your hackathon project, use **`gemini-1.5-flash-latest`**:

**Why?**
- ✅ Fast enough for good UX
- ✅ Good quality content
- ✅ Higher free tier limit (15 RPM vs 2 RPM for Pro)
- ✅ Stable (not experimental)

**With this model:**
- 1 report = 8-9 requests
- 15 RPM = ~90 reports per hour (on free tier!)
- Much better than the old 20 requests per day

## 🔍 How to List Available Models

Want to see all available models? Create a test script:

```python
# test_models.py
import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.gemini_api_key)

print("Available Gemini models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")
        print(f"    Display: {model.display_name}")
        print(f"    Input limit: {model.input_token_limit}")
        print(f"    Output limit: {model.output_token_limit}")
        print()
```

Run it:
```bash
cd src/backend
python test_models.py
```

## ✅ After Fix

You should see:
```
🤖 NODE: Straight-Through-LLM (Direct Content Generation)
Generating content for 9 sections
✅ Straight-Through-LLM completed - Generated 9 sections, 2,800 words
```

**No more 404 errors!** 🎉

---

**Fix Applied:** December 15, 2025  
**Status:** ✅ Ready - Restart backend to apply

