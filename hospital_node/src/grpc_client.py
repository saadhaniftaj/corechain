"""
gRPC Client for Hospital Nodes
Communicates with aggregator server
"""

import grpc
import sys
import os

# Add proto path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from loguru import logger
from typing import List
import numpy as np
from datetime import datetime

# Import generated protobuf code
try:
    from shared import corechain_pb2, corechain_pb2_grpc
except ImportError:
    logger.warning("Protobuf files not generated yet")
    corechain_pb2 = None
    corechain_pb2_grpc = None

from shared.encryption import EncryptionManager


class AggregatorClient:
    """Client for communicating with aggregator"""
    
    def __init__(self, aggregator_ip: str, aggregator_port: int, hospital_id: str):
        self.aggregator_ip = aggregator_ip
        self.aggregator_port = aggregator_port
        self.hospital_id = hospital_id
        self.channel = None
        self.stub = None
        self.encryption_manager = EncryptionManager()
        self.public_key_str = None
        
        logger.info(f"Initializing client for {hospital_id}")
    
    def connect(self):
        """Establish connection to aggregator"""
        address = f'{self.aggregator_ip}:{self.aggregator_port}'
        logger.info(f"Connecting to aggregator at {address}...")
        
        try:
            self.channel = grpc.insecure_channel(address)
            if corechain_pb2_grpc:
                self.stub = corechain_pb2_grpc.ModelAggregationStub(self.channel)
            logger.success(f"Connected to aggregator at {address}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def register(self, hospital_name: str, dataset_size: int, dataset_type: str):
        """Register hospital with aggregator"""
        if not corechain_pb2:
            logger.error("Protobuf not available")
            return False
        
        logger.info(f"Registering hospital {self.hospital_id}...")
        
        try:
            request = corechain_pb2.HospitalInfo(
                hospital_id=self.hospital_id,
                hospital_name=hospital_name,
                dataset_size=dataset_size,
                dataset_type=dataset_type
            )
            
            response = self.stub.RegisterHospital(request)
            
            if response.success:
                # Store public key for encryption
                self.public_key_str = response.public_key
                self.encryption_manager.set_public_key(self.public_key_str)
                
                logger.success(f"Registration successful: {response.message}")
                return True
            else:
                logger.error(f"Registration failed: {response.message}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def submit_update(
        self,
        round_number: int,
        model_weights: List[np.ndarray],
        samples_trained: int,
        local_accuracy: float,
        local_loss: float
    ) -> bool:
        """Submit model update to aggregator"""
        if not corechain_pb2:
            logger.error("Protobuf not available")
            return False
        
        logger.info(f"Submitting update for round {round_number}...")
        
        try:
            # Encrypt weights
            encrypted_weights = self.encryption_manager.encrypt_weights(model_weights)
            
            # Create request
            request = corechain_pb2.ModelUpdate(
                hospital_id=self.hospital_id,
                round_number=round_number,
                encrypted_weights=encrypted_weights,
                samples_trained=samples_trained,
                local_accuracy=local_accuracy,
                local_loss=local_loss,
                timestamp=datetime.now().isoformat()
            )
            
            # Send update
            response = self.stub.SubmitUpdate(request)
            
            if response.success:
                logger.success(
                    f"Update submitted: {response.message} "
                    f"(Round {response.current_round}, "
                    f"{response.total_participants} participants, "
                    f"TX: {response.transaction_hash[:16]}...)"
                )
                return True
            else:
                logger.error(f"Update failed: {response.message}")
                return False
                
        except Exception as e:
            logger.error(f"Submit update error: {e}")
            return False
    
    def get_global_model(self, round_number: int) -> List[np.ndarray]:
        """Retrieve global model from aggregator"""
        if not corechain_pb2:
            logger.error("Protobuf not available")
            return None
        
        logger.info(f"Requesting global model for round {round_number}...")
        
        try:
            request = corechain_pb2.ModelRequest(
                hospital_id=self.hospital_id,
                round_number=round_number
            )
            
            response = self.stub.GetGlobalModel(request)
            
            if response.round_number == 0:
                logger.warning("No global model available yet")
                return None
            
            # Deserialize weights
            import pickle
            weights = pickle.loads(response.model_weights)
            
            logger.success(
                f"Received global model: "
                f"Round {response.round_number}, "
                f"Accuracy: {response.global_accuracy:.4f}, "
                f"Loss: {response.global_loss:.4f}"
            )
            
            return weights
            
        except Exception as e:
            logger.error(f"Get global model error: {e}")
            return None
    
    def get_training_status(self) -> dict:
        """Get current training status"""
        if not corechain_pb2:
            logger.error("Protobuf not available")
            return {}
        
        try:
            request = corechain_pb2.StatusRequest(
                hospital_id=self.hospital_id
            )
            
            response = self.stub.GetTrainingStatus(request)
            
            status = {
                'current_round': response.current_round,
                'total_rounds': response.total_rounds,
                'connected_hospitals': response.connected_hospitals,
                'global_accuracy': response.global_accuracy,
                'global_loss': response.global_loss,
                'is_training': response.is_training,
                'next_round_eta': response.next_round_eta
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Get status error: {e}")
            return {}
    
    def close(self):
        """Close connection"""
        if self.channel:
            self.channel.close()
            logger.info("Connection closed")


if __name__ == "__main__":
    # Test client
    client = AggregatorClient(
        aggregator_ip=os.getenv('AGGREGATOR_IP', 'localhost'),
        aggregator_port=int(os.getenv('AGGREGATOR_PORT', 50051)),
        hospital_id=os.getenv('HOSPITAL_ID', 'hospital_test')
    )
    
    if client.connect():
        client.register(
            hospital_name="Test Hospital",
            dataset_size=1000,
            dataset_type="shenzhen"
        )
        
        status = client.get_training_status()
        logger.info(f"Training status: {status}")
        
        client.close()
