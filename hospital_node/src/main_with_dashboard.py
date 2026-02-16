"""
Hospital Node Main Entry Point with Dashboard
Runs both the FL client and the dashboard API
"""

import os
import sys
import threading
from loguru import logger

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dashboard_api import app
import uvicorn


def start_dashboard_server():
    """Start the dashboard API server in a separate thread"""
    logger.info("Starting dashboard server on port 3000...")
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("CoreChain Hospital Node with Dashboard Starting")
    logger.info("=" * 60)
    
    # Start dashboard in background thread
    dashboard_thread = threading.Thread(target=start_dashboard_server, daemon=True)
    dashboard_thread.start()
    logger.success("Dashboard server started on http://localhost:3000")
    
    # Import and run the original hospital node main
    # Use relative import since we're in the same package
    import main as hospital_main
    
    try:
        hospital_main.main()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("=" * 60)
    logger.info("Hospital Node Shutting Down")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
