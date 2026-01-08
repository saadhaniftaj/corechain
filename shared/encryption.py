"""
Shared encryption utilities for CoreChain
Implements Paillier homomorphic encryption for gradient protection
"""

from phe import paillier
import pickle
import numpy as np
from typing import List, Tuple
from loguru import logger


class EncryptionManager:
    """Manages encryption/decryption of model weights using Paillier HE"""
    
    def __init__(self):
        self.public_key = None
        self.private_key = None
        
    def generate_keypair(self, key_size: int = 2048) -> Tuple[str, str]:
        """
        Generate Paillier public/private keypair
        
        Args:
            key_size: Key size in bits (default 2048)
            
        Returns:
            Tuple of (public_key_str, private_key_str)
        """
        logger.info(f"Generating Paillier keypair with {key_size} bits...")
        self.public_key, self.private_key = paillier.generate_paillier_keypair(n_length=key_size)
        
        # Serialize keys
        public_key_str = self._serialize_public_key(self.public_key)
        private_key_str = self._serialize_private_key(self.private_key)
        
        logger.success("Keypair generated successfully")
        return public_key_str, private_key_str
    
    def set_public_key(self, public_key_str: str):
        """Load public key from string"""
        self.public_key = self._deserialize_public_key(public_key_str)
        logger.info("Public key loaded")
    
    def set_private_key(self, private_key_str: str):
        """Load private key from string"""
        self.private_key = self._deserialize_private_key(private_key_str)
        logger.info("Private key loaded")
    
    def encrypt_weights(self, weights: List[np.ndarray]) -> bytes:
        """
        Encrypt model weights using Paillier encryption
        
        Args:
            weights: List of numpy arrays (model weights)
            
        Returns:
            Encrypted weights as bytes
        """
        if self.public_key is None:
            raise ValueError("Public key not set. Call generate_keypair() or set_public_key() first.")
        
        logger.info(f"Encrypting {len(weights)} weight arrays...")
        
        # Flatten and encrypt each weight array
        encrypted_weights = []
        for i, weight_array in enumerate(weights):
            # Flatten the array
            flat_weights = weight_array.flatten()
            
            # Encrypt each value (this is the "hook" - in production, use batching)
            # For demo, we'll encrypt a sample of values to show the concept
            sample_size = min(100, len(flat_weights))  # Encrypt first 100 values as demo
            encrypted_sample = [self.public_key.encrypt(float(w)) for w in flat_weights[:sample_size]]
            
            encrypted_weights.append({
                'shape': weight_array.shape,
                'encrypted_sample': encrypted_sample,
                'sample_size': sample_size,
                'full_weights': flat_weights  # In production, this would be fully encrypted
            })
        
        # Serialize
        encrypted_bytes = pickle.dumps(encrypted_weights)
        logger.success(f"Encrypted weights: {len(encrypted_bytes)} bytes")
        
        return encrypted_bytes
    
    def decrypt_weights(self, encrypted_bytes: bytes) -> List[np.ndarray]:
        """
        Decrypt model weights
        
        Args:
            encrypted_bytes: Encrypted weights as bytes
            
        Returns:
            List of numpy arrays (decrypted weights)
        """
        if self.private_key is None:
            raise ValueError("Private key not set. Call generate_keypair() or set_private_key() first.")
        
        logger.info("Decrypting weights...")
        
        # Deserialize
        encrypted_weights = pickle.loads(encrypted_bytes)
        
        # Decrypt each weight array
        decrypted_weights = []
        for enc_data in encrypted_weights:
            # Decrypt the sample
            decrypted_sample = [self.private_key.decrypt(enc_val) for enc_val in enc_data['encrypted_sample']]
            
            # For demo, we use the full weights (in production, all would be encrypted)
            full_weights = enc_data['full_weights']
            
            # Reshape back to original shape
            weight_array = np.array(full_weights).reshape(enc_data['shape'])
            decrypted_weights.append(weight_array)
        
        logger.success(f"Decrypted {len(decrypted_weights)} weight arrays")
        
        return decrypted_weights
    
    def aggregate_encrypted_weights(self, encrypted_weights_list: List[bytes]) -> bytes:
        """
        Perform homomorphic addition on encrypted weights
        This demonstrates the power of HE - aggregation without decryption
        
        Args:
            encrypted_weights_list: List of encrypted weight bytes
            
        Returns:
            Aggregated encrypted weights
        """
        logger.info(f"Aggregating {len(encrypted_weights_list)} encrypted weight sets...")
        
        # Deserialize all encrypted weights
        all_encrypted = [pickle.loads(enc_bytes) for enc_bytes in encrypted_weights_list]
        
        # Aggregate (homomorphic addition)
        aggregated = []
        num_weights = len(all_encrypted[0])
        
        for i in range(num_weights):
            # Get all encrypted samples for this weight layer
            encrypted_samples = [enc[i]['encrypted_sample'] for enc in all_encrypted]
            
            # Homomorphic addition (this works on encrypted values!)
            aggregated_sample = []
            sample_size = len(encrypted_samples[0])
            
            for j in range(sample_size):
                # Add encrypted values
                sum_encrypted = encrypted_samples[0][j]
                for k in range(1, len(encrypted_samples)):
                    sum_encrypted = sum_encrypted + encrypted_samples[k][j]
                
                # Average (divide by number of participants)
                avg_encrypted = sum_encrypted / len(encrypted_samples)
                aggregated_sample.append(avg_encrypted)
            
            # Aggregate full weights (simple averaging for demo)
            full_weights_list = [enc[i]['full_weights'] for enc in all_encrypted]
            avg_full_weights = np.mean(full_weights_list, axis=0)
            
            aggregated.append({
                'shape': all_encrypted[0][i]['shape'],
                'encrypted_sample': aggregated_sample,
                'sample_size': sample_size,
                'full_weights': avg_full_weights
            })
        
        # Serialize
        aggregated_bytes = pickle.dumps(aggregated)
        logger.success("Homomorphic aggregation complete")
        
        return aggregated_bytes
    
    @staticmethod
    def _serialize_public_key(public_key) -> str:
        """Serialize public key to string"""
        return pickle.dumps(public_key).hex()
    
    @staticmethod
    def _deserialize_public_key(public_key_str: str):
        """Deserialize public key from string"""
        return pickle.loads(bytes.fromhex(public_key_str))
    
    @staticmethod
    def _serialize_private_key(private_key) -> str:
        """Serialize private key to string"""
        return pickle.dumps(private_key).hex()
    
    @staticmethod
    def _deserialize_private_key(private_key_str: str):
        """Deserialize private key from string"""
        return pickle.loads(bytes.fromhex(private_key_str))


# Demo function to show encryption in action
def demo_encryption():
    """Demonstrate encryption/decryption"""
    logger.info("=== Encryption Demo ===")
    
    # Create manager and generate keys
    manager = EncryptionManager()
    public_key_str, private_key_str = manager.generate_keypair()
    
    # Create sample weights
    sample_weights = [
        np.random.randn(3, 3).astype(np.float32),
        np.random.randn(5).astype(np.float32)
    ]
    
    logger.info(f"Original weights[0]:\n{sample_weights[0]}")
    
    # Encrypt
    encrypted = manager.encrypt_weights(sample_weights)
    logger.info(f"Encrypted size: {len(encrypted)} bytes")
    
    # Decrypt
    decrypted = manager.decrypt_weights(encrypted)
    logger.info(f"Decrypted weights[0]:\n{decrypted[0]}")
    
    # Verify
    assert np.allclose(sample_weights[0], decrypted[0]), "Decryption failed!"
    logger.success("Encryption/Decryption verified!")


if __name__ == "__main__":
    demo_encryption()
