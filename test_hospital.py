#!/usr/bin/env python3
"""
Test script to verify hospital node functionality locally
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

from hospital_node.src.data_loader import TBDataLoader
from hospital_node.src.tb_model import TBModel

def test_data_loading():
    """Test data loading"""
    print("=" * 60)
    print("TEST 1: Data Loading")
    print("=" * 60)
    
    loader = TBDataLoader(
        dataset_path='data/tb_dataset/archive',
        dataset_type='shenzhen'
    )
    
    X_train, y_train, X_test, y_test = loader.load_data()
    
    print(f"✅ Data loaded successfully!")
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    print(f"   Image shape: {X_train[0].shape}")
    print(f"   Positive samples (TB): {sum(y_train)}")
    print(f"   Negative samples (Normal): {len(y_train) - sum(y_train)}")
    
    return X_train, y_train, X_test, y_test

def test_model_creation():
    """Test model creation"""
    print("\n" + "=" * 60)
    print("TEST 2: Model Creation")
    print("=" * 60)
    
    model = TBModel()
    print(f"✅ Model created successfully!")
    print(f"   Input shape: {model.model.input_shape}")
    print(f"   Output shape: {model.model.output_shape}")
    print(f"   Total parameters: {model.model.count_params():,}")
    
    return model

def test_training(model, X_train, y_train, X_test, y_test):
    """Test model training"""
    print("\n" + "=" * 60)
    print("TEST 3: Model Training (1 epoch)")
    print("=" * 60)
    
    # Train for 1 epoch only
    history = model.train(X_train, y_train, X_test, y_test, epochs=1, batch_size=16)
    
    print(f"✅ Training completed!")
    print(f"   Training accuracy: {history.history['accuracy'][-1]:.4f}")
    print(f"   Training loss: {history.history['loss'][-1]:.4f}")
    print(f"   Validation accuracy: {history.history['val_accuracy'][-1]:.4f}")
    print(f"   Validation loss: {history.history['val_loss'][-1]:.4f}")
    
    return history

if __name__ == "__main__":
    try:
        # Test 1: Data Loading
        X_train, y_train, X_test, y_test = test_data_loading()
        
        # Test 2: Model Creation
        model = test_model_creation()
        
        # Test 3: Training
        history = test_training(model, X_train, y_train, X_test, y_test)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
