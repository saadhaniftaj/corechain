"""
Flower Client for Hospital Nodes
Implements federated learning client logic
"""

import flwr as fl
from loguru import logger
import numpy as np
from typing import List, Tuple, Dict
import os

from tb_model import TBDetectionModel
from data_loader import TBDataLoader


class TBFlowerClient(fl.client.NumPyClient):
    """Flower client for TB detection model training"""
    
    def __init__(
        self,
        hospital_id: str,
        model: TBDetectionModel,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_test: np.ndarray,
        y_test: np.ndarray,
        local_epochs: int = 5,
        batch_size: int = 32
    ):
        self.hospital_id = hospital_id
        self.model = model
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        
        logger.info(f"Flower client initialized for {hospital_id}")
    
    def get_parameters(self, config: Dict) -> List[np.ndarray]:
        """Return current model parameters"""
        logger.info(f"{self.hospital_id}: Getting model parameters")
        return self.model.get_weights()
    
    def fit(
        self,
        parameters: List[np.ndarray],
        config: Dict
    ) -> Tuple[List[np.ndarray], int, Dict]:
        """
        Train model on local data
        
        Args:
            parameters: Global model parameters
            config: Training configuration
            
        Returns:
            Tuple of (updated_parameters, num_examples, metrics)
        """
        logger.info(f"{self.hospital_id}: Starting local training...")
        
        # Update model with global parameters
        self.model.set_weights(parameters)
        
        # Train model
        history = self.model.train(
            self.x_train,
            self.y_train,
            self.x_test,
            self.y_test,
            epochs=self.local_epochs,
            batch_size=self.batch_size,
            verbose=0
        )
        
        # Get updated parameters
        updated_parameters = self.model.get_weights()
        
        # Calculate metrics
        num_examples = len(self.x_train)
        
        # Get final epoch metrics
        metrics = {
            'loss': float(history['loss'][-1]),
            'accuracy': float(history['accuracy'][-1]),
            'val_loss': float(history['val_loss'][-1]) if 'val_loss' in history else 0.0,
            'val_accuracy': float(history['val_accuracy'][-1]) if 'val_accuracy' in history else 0.0
        }
        
        logger.success(
            f"{self.hospital_id}: Training complete - "
            f"accuracy={metrics['accuracy']:.4f}, loss={metrics['loss']:.4f}"
        )
        
        return updated_parameters, num_examples, metrics
    
    def evaluate(
        self,
        parameters: List[np.ndarray],
        config: Dict
    ) -> Tuple[float, int, Dict]:
        """
        Evaluate model on local test data
        
        Args:
            parameters: Model parameters to evaluate
            config: Evaluation configuration
            
        Returns:
            Tuple of (loss, num_examples, metrics)
        """
        logger.info(f"{self.hospital_id}: Evaluating model...")
        
        # Update model with parameters
        self.model.set_weights(parameters)
        
        # Evaluate
        metrics = self.model.evaluate(self.x_test, self.y_test, self.batch_size)
        
        loss = metrics.get('loss', 0.0)
        num_examples = len(self.x_test)
        
        logger.success(
            f"{self.hospital_id}: Evaluation complete - "
            f"accuracy={metrics.get('accuracy', 0):.4f}, loss={loss:.4f}"
        )
        
        return loss, num_examples, metrics


def create_flower_client(
    hospital_id: str,
    dataset_path: str,
    dataset_type: str = 'shenzhen'
) -> TBFlowerClient:
    """
    Create and initialize a Flower client
    
    Args:
        hospital_id: Hospital identifier
        dataset_path: Path to dataset
        dataset_type: Type of dataset ('shenzhen' or 'montgomery')
        
    Returns:
        Initialized TBFlowerClient
    """
    logger.info(f"Creating Flower client for {hospital_id}...")
    
    # Load data
    data_loader = TBDataLoader(
        dataset_path=dataset_path,
        dataset_type=dataset_type
    )
    x_train, y_train, x_test, y_test = data_loader.load_data()
    
    # Log dataset info
    info = data_loader.get_dataset_info()
    logger.info(f"Dataset info: {info}")
    
    # Create model
    model = TBDetectionModel()
    model.compile_model(
        learning_rate=float(os.getenv('LEARNING_RATE', 0.001))
    )
    
    # Create client
    client = TBFlowerClient(
        hospital_id=hospital_id,
        model=model,
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        local_epochs=int(os.getenv('LOCAL_EPOCHS', 5)),
        batch_size=int(os.getenv('BATCH_SIZE', 32))
    )
    
    logger.success(f"Flower client created for {hospital_id}")
    
    return client


# Demo
if __name__ == "__main__":
    logger.info("=== Flower Client Demo ===")
    
    # Create client
    client = create_flower_client(
        hospital_id='hospital_demo',
        dataset_path='/data',
        dataset_type='shenzhen'
    )
    
    # Get initial parameters
    params = client.get_parameters({})
    logger.info(f"Initial parameters: {len(params)} layers")
    
    # Simulate training
    updated_params, num_examples, metrics = client.fit(params, {})
    logger.info(f"Training metrics: {metrics}")
    
    # Evaluate
    loss, num_examples, eval_metrics = client.evaluate(updated_params, {})
    logger.info(f"Evaluation metrics: {eval_metrics}")
