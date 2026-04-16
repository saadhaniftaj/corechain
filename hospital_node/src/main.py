"""
Hospital Node Main Entry Point
Runs Flower client and communicates with aggregator
"""

import os
import sys
from loguru import logger
import time

# Add parent directory
sys.path.insert(0, '/app')
sys.path.insert(0, os.path.dirname(__file__))

from fl_trainer import create_flower_client
from grpc_client import AggregatorClient
import flwr as fl


def wait_for_aggregator(host: str, port: int, timeout: int = 60) -> bool:
    """Wait for aggregator Flower port to accept connections"""
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except (ConnectionRefusedError, OSError, socket.timeout):
            logger.info(f"Waiting for aggregator at {host}:{port}...")
            time.sleep(3)
    return False


def main():
    """Main entry point for hospital node"""
    
    logger.info("=" * 60)
    logger.info("CoreChain Hospital Node Starting")
    logger.info("=" * 60)
    
    # Get configuration from environment
    hospital_id = os.getenv('HOSPITAL_ID', 'hospital_1')
    hospital_name = os.getenv('HOSPITAL_NAME', 'General Hospital 1')
    aggregator_ip = os.getenv('AGGREGATOR_IP', 'localhost')
    aggregator_port = int(os.getenv('AGGREGATOR_PORT', 50051))
    flower_port = int(os.getenv('FLOWER_PORT', 8080))
    dataset_path = os.getenv('DATASET_PATH', '/data')
    dataset_type = os.getenv('DATASET_TYPE', 'shenzhen')
    
    logger.info(f"Hospital ID: {hospital_id}")
    logger.info(f"Hospital Name: {hospital_name}")
    logger.info(f"Aggregator: {aggregator_ip}:{flower_port} (Flower)")
    logger.info(f"Dataset: {dataset_type} at {dataset_path}")
    
    # Wait for Flower server to be reachable
    flower_server_address = f"{aggregator_ip}:{flower_port}"
    
    # Try gRPC registration (optional — Flower handles its own connection)
    try:
        grpc_client = AggregatorClient(
            aggregator_ip=aggregator_ip,
            aggregator_port=aggregator_port,
            hospital_id=hospital_id
        )
        if grpc_client.connect():
            logger.success("gRPC channel established")
            grpc_client.register(
                hospital_name=hospital_name,
                dataset_size=1000,
                dataset_type=dataset_type
            )
        else:
            logger.warning("gRPC connection failed — continuing with Flower only")
            grpc_client = None
    except Exception as e:
        logger.warning(f"gRPC setup skipped: {e}")
        grpc_client = None
    
    # Create Flower client
    logger.info("Creating Flower client...")
    flower_client = create_flower_client(
        hospital_id=hospital_id,
        dataset_path=dataset_path,
        dataset_type=dataset_type
    )
    
    # Connect to Flower server with retry loop
    while True:
        try:
            logger.info(f"Connecting to Flower server at {flower_server_address}...")
            fl.client.start_numpy_client(
                server_address=flower_server_address,
                client=flower_client
            )
            logger.success("Flower round complete")
            break
        except Exception as e:
            logger.warning(f"Flower server not ready yet: {e} — retrying in 5 seconds...")
            time.sleep(5)
            import traceback
            traceback.print_exc()
    
    finally:
        if grpc_client:
            grpc_client.close()
    
    logger.info("=" * 60)
    logger.info("Hospital Node Shutting Down")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
