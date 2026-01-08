"""
Data Loader for TB Datasets (Shenzhen and Montgomery)
Handles loading, preprocessing, and augmentation
"""

import os
import numpy as np
from PIL import Image
import tensorflow as tf
from sklearn.model_selection import train_test_split
from loguru import logger
from typing import Tuple, Optional
import glob


class TBDataLoader:
    """Data loader for TB chest X-ray datasets"""
    
    def __init__(
        self,
        dataset_path: str,
        dataset_type: str = 'shenzhen',
        img_size: Tuple[int, int] = (224, 224),
        test_split: float = 0.2,
        random_seed: int = 42
    ):
        self.dataset_path = dataset_path
        self.dataset_type = dataset_type.lower()
        self.img_size = img_size
        self.test_split = test_split
        self.random_seed = random_seed
        
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None
        
        logger.info(f"TBDataLoader initialized: {dataset_type} dataset at {dataset_path}")
    
    def load_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Load and preprocess TB dataset
        
        Returns:
            Tuple of (x_train, y_train, x_test, y_test)
        """
        logger.info(f"Loading {self.dataset_type} dataset...")
        
        # Check if dataset exists
        if not os.path.exists(self.dataset_path):
            logger.warning(f"Dataset path {self.dataset_path} not found. Creating synthetic data for demo...")
            return self._create_synthetic_data()
        
        # Load images and labels
        images = []
        labels = []
        
        # Look for image files
        image_extensions = ['*.png', '*.jpg', '*.jpeg']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(self.dataset_path, '**', ext), recursive=True))
        
        if not image_files:
            logger.warning(f"No images found in {self.dataset_path}. Creating synthetic data for demo...")
            return self._create_synthetic_data()
        
        logger.info(f"Found {len(image_files)} images")
        
        # Load images
        for img_path in image_files:
            try:
                # Load and preprocess image
                img = Image.open(img_path).convert('L')  # Convert to grayscale
                img = img.resize(self.img_size)
                img_array = np.array(img) / 255.0  # Normalize to [0, 1]
                
                images.append(img_array)
                
                # Determine label from filename or directory
                # Assuming 'normal' or 'tb' in path indicates label
                label = 1 if 'tb' in img_path.lower() or 'positive' in img_path.lower() else 0
                labels.append(label)
                
            except Exception as e:
                logger.warning(f"Failed to load {img_path}: {e}")
        
        if not images:
            logger.warning("No valid images loaded. Creating synthetic data for demo...")
            return self._create_synthetic_data()
        
        # Convert to numpy arrays
        images = np.array(images)
        labels = np.array(labels)
        
        # Add channel dimension
        images = np.expand_dims(images, axis=-1)
        
        logger.info(f"Loaded {len(images)} images with shape {images.shape}")
        logger.info(f"Label distribution: TB={np.sum(labels)}, Normal={len(labels)-np.sum(labels)}")
        
        # Split into train/test
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            images, labels,
            test_size=self.test_split,
            random_state=self.random_seed,
            stratify=labels
        )
        
        logger.success(
            f"Data split: train={len(self.x_train)}, test={len(self.x_test)}"
        )
        
        return self.x_train, self.y_train, self.x_test, self.y_test
    
    def _create_synthetic_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Create synthetic data for demo purposes"""
        logger.info("Creating synthetic TB dataset for demonstration...")
        
        # Create synthetic images (random noise with some structure)
        num_samples = 1000
        
        images = []
        labels = []
        
        for i in range(num_samples):
            # Create base image with some structure
            img = np.random.randn(*self.img_size) * 0.3 + 0.5
            
            # Add some "features" to simulate X-rays
            if i % 2 == 0:  # TB positive
                # Add some bright spots (simulate lesions)
                num_spots = np.random.randint(2, 5)
                for _ in range(num_spots):
                    x = np.random.randint(50, self.img_size[0] - 50)
                    y = np.random.randint(50, self.img_size[1] - 50)
                    size = np.random.randint(10, 30)
                    img[x:x+size, y:y+size] += 0.3
                
                labels.append(1)
            else:  # Normal
                # Add more uniform structure
                img += np.random.randn(*self.img_size) * 0.1
                labels.append(0)
            
            # Clip to [0, 1]
            img = np.clip(img, 0, 1)
            images.append(img)
        
        images = np.array(images)
        labels = np.array(labels)
        
        # Add channel dimension
        images = np.expand_dims(images, axis=-1)
        
        # Split into train/test
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            images, labels,
            test_size=self.test_split,
            random_state=self.random_seed,
            stratify=labels
        )
        
        logger.success(
            f"Synthetic data created: train={len(self.x_train)}, test={len(self.x_test)}"
        )
        
        return self.x_train, self.y_train, self.x_test, self.y_test
    
    def get_data_augmentation(self):
        """Get data augmentation pipeline"""
        return tf.keras.Sequential([
            tf.keras.layers.RandomRotation(0.1),
            tf.keras.layers.RandomZoom(0.1),
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomContrast(0.1),
        ])
    
    def get_dataset_info(self) -> dict:
        """Get dataset statistics"""
        if self.x_train is None:
            return {}
        
        return {
            'dataset_type': self.dataset_type,
            'train_samples': len(self.x_train),
            'test_samples': len(self.x_test),
            'image_shape': self.x_train.shape[1:],
            'train_tb_positive': int(np.sum(self.y_train)),
            'train_tb_negative': int(len(self.y_train) - np.sum(self.y_train)),
            'test_tb_positive': int(np.sum(self.y_test)),
            'test_tb_negative': int(len(self.y_test) - np.sum(self.y_test))
        }


# Demo
if __name__ == "__main__":
    logger.info("=== TB Data Loader Demo ===")
    
    # Create loader
    loader = TBDataLoader(
        dataset_path='/data',
        dataset_type='shenzhen'
    )
    
    # Load data
    x_train, y_train, x_test, y_test = loader.load_data()
    
    # Get info
    info = loader.get_dataset_info()
    logger.info(f"Dataset info: {info}")
    
    # Show sample
    logger.info(f"Sample image shape: {x_train[0].shape}")
    logger.info(f"Sample label: {y_train[0]}")
