"""
Hospital Node Main Entry Point
Runs Flower client and communicates with aggregator
"""

import os
import sys
from loguru import logger
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fl_trainer import create_flower_client
from grpc_client import AggregatorClient
import flwr as fl


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
    dataset_path = os.getenv('DATASET_PATH', '/data')
    dataset_type = os.getenv('DATASET_TYPE', 'shenzhen')
    
    logger.info(f"Hospital ID: {hospital_id}")
    logger.info(f"Hospital Name: {hospital_name}")
    logger.info(f"Aggregator: {aggregator_ip}:{aggregator_port}")
    logger.info(f"Dataset: {dataset_type} at {dataset_path}")
    
    # Wait a bit for aggregator to start
    logger.info("Waiting for aggregator to be ready...")
    time.sleep(10)
    
    # Create gRPC client
    grpc_client = AggregatorClient(
        aggregator_ip=aggregator_ip,
        aggregator_port=aggregator_port,
        hospital_id=hospital_id
    )
    
    # Connect to aggregator
    if not grpc_client.connect():
        logger.error("Failed to connect to aggregator. Exiting.")
        return
    
    # Register hospital
    # Note: For now, we'll use Flower's built-in registration
    # In production, you'd register via gRPC first
    
    # Create Flower client
    logger.info("Creating Flower client...")
    flower_client = create_flower_client(
        hospital_id=hospital_id,
        dataset_path=dataset_path,
        dataset_type=dataset_type
    )
    
    # Connect to Flower server
    flower_server_address = f"{aggregator_ip}:8080"
    logger.info(f"Connecting to Flower server at {flower_server_address}...")
    
    try:
        fl.client.start_numpy_client(
            server_address=flower_server_address,
            client=flower_client
        )
        
        logger.success("Federated learning completed successfully!")
        
    except Exception as e:
        logger.error(f"Flower client error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        grpc_client.close()
    
    logger.info("=" * 60)
    logger.info("Hospital Node Shutting Down")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
