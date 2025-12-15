#!/usr/bin/env python3
"""
Simple script to list available Gemini models.
Doesn't require any dependencies except google-generativeai.
"""

import os
import google.generativeai as genai

# Get API key from environment
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in environment")
    print()
    print("Set it with:")
    print('  export GEMINI_API_KEY="your-key-here"')
    exit(1)

print("=" * 80)
print("AVAILABLE GEMINI MODELS")
print("=" * 80)
print()

try:
    genai.configure(api_key=api_key)
    
    models = list(genai.list_models())
    
    # Filter for models that support generateContent
    content_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    
    if not content_models:
        print("❌ No models found!")
        exit(1)
    
    print(f"✅ Found {len(content_models)} models:\n")
    
    for i, model in enumerate(content_models, 1):
        model_name = model.name.replace('models/', '')
        
        print(f"{i}. {model_name}")
        print(f"   📝 {model.display_name}")
        print(f"   📊 Input: {model.input_token_limit:,} tokens")
        print(f"   📤 Output: {model.output_token_limit:,} tokens")
        print()
    
    print("=" * 80)
    print("RECOMMENDED MODELS:")
    print("=" * 80)
    print()
    
    # Find specific models
    for model in content_models:
        model_name = model.name.replace('models/', '')
        
        if 'flash' in model_name.lower() and 'exp' not in model_name.lower():
            print(f"⚡ FAST: {model_name}")
            print(f"   Use this in config.py: gemini_model = \"{model_name}\"")
            print()
        
        if 'pro' in model_name.lower() and 'vision' not in model_name.lower():
            print(f"🎯 QUALITY: {model_name}")
            print(f"   Use this in config.py: gemini_model = \"{model_name}\"")
            print()

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Check:")
    print("  1. API key is valid")
    print("  2. Internet connection works")

