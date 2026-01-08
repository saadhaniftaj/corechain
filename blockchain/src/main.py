"""
Blockchain Service Main Entry Point
"""

from fabric_api import start_server
from loguru import logger
import os


if __name__ == "__main__":
    logger.info("=== CoreChain Blockchain Service ===")
    
    port = int(os.getenv('BLOCKCHAIN_PORT', 7050))
    difficulty = int(os.getenv('DIFFICULTY', 4))
    
    logger.info(f"Configuration: port={port}, difficulty={difficulty}")
    
    start_server(port)
