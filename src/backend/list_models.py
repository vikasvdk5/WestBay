#!/usr/bin/env python3
"""
List all available Gemini models for your API key.
Run this to find valid model names.
"""

import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
import google.generativeai as genai

def list_available_models():
    """List all available Gemini models."""
    
    print("=" * 80)
    print("AVAILABLE GEMINI MODELS FOR YOUR API KEY")
    print("=" * 80)
    print()
    
    try:
        genai.configure(api_key=settings.gemini_api_key)
        
        models = genai.list_models()
        
        # Filter for models that support generateContent
        content_models = []
        
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                content_models.append(model)
        
        if not content_models:
            print("❌ No models found that support generateContent!")
            return
        
        print(f"✅ Found {len(content_models)} models that support content generation:\n")
        
        for i, model in enumerate(content_models, 1):
            model_name = model.name.replace('models/', '')
            
            print(f"{i}. {model_name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100]}...")
            print(f"   Input Token Limit: {model.input_token_limit:,}")
            print(f"   Output Token Limit: {model.output_token_limit:,}")
            
            # Show supported methods
            methods = ', '.join(model.supported_generation_methods)
            print(f"   Supported Methods: {methods}")
            print()
        
        print("=" * 80)
        print("HOW TO USE:")
        print("=" * 80)
        print()
        print("Update config.py with one of the model names above (without 'models/' prefix)")
        print()
        print("Example:")
        print('  gemini_model: str = "gemini-1.5-pro-002"')
        print()
        print("Or update .env file:")
        print('  GEMINI_MODEL=gemini-1.5-pro-002')
        print()
        
        # Recommend best model
        print("=" * 80)
        print("RECOMMENDED MODELS:")
        print("=" * 80)
        print()
        
        # Find Pro and Flash models
        pro_models = [m for m in content_models if 'pro' in m.name.lower()]
        flash_models = [m for m in content_models if 'flash' in m.name.lower()]
        
        if flash_models:
            flash_name = flash_models[0].name.replace('models/', '')
            print(f"⚡ For SPEED: {flash_name}")
            print("   - Faster response times")
            print("   - Good for development/testing")
            print()
        
        if pro_models:
            pro_name = pro_models[0].name.replace('models/', '')
            print(f"🎯 For QUALITY: {pro_name}")
            print("   - Better content quality")
            print("   - More accurate responses")
            print()
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        print()
        print("Make sure:")
        print("  1. Your GEMINI_API_KEY is set in .env")
        print("  2. The API key is valid")
        print("  3. You have internet connection")

if __name__ == "__main__":
    list_available_models()

