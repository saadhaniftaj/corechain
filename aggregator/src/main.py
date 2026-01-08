"""
Aggregator Main Entry Point
Runs all aggregator services: Flower server, gRPC, REST API, WebSocket
"""

import os
import sys
from loguru import logger
import asyncio
import threading
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from flower_server import start_flower_server
from rest_api import start_api_server, training_state, registered_hospitals
from websocket_server import WebSocketServer
from blockchain_client import BlockchainClient


def run_flower_server(blockchain_client, websocket_server):
    """Run Flower server in separate thread"""
    logger.info("Starting Flower server thread...")
    
    min_clients = int(os.getenv('MIN_CLIENTS', 2))
    num_rounds = int(os.getenv('FL_ROUNDS', 10))
    
    try:
        start_flower_server(
            server_address="0.0.0.0:8080",
            min_clients=min_clients,
            num_rounds=num_rounds,
            blockchain_client=blockchain_client,
            websocket_server=websocket_server
        )
    except Exception as e:
        logger.error(f"Flower server error: {e}")
        import traceback
        traceback.print_exc()


def run_rest_api():
    """Run REST API in separate thread"""
    logger.info("Starting REST API thread...")
    
    port = int(os.getenv('REST_PORT', 8000))
    
    try:
        start_api_server(port)
    except Exception as e:
        logger.error(f"REST API error: {e}")
        import traceback
        traceback.print_exc()


async def run_websocket_server(websocket_server):
    """Run WebSocket server"""
    logger.info("Starting WebSocket server...")
    
    try:
        await websocket_server.start()
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for aggregator"""
    
    logger.info("=" * 60)
    logger.info("CoreChain Aggregator Starting")
    logger.info("=" * 60)
    
    # Get configuration
    grpc_port = int(os.getenv('GRPC_PORT', 50051))
    rest_port = int(os.getenv('REST_PORT', 8000))
    websocket_port = int(os.getenv('WEBSOCKET_PORT', 8001))
    blockchain_url = os.getenv('BLOCKCHAIN_URL', 'http://localhost:7050')
    min_clients = int(os.getenv('MIN_CLIENTS', 2))
    fl_rounds = int(os.getenv('FL_ROUNDS', 10))
    
    logger.info(f"Configuration:")
    logger.info(f"  - gRPC Port: {grpc_port}")
    logger.info(f"  - REST Port: {rest_port}")
    logger.info(f"  - WebSocket Port: {websocket_port}")
    logger.info(f"  - Blockchain URL: {blockchain_url}")
    logger.info(f"  - Min Clients: {min_clients}")
    logger.info(f"  - FL Rounds: {fl_rounds}")
    
    # Wait for blockchain to be ready
    logger.info("Waiting for blockchain service to be ready...")
    time.sleep(5)
    
    # Initialize blockchain client
    blockchain_client = BlockchainClient(blockchain_url)
    
    # Initialize WebSocket server
    websocket_server = WebSocketServer(websocket_port)
    
    # Start services in separate threads
    
    # 1. REST API
    rest_thread = threading.Thread(target=run_rest_api, daemon=True)
    rest_thread.start()
    logger.success(f"REST API started on port {rest_port}")
    
    # 2. Flower server
    flower_thread = threading.Thread(
        target=run_flower_server,
        args=(blockchain_client, websocket_server),
        daemon=True
    )
    flower_thread.start()
    logger.success(f"Flower server started on port 8080")
    
    # 3. WebSocket server (run in main thread with asyncio)
    logger.info("Starting WebSocket server in main thread...")
    
    try:
        asyncio.run(run_websocket_server(websocket_server))
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Main loop error: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("=" * 60)
    logger.info("CoreChain Aggregator Shutting Down")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
