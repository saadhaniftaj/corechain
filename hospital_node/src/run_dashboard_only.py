"""
Standalone Hospital Dashboard Server
Runs only the dashboard API without the FL client for testing
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dashboard_api import app
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Hospital Dashboard (Standalone Mode)")
    print("Dashboard will be available at: http://localhost:3000")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
