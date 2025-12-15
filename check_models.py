#!/usr/bin/env python3
"""Standalone script to check available Gemini models."""

import os
import sys

# Try to load .env
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent / '.env')
except:
    pass

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not found")
    print("Make sure it's in your .env file")
    sys.exit(1)

print("=" * 80)
print("AVAILABLE GEMINI MODELS")
print("=" * 80)
print()
print("🔑 API Key found (starts with: {}...)".format(api_key[:10]))
print()

try:
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    
    print("📋 Fetching models from Gemini API...")
    print()
    
    models = list(genai.list_models())
    
    # Filter for generateContent support
    content_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    
    print(f"✅ Found {len(content_models)} models that support generateContent:")
    print()
    
    for i, model in enumerate(content_models, 1):
        name = model.name.replace('models/', '')
        print(f"{i}. {name}")
        print(f"   📝 Display: {model.display_name}")
        print(f"   📊 Input: {model.input_token_limit:,} tokens | Output: {model.output_token_limit:,} tokens")
        print()
    
    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS FOR YOUR PROJECT:")
    print("=" * 80)
    print()
    
    flash_models = [m for m in content_models if 'flash' in m.name.lower()]
    pro_models = [m for m in content_models if 'pro' in m.name.lower() and 'vision' not in m.name.lower()]
    
    if flash_models:
        print("⚡ FOR SPEED & COST:")
        for m in flash_models[:2]:  # Show top 2
            name = m.name.replace('models/', '')
            print(f"   → {name}")
        print()
    
    if pro_models:
        print("🎯 FOR QUALITY:")
        for m in pro_models[:2]:  # Show top 2
            name = m.name.replace('models/', '')
            print(f"   → {name}")
        print()
    
    print("💡 Current setting in config.py: gemini-1.5-pro")
    print()

except ImportError:
    print("❌ google-generativeai not installed")
    print("Run: pip install google-generativeai")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

