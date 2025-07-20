#!/usr/bin/env python3
"""
Setup script for AI Trends Reporter
Checks environment variables and dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

def check_env_variables():
    """Check if required environment variables are set"""
    required_vars = [
        "GEMINI_API_KEY",
        "GOOGLE_SEARCH_API_KEY", 
        "GOOGLE_SEARCH_ENGINE_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with:")
        for var in missing_vars:
            print(f"   {var}=your_{var.lower()}_here")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    try:
        import langchain_google_genai
        import langgraph
        import fastapi
        print("✅ Core dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_output_dir():
    """Ensure output directory exists"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"✅ Output directory ready: {output_dir.absolute()}")

def main():
    """Run setup checks"""
    print("🔧 AI Trends Reporter Setup Check")
    print("=" * 40)
    
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Loaded .env file")
        except ImportError:
            print("ℹ️  .env file exists but python-dotenv not installed")
            print("   Install with: pip install python-dotenv")
    else:
        print("⚠️  No .env file found")
    
    all_good = True
    
    # Check environment variables
    if not check_env_variables():
        all_good = False
    
    print()
    
    # Check dependencies  
    if not check_dependencies():
        all_good = False
    
    print()
    
    # Check output directory
    check_output_dir()
    
    print()
    
    if all_good:
        print("🎉 Setup complete! Ready to generate reports.")
        print("Run: python run_report.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 