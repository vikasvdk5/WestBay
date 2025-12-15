#!/usr/bin/env python3
"""
Quick script to verify if a Gemini model exists and supports generateContent.
"""

import os
import sys

# Get API key from environment or .env file (in parent directory)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Load .env from parent directory (project root)
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except:
    pass

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found")
    print("Set it in .env file or environment")
    sys.exit(1)

# Models to test
models_to_test = [
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]

print("=" * 80)
print("VERIFYING GEMINI MODELS")
print("=" * 80)
print()

try:
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    
    # Get all available models
    all_models = list(genai.list_models())
    
    # Check each model we want to test
    for model_name in models_to_test:
        print(f"🔍 Testing: {model_name}")
        
        # Check if model exists in the list
        full_model_name = f"models/{model_name}"
        model_exists = any(m.name == full_model_name for m in all_models)
        
        if model_exists:
            # Get the model details
            model = next(m for m in all_models if m.name == full_model_name)
            
            # Check if it supports generateContent
            supports_generate = 'generateContent' in model.supported_generation_methods
            
            if supports_generate:
                print(f"   ✅ EXISTS and SUPPORTS generateContent")
                print(f"   📊 Input limit: {model.input_token_limit:,} tokens")
                print(f"   📤 Output limit: {model.output_token_limit:,} tokens")
            else:
                print(f"   ⚠️  EXISTS but does NOT support generateContent")
                print(f"   Supported methods: {', '.join(model.supported_generation_methods)}")
        else:
            print(f"   ❌ DOES NOT EXIST in v1beta API")
        
        print()
    
    print("=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    print()
    
    # Find the best working model
    working_models = []
    for model_name in models_to_test:
        full_model_name = f"models/{model_name}"
        model_exists = any(m.name == full_model_name for m in all_models)
        if model_exists:
            model = next(m for m in all_models if m.name == full_model_name)
            if 'generateContent' in model.supported_generation_methods:
                working_models.append(model_name)
    
    if working_models:
        print("✅ Use one of these models:")
        for model in working_models:
            print(f"   - {model}")
        print()
        print(f"💡 CHEAPEST: Look for 'flash-8b' or regular 'flash'")
        print(f"🎯 QUALITY: Look for 'pro'")
    else:
        print("❌ No working models found!")
        print("This shouldn't happen - check your API key")

except ImportError:
    print("❌ ERROR: google-generativeai not installed")
    print("Run: pip install google-generativeai")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

