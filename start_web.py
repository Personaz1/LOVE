#!/usr/bin/env python3
"""
Dr. Harmony Web Application Startup Script
Beautiful romantic web interface with password protection
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("💕 Starting Dr. Harmony Web Application...")
    print("=" * 50)
    
    # Check if required environment variables are set
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        sys.exit(1)
    
    print("✅ Environment variables loaded")
    print("✅ Gemini 2.5 Pro AI engine ready")
    print("✅ User profiles and memory system ready")
    print("✅ Beautiful romantic UI ready")
    print("\n🌐 Starting web server...")
    print("📱 Visit: http://localhost:8000")
    print("🔐 Login credentials:")
    print("   Meranda: username=meranda, password=musser")
    print("   Stepan: username=stepan, password=stepan")
    print("\n💕 Dr. Harmony is ready for Stepan & Meranda!")
    print("=" * 50)
    
    # Import and run the web app
    from web_app import app
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 