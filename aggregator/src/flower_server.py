"""
Flower Server for Aggregator
Implements federated averaging strategy
"""

import flwr as fl
from flwr.server.strategy import FedAvg
from flwr.common import Parameters, FitRes, EvaluateRes
from flwr.server.client_proxy import ClientProxy
from loguru import logger
from typing import List, Tuple, Dict, Optional, Union
import numpy as np
import os


class CoreChainStrategy(FedAvg):
    """Custom Federated Averaging strategy for CoreChain"""
    
    def __init__(
        self,
        blockchain_client=None,
        websocket_server=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.blockchain_client = blockchain_client
        self.websocket_server = websocket_server
        self.current_round = 0
        
        logger.info("CoreChainStrategy initialized")
    
    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]]
    ) -> Tuple[Optional[Parameters], Dict]:
        """Aggregate model updates from clients"""
        
        self.current_round = server_round
        
        logger.info(f"Round {server_round}: Aggregating {len(results)} client updates...")
        
        # Log to blockchain
        if self.blockchain_client:
            for client, fit_res in results:
                self.blockchain_client.log_transaction({
                    'type': 'MODEL_UPDATE',
                    'hospital_id': str(client.cid),
                    'round': server_round,
                    'accuracy': fit_res.metrics.get('accuracy', 0.0),
                    'loss': fit_res.metrics.get('loss', 0.0),
                    'samples_trained': fit_res.num_examples
                })
        
        # Perform standard FedAvg aggregation
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures
        )
        
        # Calculate global metrics
        total_examples = sum([fit_res.num_examples for _, fit_res in results])
        
        weighted_accuracy = sum([
            fit_res.metrics.get('accuracy', 0.0) * fit_res.num_examples
            for _, fit_res in results
        ]) / total_examples if total_examples > 0 else 0.0
        
        weighted_loss = sum([
            fit_res.metrics.get('loss', 0.0) * fit_res.num_examples
            for _, fit_res in results
        ]) / total_examples if total_examples > 0 else 0.0
        
        logger.success(
            f"Round {server_round} aggregation complete: "
            f"accuracy={weighted_accuracy:.4f}, loss={weighted_loss:.4f}"
        )
        
        # Log aggregation to blockchain
        if self.blockchain_client:
            self.blockchain_client.log_transaction({
                'type': 'MODEL_AGGREGATION',
                'round': server_round,
                'global_accuracy': weighted_accuracy,
                'global_loss': weighted_loss,
                'participants': len(results),
                'total_samples': total_examples
            })
            
            # Distribute rewards
            for client, fit_res in results:
                reward = self._calculate_reward(
                    accuracy=fit_res.metrics.get('accuracy', 0.0),
                    samples=fit_res.num_examples,
                    total_samples=total_examples
                )
                
                self.blockchain_client.log_transaction({
                    'type': 'REWARD_DISTRIBUTION',
                    'hospital_id': str(client.cid),
                    'round': server_round,
                    'reward_tokens': reward,
                    'accuracy': fit_res.metrics.get('accuracy', 0.0),
                    'samples_contributed': fit_res.num_examples
                })
        
        # Broadcast to dashboard
        if self.websocket_server:
            import asyncio
            asyncio.create_task(self.websocket_server.broadcast({
                'event': 'model_aggregated',
                'data': {
                    'round': server_round,
                    'accuracy': weighted_accuracy,
                    'loss': weighted_loss,
                    'participants': len(results)
                }
            }))
        
        # Add global metrics to aggregated_metrics
        aggregated_metrics['global_accuracy'] = weighted_accuracy
        aggregated_metrics['global_loss'] = weighted_loss
        aggregated_metrics['round'] = server_round
        
        return aggregated_parameters, aggregated_metrics
    
    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, EvaluateRes]],
        failures: List[Union[Tuple[ClientProxy, EvaluateRes], BaseException]]
    ) -> Tuple[Optional[float], Dict]:
        """Aggregate evaluation results from clients"""
        
        logger.info(f"Round {server_round}: Aggregating {len(results)} evaluation results...")
        
        # Perform standard aggregation
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(
            server_round, results, failures
        )
        
        # Calculate weighted metrics
        total_examples = sum([eval_res.num_examples for _, eval_res in results])
        
        weighted_accuracy = sum([
            eval_res.metrics.get('accuracy', 0.0) * eval_res.num_examples
            for _, eval_res in results
        ]) / total_examples if total_examples > 0 else 0.0
        
        logger.success(
            f"Round {server_round} evaluation complete: "
            f"accuracy={weighted_accuracy:.4f}, loss={aggregated_loss:.4f}"
        )
        
        # Broadcast to dashboard
        if self.websocket_server:
            import asyncio
            asyncio.create_task(self.websocket_server.broadcast({
                'event': 'accuracy_updated',
                'data': {
                    'round': server_round,
                    'accuracy': weighted_accuracy,
                    'loss': aggregated_loss
                }
            }))
        
        aggregated_metrics['global_accuracy'] = weighted_accuracy
        
        return aggregated_loss, aggregated_metrics
    
    def _calculate_reward(
        self,
        accuracy: float,
        samples: int,
        total_samples: int
    ) -> float:
        """Calculate reward tokens for a hospital"""
        base_reward = 10.0
        accuracy_bonus = accuracy * 5.0
        sample_bonus = (samples / total_samples) * 5.0 if total_samples > 0 else 0.0
        
        reward = base_reward + accuracy_bonus + sample_bonus
        
        # Quality multiplier
        if accuracy > 0.9:
            reward *= 1.2
        
        return round(reward, 2)


def create_flower_server(
    min_clients: int = 2,
    num_rounds: int = 10,
    blockchain_client=None,
    websocket_server=None
):
    """
    Create Flower server with CoreChain strategy
    
    Args:
        min_clients: Minimum number of clients required
        num_rounds: Number of FL rounds
        blockchain_client: Blockchain client for logging
        websocket_server: WebSocket server for broadcasting
        
    Returns:
        Configured Flower server
    """
    logger.info(f"Creating Flower server: min_clients={min_clients}, rounds={num_rounds}")
    
    # Create strategy
    strategy = CoreChainStrategy(
        blockchain_client=blockchain_client,
        websocket_server=websocket_server,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
        fraction_fit=1.0,  # Use all available clients
        fraction_evaluate=1.0
    )
    
    logger.success("Flower server strategy created")
    
    return strategy, num_rounds


def start_flower_server(
    server_address: str = "0.0.0.0:8080",
    min_clients: int = 2,
    num_rounds: int = 10,
    blockchain_client=None,
    websocket_server=None
):
    """Start Flower server"""
    
    logger.info(f"Starting Flower server on {server_address}...")
    
    strategy, rounds = create_flower_server(
        min_clients=min_clients,
        num_rounds=num_rounds,
        blockchain_client=blockchain_client,
        websocket_server=websocket_server
    )
    
    # Start server
    fl.server.start_server(
        server_address=server_address,
        config=fl.server.ServerConfig(num_rounds=rounds),
        strategy=strategy
    )
    
    logger.success("Flower server completed all rounds")


if __name__ == "__main__":
    # Demo server
    start_flower_server(
        server_address="0.0.0.0:8080",
        min_clients=int(os.getenv('MIN_CLIENTS', 2)),
        num_rounds=int(os.getenv('FL_ROUNDS', 10))
    )
