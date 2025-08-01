#!/usr/bin/env python3
"""Test script to check available Gemini models"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Load API key from environment
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ GEMINI_API_KEY not found in environment variables")
    exit(1)

# Test different model names
models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro", 
    "gemini-1.0-pro",
    "gemini-2.0-flash",
    "gemini-2.5-flash"
]

print("Testing Gemini models...\n")

for model in models_to_test:
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=0.1
        )
        
        # Test with a simple prompt
        response = llm.invoke("Hello, can you respond with just 'OK'?")
        print(f"✅ {model}: Working - Response: {response.content}")
        
    except Exception as e:
        print(f"❌ {model}: Error - {str(e)}")

print("\n🔍 Use one of the working models in your graph.py file.") 