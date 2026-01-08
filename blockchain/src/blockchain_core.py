"""
Lightweight Blockchain Core for CoreChain
Provides immutable audit trail for federated learning
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import os


class Block:
    """Individual block in the blockchain"""
    
    def __init__(
        self,
        index: int,
        timestamp: str,
        transactions: List[Dict],
        previous_hash: str,
        nonce: int = 0
    ):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int):
        """Mine block with proof-of-work"""
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        logger.info(f"Block mined: {self.hash[:16]}... (nonce: {self.nonce})")
    
    def to_dict(self) -> Dict:
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class Blockchain:
    """Blockchain for audit trail"""
    
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.difficulty = difficulty
        self.mining_reward = 1.0
        
        # Create genesis block
        self._create_genesis_block()
        
        logger.info(f"Blockchain initialized with difficulty {difficulty}")
    
    def _create_genesis_block(self):
        """Create the first block"""
        genesis_block = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            transactions=[{
                'type': 'GENESIS',
                'message': 'CoreChain Genesis Block',
                'timestamp': datetime.now().isoformat()
            }],
            previous_hash='0'
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        
        logger.success("Genesis block created")
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict) -> str:
        """Add transaction to pending pool"""
        # Add timestamp if not present
        if 'timestamp' not in transaction:
            transaction['timestamp'] = datetime.now().isoformat()
        
        self.pending_transactions.append(transaction)
        
        # Auto-mine if we have enough transactions
        if len(self.pending_transactions) >= 5:
            self.mine_pending_transactions()
        
        # Return transaction hash
        tx_hash = hashlib.sha256(
            json.dumps(transaction, sort_keys=True).encode()
        ).hexdigest()
        
        return tx_hash
    
    def mine_pending_transactions(self):
        """Mine a new block with pending transactions"""
        if not self.pending_transactions:
            logger.warning("No pending transactions to mine")
            return
        
        logger.info(f"Mining block with {len(self.pending_transactions)} transactions...")
        
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        
        logger.success(
            f"Block {new_block.index} mined: {new_block.hash[:16]}... "
            f"({len(new_block.transactions)} transactions)"
        )
        
        # Clear pending transactions
        self.pending_transactions = []
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check hash integrity
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Block {i} has invalid hash")
                return False
            
            # Check chain linkage
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Block {i} has invalid previous_hash")
                return False
            
            # Check proof-of-work
            if not current_block.hash.startswith('0' * self.difficulty):
                logger.error(f"Block {i} has invalid proof-of-work")
                return False
        
        return True
    
    def get_chain(self) -> List[Dict]:
        """Get entire chain as list of dictionaries"""
        return [block.to_dict() for block in self.chain]
    
    def get_block(self, index: int) -> Optional[Dict]:
        """Get specific block by index"""
        if 0 <= index < len(self.chain):
            return self.chain[index].to_dict()
        return None
    
    def get_transactions_by_type(self, tx_type: str) -> List[Dict]:
        """Get all transactions of a specific type"""
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('type') == tx_type:
                    transactions.append({
                        **tx,
                        'block_index': block.index,
                        'block_hash': block.hash
                    })
        return transactions
    
    def get_transactions_by_hospital(self, hospital_id: str) -> List[Dict]:
        """Get all transactions for a specific hospital"""
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('hospital_id') == hospital_id:
                    transactions.append({
                        **tx,
                        'block_index': block.index,
                        'block_hash': block.hash
                    })
        return transactions
    
    def get_hospital_rewards(self, hospital_id: str) -> float:
        """Calculate total rewards for a hospital"""
        reward_txs = [
            tx for tx in self.get_transactions_by_hospital(hospital_id)
            if tx.get('type') == 'REWARD_DISTRIBUTION'
        ]
        
        total_rewards = sum(tx.get('reward_tokens', 0) for tx in reward_txs)
        return total_rewards
    
    def get_stats(self) -> Dict:
        """Get blockchain statistics"""
        total_blocks = len(self.chain)
        total_transactions = sum(len(block.transactions) for block in self.chain)
        
        # Count transaction types
        tx_types = {}
        for block in self.chain:
            for tx in block.transactions:
                tx_type = tx.get('type', 'UNKNOWN')
                tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
        
        return {
            'total_blocks': total_blocks,
            'total_transactions': total_transactions,
            'pending_transactions': len(self.pending_transactions),
            'difficulty': self.difficulty,
            'is_valid': self.is_chain_valid(),
            'transaction_types': tx_types,
            'latest_block_hash': self.get_latest_block().hash
        }
    
    def save_to_file(self, filepath: str):
        """Save blockchain to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_chain(), f, indent=2)
        logger.info(f"Blockchain saved to {filepath}")
    
    def load_from_file(self, filepath: str):
        """Load blockchain from JSON file"""
        if not os.path.exists(filepath):
            logger.warning(f"File {filepath} not found")
            return
        
        with open(filepath, 'r') as f:
            chain_data = json.load(f)
        
        self.chain = []
        for block_data in chain_data:
            block = Block(
                index=block_data['index'],
                timestamp=block_data['timestamp'],
                transactions=block_data['transactions'],
                previous_hash=block_data['previous_hash'],
                nonce=block_data['nonce']
            )
            block.hash = block_data['hash']
            self.chain.append(block)
        
        logger.success(f"Blockchain loaded from {filepath} ({len(self.chain)} blocks)")


# Demo
if __name__ == "__main__":
    logger.info("=== Blockchain Demo ===")
    
    # Create blockchain
    bc = Blockchain(difficulty=4)
    
    # Add some transactions
    bc.add_transaction({
        'type': 'HOSPITAL_REGISTRATION',
        'hospital_id': 'hospital_1',
        'hospital_name': 'General Hospital',
        'dataset_size': 1500
    })
    
    bc.add_transaction({
        'type': 'MODEL_UPDATE',
        'hospital_id': 'hospital_1',
        'round': 1,
        'accuracy': 0.85,
        'samples_trained': 1500
    })
    
    bc.add_transaction({
        'type': 'REWARD_DISTRIBUTION',
        'hospital_id': 'hospital_1',
        'round': 1,
        'reward_tokens': 15.5
    })
    
    # Mine pending
    bc.mine_pending_transactions()
    
    # Validate
    logger.info(f"Chain valid: {bc.is_chain_valid()}")
    
    # Stats
    stats = bc.get_stats()
    logger.info(f"Stats: {json.dumps(stats, indent=2)}")
    
    # Hospital rewards
    rewards = bc.get_hospital_rewards('hospital_1')
    logger.info(f"Hospital 1 total rewards: {rewards} tokens")
