"""
Smart Contracts for CoreChain
Implements validation and reward distribution logic
"""

from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime


class SmartContract:
    """Base class for smart contracts"""
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
    
    def execute(self, *args, **kwargs):
        """Execute contract logic"""
        raise NotImplementedError


class ModelUpdateValidator(SmartContract):
    """Validates model updates from hospitals"""
    
    def execute(self, update_data: Dict) -> tuple[bool, str]:
        """
        Validate a model update
        
        Args:
            update_data: Dictionary containing update information
            
        Returns:
            Tuple of (is_valid, message)
        """
        logger.info(f"Validating update from {update_data.get('hospital_id')}")
        
        # Check required fields
        required_fields = ['hospital_id', 'round', 'accuracy', 'samples_trained']
        for field in required_fields:
            if field not in update_data:
                return False, f"Missing required field: {field}"
        
        # Validate hospital is registered
        hospital_id = update_data['hospital_id']
        registrations = self.blockchain.get_transactions_by_type('HOSPITAL_REGISTRATION')
        
        if not any(reg['hospital_id'] == hospital_id for reg in registrations):
            return False, f"Hospital {hospital_id} not registered"
        
        # Validate accuracy range
        accuracy = update_data['accuracy']
        if not (0.0 <= accuracy <= 1.0):
            return False, f"Invalid accuracy: {accuracy} (must be 0-1)"
        
        # Validate samples count
        samples = update_data['samples_trained']
        if samples <= 0:
            return False, f"Invalid samples count: {samples}"
        
        # Check for duplicate submissions in same round
        round_num = update_data['round']
        existing_updates = [
            tx for tx in self.blockchain.get_transactions_by_hospital(hospital_id)
            if tx.get('type') == 'MODEL_UPDATE' and tx.get('round') == round_num
        ]
        
        if existing_updates:
            return False, f"Hospital {hospital_id} already submitted update for round {round_num}"
        
        logger.success(f"Update from {hospital_id} validated successfully")
        return True, "Validation successful"


class RewardDistributor(SmartContract):
    """Calculates and distributes token rewards"""
    
    def __init__(self, blockchain, base_reward: float = 10.0):
        super().__init__(blockchain)
        self.base_reward = base_reward
    
    def execute(
        self,
        hospital_id: str,
        round_num: int,
        accuracy: float,
        samples_contributed: int,
        total_samples: int
    ) -> float:
        """
        Calculate reward for a hospital's contribution
        
        Args:
            hospital_id: Hospital identifier
            round_num: Training round number
            accuracy: Local model accuracy
            samples_contributed: Number of samples trained
            total_samples: Total samples across all hospitals
            
        Returns:
            Reward amount in tokens
        """
        logger.info(f"Calculating reward for {hospital_id} (round {round_num})")
        
        # Base reward for participation
        reward = self.base_reward
        
        # Accuracy bonus (0-5 tokens based on accuracy)
        accuracy_bonus = accuracy * 5.0
        reward += accuracy_bonus
        
        # Sample contribution bonus (0-5 tokens based on proportion)
        if total_samples > 0:
            contribution_ratio = samples_contributed / total_samples
            sample_bonus = contribution_ratio * 5.0
            reward += sample_bonus
        
        # Quality multiplier (if accuracy > 0.9, give 1.2x multiplier)
        if accuracy > 0.9:
            reward *= 1.2
        
        logger.success(
            f"Reward calculated for {hospital_id}: {reward:.2f} tokens "
            f"(base: {self.base_reward}, accuracy: {accuracy_bonus:.2f}, "
            f"samples: {sample_bonus:.2f})"
        )
        
        return round(reward, 2)
    
    def get_leaderboard(self) -> List[Dict]:
        """Get hospital leaderboard by total rewards"""
        # Get all reward transactions
        reward_txs = self.blockchain.get_transactions_by_type('REWARD_DISTRIBUTION')
        
        # Aggregate by hospital
        hospital_rewards = {}
        for tx in reward_txs:
            hospital_id = tx.get('hospital_id')
            reward = tx.get('reward_tokens', 0)
            
            if hospital_id not in hospital_rewards:
                hospital_rewards[hospital_id] = {
                    'hospital_id': hospital_id,
                    'total_rewards': 0,
                    'rounds_participated': 0,
                    'total_accuracy': 0,
                    'total_samples': 0
                }
            
            hospital_rewards[hospital_id]['total_rewards'] += reward
            hospital_rewards[hospital_id]['rounds_participated'] += 1
            hospital_rewards[hospital_id]['total_accuracy'] += tx.get('accuracy', 0)
            hospital_rewards[hospital_id]['total_samples'] += tx.get('samples_contributed', 0)
        
        # Calculate averages
        for hospital_id, data in hospital_rewards.items():
            rounds = data['rounds_participated']
            if rounds > 0:
                data['avg_accuracy'] = data['total_accuracy'] / rounds
                data['avg_reward_per_round'] = data['total_rewards'] / rounds
        
        # Sort by total rewards
        leaderboard = sorted(
            hospital_rewards.values(),
            key=lambda x: x['total_rewards'],
            reverse=True
        )
        
        return leaderboard


class AuditLogger(SmartContract):
    """Logs and queries audit trail"""
    
    def execute(self, event_type: str, event_data: Dict) -> str:
        """
        Log an audit event to blockchain
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Transaction hash
        """
        transaction = {
            'type': event_type,
            **event_data,
            'timestamp': datetime.now().isoformat()
        }
        
        tx_hash = self.blockchain.add_transaction(transaction)
        logger.info(f"Audit event logged: {event_type} (TX: {tx_hash[:16]}...)")
        
        return tx_hash
    
    def get_audit_trail(
        self,
        hospital_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query audit trail
        
        Args:
            hospital_id: Filter by hospital (optional)
            event_type: Filter by event type (optional)
            limit: Maximum number of results
            
        Returns:
            List of audit events
        """
        # Get all transactions
        all_txs = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                all_txs.append({
                    **tx,
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'block_timestamp': block.timestamp
                })
        
        # Apply filters
        filtered_txs = all_txs
        
        if hospital_id:
            filtered_txs = [
                tx for tx in filtered_txs
                if tx.get('hospital_id') == hospital_id
            ]
        
        if event_type:
            filtered_txs = [
                tx for tx in filtered_txs
                if tx.get('type') == event_type
            ]
        
        # Sort by timestamp (newest first)
        filtered_txs.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Apply limit
        return filtered_txs[:limit]
    
    def get_training_summary(self) -> Dict:
        """Get summary of training activity"""
        model_updates = self.blockchain.get_transactions_by_type('MODEL_UPDATE')
        aggregations = self.blockchain.get_transactions_by_type('MODEL_AGGREGATION')
        
        if not model_updates:
            return {
                'total_rounds': 0,
                'total_updates': 0,
                'participating_hospitals': 0,
                'avg_accuracy': 0.0,
                'best_accuracy': 0.0
            }
        
        # Calculate metrics
        unique_hospitals = set(tx['hospital_id'] for tx in model_updates)
        accuracies = [tx['accuracy'] for tx in model_updates if 'accuracy' in tx]
        
        # Get latest aggregation
        latest_aggregation = aggregations[-1] if aggregations else {}
        
        return {
            'total_rounds': len(aggregations),
            'total_updates': len(model_updates),
            'participating_hospitals': len(unique_hospitals),
            'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0.0,
            'best_accuracy': max(accuracies) if accuracies else 0.0,
            'latest_global_accuracy': latest_aggregation.get('global_accuracy', 0.0),
            'latest_round': latest_aggregation.get('round', 0)
        }


# Demo
if __name__ == "__main__":
    from blockchain_core import Blockchain
    
    logger.info("=== Smart Contracts Demo ===")
    
    # Create blockchain
    bc = Blockchain(difficulty=2)
    
    # Create contracts
    validator = ModelUpdateValidator(bc)
    reward_dist = RewardDistributor(bc)
    audit_logger = AuditLogger(bc)
    
    # Register hospital
    audit_logger.execute('HOSPITAL_REGISTRATION', {
        'hospital_id': 'hospital_1',
        'hospital_name': 'General Hospital',
        'dataset_size': 1500
    })
    
    # Validate and log update
    update_data = {
        'hospital_id': 'hospital_1',
        'round': 1,
        'accuracy': 0.87,
        'samples_trained': 1500
    }
    
    is_valid, message = validator.execute(update_data)
    logger.info(f"Validation result: {is_valid} - {message}")
    
    if is_valid:
        audit_logger.execute('MODEL_UPDATE', update_data)
        
        # Calculate reward
        reward = reward_dist.execute(
            hospital_id='hospital_1',
            round_num=1,
            accuracy=0.87,
            samples_contributed=1500,
            total_samples=3000
        )
        
        audit_logger.execute('REWARD_DISTRIBUTION', {
            'hospital_id': 'hospital_1',
            'round': 1,
            'reward_tokens': reward,
            'accuracy': 0.87,
            'samples_contributed': 1500
        })
    
    # Mine pending
    bc.mine_pending_transactions()
    
    # Get training summary
    summary = audit_logger.get_training_summary()
    logger.info(f"Training summary: {summary}")
    
    # Get leaderboard
    leaderboard = reward_dist.get_leaderboard()
    logger.info(f"Leaderboard: {leaderboard}")
