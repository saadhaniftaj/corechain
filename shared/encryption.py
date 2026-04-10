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
        Encrypt model weights using Paillier homomorphic encryption.
        All weight values are encrypted (no demo cap).
        Note: PHE is computationally expensive; use small models or reduce precision for speed.
        """
        if self.public_key is None:
            raise ValueError("Public key not set. Call generate_keypair() or set_public_key() first.")

        logger.info(f"Encrypting {len(weights)} weight arrays (full HE)...")

        encrypted_weights = []
        for weight_array in weights:
            flat = weight_array.flatten().tolist()
            # Encrypt every value
            encrypted_vals = [self.public_key.encrypt(float(v)) for v in flat]
            encrypted_weights.append({
                'shape': weight_array.shape,
                'encrypted_vals': encrypted_vals,
            })

        encrypted_bytes = pickle.dumps(encrypted_weights)
        logger.success(f"Encrypted weights: {len(encrypted_bytes)} bytes")
        return encrypted_bytes
    
    def decrypt_weights(self, encrypted_bytes: bytes) -> List[np.ndarray]:
        """Decrypt model weights encrypted with Paillier HE."""
        if self.private_key is None:
            raise ValueError("Private key not set.")

        logger.info("Decrypting weights...")
        encrypted_weights = pickle.loads(encrypted_bytes)

        decrypted_weights = []
        for enc in encrypted_weights:
            decrypted_vals = [self.private_key.decrypt(v) for v in enc['encrypted_vals']]
            weight_array = np.array(decrypted_vals, dtype=np.float32).reshape(enc['shape'])
            decrypted_weights.append(weight_array)

        logger.success(f"Decrypted {len(decrypted_weights)} weight arrays")
        return decrypted_weights
    
    def aggregate_encrypted_weights(self, encrypted_weights_list: List[bytes]) -> bytes:
        """
        Homomorphic aggregation — adds encrypted weights without decrypting.
        This is the core privacy guarantee of Paillier HE.
        """
        logger.info(f"Homomorphic aggregation of {len(encrypted_weights_list)} encrypted sets...")

        all_encrypted = [pickle.loads(b) for b in encrypted_weights_list]
        n = len(all_encrypted)
        aggregated = []

        for layer_idx in range(len(all_encrypted[0])):
            enc_vals_per_client = [all_encrypted[c][layer_idx]['encrypted_vals'] for c in range(n)]
            shape = all_encrypted[0][layer_idx]['shape']
            num_vals = len(enc_vals_per_client[0])

            # Homomorphic addition then division (Paillier supports this natively)
            agg_vals = []
            for j in range(num_vals):
                total = enc_vals_per_client[0][j]
                for c in range(1, n):
                    total = total + enc_vals_per_client[c][j]
                agg_vals.append(total / n)  # Paillier supports scalar division

            aggregated.append({'shape': shape, 'encrypted_vals': agg_vals})

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
