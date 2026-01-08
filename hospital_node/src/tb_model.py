"""
TB Detection Model using TensorFlow/Keras
CNN architecture for chest X-ray analysis
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from loguru import logger
import numpy as np
from typing import Tuple


class TBDetectionModel:
    """CNN model for TB detection from chest X-rays"""
    
    def __init__(self, input_shape: Tuple[int, int, int] = (224, 224, 1)):
        self.input_shape = input_shape
        self.model = None
        self._build_model()
        
        logger.info(f"TB Detection Model initialized with input shape {input_shape}")
    
    def _build_model(self):
        """Build CNN architecture"""
        self.model = models.Sequential([
            # Input layer
            layers.Input(shape=self.input_shape),
            
            # First convolutional block
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Second convolutional block
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Third convolutional block
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Fourth convolutional block
            layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Dense layers
            layers.Flatten(),
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            
            # Output layer (binary classification)
            layers.Dense(1, activation='sigmoid')
        ])
        
        logger.success("Model architecture built")
    
    def compile_model(
        self,
        learning_rate: float = 0.001,
        metrics: list = None
    ):
        """Compile the model"""
        if metrics is None:
            metrics = [
                'accuracy',
                tf.keras.metrics.AUC(name='auc'),
                tf.keras.metrics.Precision(name='precision'),
                tf.keras.metrics.Recall(name='recall')
            ]
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='binary_crossentropy',
            metrics=metrics
        )
        
        logger.success(f"Model compiled with learning rate {learning_rate}")
    
    def get_weights(self) -> list:
        """Get model weights"""
        return self.model.get_weights()
    
    def set_weights(self, weights: list):
        """Set model weights"""
        self.model.set_weights(weights)
        logger.info("Model weights updated")
    
    def train(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_val: np.ndarray = None,
        y_val: np.ndarray = None,
        epochs: int = 5,
        batch_size: int = 32,
        verbose: int = 1
    ) -> dict:
        """
        Train the model
        
        Args:
            x_train: Training images
            y_train: Training labels
            x_val: Validation images (optional)
            y_val: Validation labels (optional)
            epochs: Number of epochs
            batch_size: Batch size
            verbose: Verbosity level
            
        Returns:
            Training history
        """
        logger.info(f"Training model for {epochs} epochs...")
        
        validation_data = None
        if x_val is not None and y_val is not None:
            validation_data = (x_val, y_val)
        
        history = self.model.fit(
            x_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss' if validation_data else 'loss',
                    patience=3,
                    restore_best_weights=True
                )
            ]
        )
        
        logger.success("Training completed")
        
        return history.history
    
    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        batch_size: int = 32
    ) -> dict:
        """
        Evaluate the model
        
        Args:
            x_test: Test images
            y_test: Test labels
            batch_size: Batch size
            
        Returns:
            Evaluation metrics
        """
        logger.info("Evaluating model...")
        
        results = self.model.evaluate(x_test, y_test, batch_size=batch_size, verbose=0)
        
        metrics = {}
        for i, metric_name in enumerate(self.model.metrics_names):
            metrics[metric_name] = float(results[i])
        
        logger.success(f"Evaluation complete: accuracy={metrics.get('accuracy', 0):.4f}")
        
        return metrics
    
    def predict(self, x: np.ndarray) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(x, verbose=0)
    
    def save_model(self, filepath: str):
        """Save model to file"""
        self.model.save(filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model from file"""
        self.model = keras.models.load_model(filepath)
        logger.info(f"Model loaded from {filepath}")
    
    def summary(self):
        """Print model summary"""
        self.model.summary()
    
    def count_parameters(self) -> int:
        """Count total trainable parameters"""
        return self.model.count_params()


# Demo
if __name__ == "__main__":
    logger.info("=== TB Detection Model Demo ===")
    
    # Create model
    model = TBDetectionModel()
    model.compile_model()
    
    # Print summary
    model.summary()
    
    logger.info(f"Total parameters: {model.count_parameters():,}")
    
    # Test with random data
    x_train = np.random.randn(100, 224, 224, 1).astype(np.float32)
    y_train = np.random.randint(0, 2, 100).astype(np.float32)
    
    x_val = np.random.randn(20, 224, 224, 1).astype(np.float32)
    y_val = np.random.randint(0, 2, 20).astype(np.float32)
    
    # Train for 1 epoch as demo
    history = model.train(x_train, y_train, x_val, y_val, epochs=1, batch_size=16)
    
    logger.info(f"Training history: {history}")
    
    # Evaluate
    metrics = model.evaluate(x_val, y_val)
    logger.info(f"Evaluation metrics: {metrics}")
