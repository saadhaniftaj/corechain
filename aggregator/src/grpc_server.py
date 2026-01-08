"""
gRPC Server for CoreChain Aggregator
Handles model updates from hospital nodes
"""

import grpc
from concurrent import futures
import sys
import os

# Add proto path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from loguru import logger
from typing import Dict, List
import numpy as np
import asyncio
import json
from datetime import datetime

# Import generated protobuf code (will be generated)
try:
    from shared import corechain_pb2, corechain_pb2_grpc
except ImportError:
    logger.warning("Protobuf files not generated yet. Run: python -m grpc_tools.protoc -I.proto --python_out=./shared --grpc_python_out=./shared .proto/corechain.proto")
    corechain_pb2 = None
    corechain_pb2_grpc = None

from shared.encryption import EncryptionManager


class ModelAggregationServicer:
    """gRPC servicer for model aggregation"""
    
    def __init__(self, blockchain_client, websocket_server):
        self.blockchain_client = blockchain_client
        self.websocket_server = websocket_server
        self.encryption_manager = EncryptionManager()
        
        # Generate encryption keys
        self.public_key_str, self.private_key_str = self.encryption_manager.generate_keypair()
        
        # State management
        self.current_round = 0
        self.registered_hospitals: Dict[str, dict] = {}
        self.round_updates: Dict[int, List[dict]] = {}
        self.global_model_weights = None
        self.global_metrics = {
            'accuracy': 0.0,
            'loss': 0.0,
            'total_samples': 0
        }
        
        logger.info("ModelAggregationServicer initialized")
    
    def RegisterHospital(self, request, context):
        """Register a new hospital node"""
        hospital_id = request.hospital_id
        
        logger.info(f"Registering hospital: {hospital_id}")
        
        # Store hospital info
        self.registered_hospitals[hospital_id] = {
            'hospital_id': hospital_id,
            'hospital_name': request.hospital_name,
            'dataset_size': request.dataset_size,
            'dataset_type': request.dataset_type,
            'registered_at': datetime.now().isoformat()
        }
        
        # Log to blockchain
        self.blockchain_client.log_transaction({
            'type': 'HOSPITAL_REGISTRATION',
            'hospital_id': hospital_id,
            'hospital_name': request.hospital_name,
            'dataset_size': request.dataset_size,
            'timestamp': datetime.now().isoformat()
        })
        
        # Broadcast to dashboard
        asyncio.create_task(self.websocket_server.broadcast({
            'event': 'hospital_registered',
            'data': self.registered_hospitals[hospital_id]
        }))
        
        logger.success(f"Hospital {hospital_id} registered successfully")
        
        if corechain_pb2:
            return corechain_pb2.RegistrationResponse(
                success=True,
                message=f"Hospital {hospital_id} registered successfully",
                public_key=self.public_key_str
            )
        else:
            return None
    
    def SubmitUpdate(self, request, context):
        """Receive model update from hospital"""
        hospital_id = request.hospital_id
        round_number = request.round_number
        
        logger.info(f"Received update from {hospital_id} for round {round_number}")
        
        # Decrypt weights
        try:
            decrypted_weights = self.encryption_manager.decrypt_weights(request.encrypted_weights)
            logger.success(f"Decrypted weights from {hospital_id}")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            if corechain_pb2:
                return corechain_pb2.AggregationResponse(
                    success=False,
                    message=f"Decryption failed: {str(e)}",
                    current_round=self.current_round,
                    total_participants=0,
                    transaction_hash=""
                )
            return None
        
        # Store update
        if round_number not in self.round_updates:
            self.round_updates[round_number] = []
        
        self.round_updates[round_number].append({
            'hospital_id': hospital_id,
            'weights': decrypted_weights,
            'samples_trained': request.samples_trained,
            'local_accuracy': request.local_accuracy,
            'local_loss': request.local_loss,
            'timestamp': request.timestamp
        })
        
        # Log to blockchain
        tx_hash = self.blockchain_client.log_transaction({
            'type': 'MODEL_UPDATE',
            'hospital_id': hospital_id,
            'round': round_number,
            'accuracy': request.local_accuracy,
            'loss': request.local_loss,
            'samples_trained': request.samples_trained,
            'timestamp': request.timestamp
        })
        
        # Broadcast to dashboard
        asyncio.create_task(self.websocket_server.broadcast({
            'event': 'hospital_update_received',
            'data': {
                'hospital_id': hospital_id,
                'round': round_number,
                'accuracy': request.local_accuracy,
                'samples_trained': request.samples_trained
            }
        }))
        
        # Check if we have all updates for this round
        num_participants = len(self.round_updates[round_number])
        min_clients = int(os.getenv('MIN_CLIENTS', 2))
        
        if num_participants >= min_clients:
            # Trigger aggregation
            self._aggregate_round(round_number)
        
        logger.success(f"Update from {hospital_id} processed ({num_participants}/{min_clients} received)")
        
        if corechain_pb2:
            return corechain_pb2.AggregationResponse(
                success=True,
                message="Update received successfully",
                current_round=self.current_round,
                total_participants=num_participants,
                transaction_hash=tx_hash
            )
        return None
    
    def GetGlobalModel(self, request, context):
        """Return current global model to hospital"""
        hospital_id = request.hospital_id
        
        logger.info(f"Hospital {hospital_id} requesting global model")
        
        if self.global_model_weights is None:
            logger.warning("No global model available yet")
            if corechain_pb2:
                return corechain_pb2.GlobalModel(
                    round_number=0,
                    model_weights=b'',
                    global_accuracy=0.0,
                    global_loss=0.0,
                    total_samples=0,
                    timestamp=datetime.now().isoformat()
                )
            return None
        
        # Serialize weights
        import pickle
        weights_bytes = pickle.dumps(self.global_model_weights)
        
        if corechain_pb2:
            return corechain_pb2.GlobalModel(
                round_number=self.current_round,
                model_weights=weights_bytes,
                global_accuracy=self.global_metrics['accuracy'],
                global_loss=self.global_metrics['loss'],
                total_samples=self.global_metrics['total_samples'],
                timestamp=datetime.now().isoformat()
            )
        return None
    
    def GetTrainingStatus(self, request, context):
        """Return current training status"""
        total_rounds = int(os.getenv('FL_ROUNDS', 10))
        
        if corechain_pb2:
            return corechain_pb2.TrainingStatus(
                current_round=self.current_round,
                total_rounds=total_rounds,
                connected_hospitals=len(self.registered_hospitals),
                global_accuracy=self.global_metrics['accuracy'],
                global_loss=self.global_metrics['loss'],
                is_training=self.current_round < total_rounds,
                next_round_eta="2 minutes"
            )
        return None
    
    def _aggregate_round(self, round_number: int):
        """Aggregate model updates for a round"""
        logger.info(f"Aggregating round {round_number}...")
        
        updates = self.round_updates[round_number]
        
        # Weighted average based on dataset size
        total_samples = sum(u['samples_trained'] for u in updates)
        
        # Aggregate weights
        aggregated_weights = []
        num_layers = len(updates[0]['weights'])
        
        for layer_idx in range(num_layers):
            # Weighted sum
            weighted_sum = None
            for update in updates:
                weight = update['weights'][layer_idx]
                contribution = weight * (update['samples_trained'] / total_samples)
                
                if weighted_sum is None:
                    weighted_sum = contribution
                else:
                    weighted_sum += contribution
            
            aggregated_weights.append(weighted_sum)
        
        self.global_model_weights = aggregated_weights
        
        # Calculate global metrics
        self.global_metrics['accuracy'] = sum(
            u['local_accuracy'] * u['samples_trained'] for u in updates
        ) / total_samples
        
        self.global_metrics['loss'] = sum(
            u['local_loss'] * u['samples_trained'] for u in updates
        ) / total_samples
        
        self.global_metrics['total_samples'] = total_samples
        
        # Update round
        self.current_round = round_number
        
        # Log to blockchain
        self.blockchain_client.log_transaction({
            'type': 'MODEL_AGGREGATION',
            'round': round_number,
            'global_accuracy': self.global_metrics['accuracy'],
            'global_loss': self.global_metrics['loss'],
            'participants': len(updates),
            'total_samples': total_samples,
            'timestamp': datetime.now().isoformat()
        })
        
        # Calculate and distribute rewards
        self._distribute_rewards(round_number, updates)
        
        # Broadcast to dashboard
        asyncio.create_task(self.websocket_server.broadcast({
            'event': 'model_aggregated',
            'data': {
                'round': round_number,
                'accuracy': self.global_metrics['accuracy'],
                'loss': self.global_metrics['loss'],
                'participants': len(updates)
            }
        }))
        
        logger.success(f"Round {round_number} aggregated: accuracy={self.global_metrics['accuracy']:.4f}")
    
    def _distribute_rewards(self, round_number: int, updates: List[dict]):
        """Calculate and distribute token rewards"""
        base_reward = 10
        
        for update in updates:
            # Reward formula: base + accuracy bonus + sample contribution
            accuracy_bonus = update['local_accuracy'] * 5
            sample_weight = (update['samples_trained'] / self.global_metrics['total_samples']) * 5
            
            total_reward = base_reward + accuracy_bonus + sample_weight
            
            # Log reward to blockchain
            self.blockchain_client.log_transaction({
                'type': 'REWARD_DISTRIBUTION',
                'hospital_id': update['hospital_id'],
                'round': round_number,
                'reward_tokens': total_reward,
                'accuracy': update['local_accuracy'],
                'samples_contributed': update['samples_trained'],
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Rewarded {update['hospital_id']}: {total_reward:.2f} tokens")


def serve(port: int = 50051):
    """Start gRPC server"""
    if corechain_pb2_grpc is None:
        logger.error("Protobuf files not generated. Cannot start server.")
        return
    
    # Import dependencies (will be implemented)
    from blockchain_client import BlockchainClient
    from websocket_server import WebSocketServer
    
    blockchain_client = BlockchainClient()
    websocket_server = WebSocketServer()
    
    servicer = ModelAggregationServicer(blockchain_client, websocket_server)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    corechain_pb2_grpc.add_ModelAggregationServicer_to_server(servicer, server)
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"gRPC server starting on port {port}...")
    server.start()
    logger.success(f"gRPC server running on port {port}")
    
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
