#!/usr/bin/env python3
"""
Simple script to run the UCP business server.
"""
import uvicorn
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import sys
    print("🚀 Starting UCP Business Server...")
    print(f"🐍 Using Python: {sys.executable}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print("📍 Server will be available at: http://localhost:8000")
    print("🌐 Web UI will be available at: http://localhost:8000/demo")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

