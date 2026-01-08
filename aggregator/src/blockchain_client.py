"""
Blockchain Client for Aggregator
Interacts with blockchain API
"""

import requests
from loguru import logger
from typing import Dict, List, Optional


class BlockchainClient:
    """Client for interacting with blockchain API"""
    
    def __init__(self, blockchain_url: str = "http://localhost:7050"):
        self.blockchain_url = blockchain_url
        logger.info(f"Blockchain client initialized: {blockchain_url}")
    
    def log_transaction(self, transaction_data: Dict) -> str:
        """
        Log a transaction to the blockchain
        
        Args:
            transaction_data: Transaction data including type and details
            
        Returns:
            Transaction hash
        """
        try:
            response = requests.post(
                f"{self.blockchain_url}/api/blockchain/transaction",
                json={
                    "type": transaction_data.get('type', 'UNKNOWN'),
                    "data": transaction_data
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                tx_hash = result.get('transaction_hash', '')
                logger.info(f"Transaction logged: {tx_hash[:16]}...")
                return tx_hash
            else:
                logger.error(f"Transaction logging failed: {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Blockchain client error: {e}")
            return ""
    
    def get_chain(self) -> List[Dict]:
        """Get the entire blockchain"""
        try:
            response = requests.get(
                f"{self.blockchain_url}/api/blockchain/chain",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get('chain', [])
            return []
            
        except Exception as e:
            logger.error(f"Get chain error: {e}")
            return []
    
    def get_hospital_rewards(self, hospital_id: str) -> float:
        """Get total rewards for a hospital"""
        try:
            response = requests.get(
                f"{self.blockchain_url}/api/blockchain/hospital/{hospital_id}/rewards",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get('total_rewards', 0.0)
            return 0.0
            
        except Exception as e:
            logger.error(f"Get rewards error: {e}")
            return 0.0
    
    def get_leaderboard(self) -> List[Dict]:
        """Get hospital leaderboard"""
        try:
            response = requests.get(
                f"{self.blockchain_url}/api/blockchain/leaderboard",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get('leaderboard', [])
            return []
            
        except Exception as e:
            logger.error(f"Get leaderboard error: {e}")
            return []
    
    def get_training_summary(self) -> Dict:
        """Get training summary"""
        try:
            response = requests.get(
                f"{self.blockchain_url}/api/blockchain/training/summary",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            logger.error(f"Get training summary error: {e}")
            return {}
    
    def validate_chain(self) -> bool:
        """Validate blockchain integrity"""
        try:
            response = requests.get(
                f"{self.blockchain_url}/api/blockchain/validate",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get('is_valid', False)
            return False
            
        except Exception as e:
            logger.error(f"Validate chain error: {e}")
            return False


if __name__ == "__main__":
    # Test client
    client = BlockchainClient()
    
    # Log a test transaction
    tx_hash = client.log_transaction({
        'type': 'TEST',
        'message': 'Test transaction',
        'value': 123
    })
    
    print(f"Transaction hash: {tx_hash}")
    
    # Validate chain
    is_valid = client.validate_chain()
    print(f"Chain valid: {is_valid}")
