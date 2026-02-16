# Mahad's Presentation Guide: Federated Learning & Aggregator

## Your Responsibility
**Flower Server Setup, FL Aggregation Logic, and Training Coordination**

You handled the Flower aggregator server, federated learning algorithms, client-server synchronization, and the mathematical aggregation of model parameters.

---

## 1. Federated Learning Overview

### What is Federated Learning?
**Definition**: A machine learning approach where multiple parties (hospitals) collaboratively train a model without sharing their raw data.

**Key Principle**: "Bring the model to the data, not the data to the model"

### Why FL for Healthcare?
1. **Privacy**: Patient data never leaves the hospital
2. **Compliance**: Meets HIPAA, GDPR requirements
3. **Data Diversity**: Learn from multiple hospitals' data
4. **Better Models**: More training data = better accuracy
5. **Trust**: Hospitals maintain control of their data

---

## 2. Flower Framework

### Technology Stack
- **Framework**: Flower (Federated Learning framework)
- **Version**: 1.6.0
- **Language**: Python 3.10
- **Communication**: gRPC (port 8080)
- **Strategy**: FedAvg (Federated Averaging)

### Why Flower?
1. **Production-Ready**: Used by major companies
2. **Framework Agnostic**: Works with TensorFlow, PyTorch
3. **Scalable**: Handles thousands of clients
4. **Flexible**: Customizable aggregation strategies
5. **Active Development**: Regular updates and support

### File Location
```
aggregator/src/flower_server.py
```

---

## 3. Flower Server Architecture

### Server Components

```python
import flwr as fl
from flwr.server.strategy import FedAvg

def start_flower_server():
    """Start Flower aggregator server"""
    
    # 1. Define aggregation strategy
    strategy = FedAvg(
        fraction_fit=1.0,          # Use 100% of available clients
        fraction_evaluate=1.0,      # Evaluate on 100% of clients
        min_fit_clients=1,          # Minimum clients for training
        min_evaluate_clients=1,     # Minimum clients for evaluation
        min_available_clients=1,    # Wait for 1 client before starting
    )
    
    # 2. Configure server
    config = fl.server.ServerConfig(
        num_rounds=10,              # Total FL rounds
        round_timeout=600           # 10 minutes per round
    )
    
    # 3. Start server
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=config,
        strategy=strategy
    )
```

### Key Configuration Explained

#### `fraction_fit` and `fraction_evaluate`
- **Value**: 1.0 (100%)
- **Meaning**: Use all available clients for training/evaluation
- **Why**: With few hospitals, we want all to participate

#### `min_fit_clients` and `min_evaluate_clients`
- **Value**: 1
- **Meaning**: Need at least 1 client to proceed
- **Why**: Allows testing with single hospital

#### `min_available_clients`
- **Value**: 1
- **Meaning**: Wait for 1 client to connect before starting
- **Why**: Server won't start rounds until a hospital connects
- **Critical Fix**: This prevents the deadlock issue we had

#### `round_timeout`
- **Value**: 600 seconds (10 minutes)
- **Meaning**: Each round must complete within 10 minutes
- **Why**: Training + parameter transfer takes ~3-4 minutes
- **Your Fix**: Increased from default 60s to prevent timeouts

---

## 4. Federated Averaging (FedAvg) Algorithm

### Mathematical Formula

**Given:**
- $n$ hospitals (clients)
- $w_i$ = model parameters from hospital $i$
- $n_i$ = number of training samples at hospital $i$
- $N = \sum_{i=1}^{n} n_i$ = total samples across all hospitals

**Aggregation:**
$$
w_{global} = \frac{1}{N} \sum_{i=1}^{n} n_i \cdot w_i
$$

**In Words**: The global model is a weighted average of local models, where weights are proportional to the number of training samples.

### Why Weighted Average?
- Hospitals with more data have more influence
- Prevents small datasets from skewing the model
- Statistically optimal under certain assumptions

### Example Calculation

**Scenario:**
- Hospital A: 500 samples, accuracy = 75%
- Hospital B: 300 samples, accuracy = 70%

**Weights:**
- $w_A = 500 / (500 + 300) = 0.625$
- $w_B = 300 / (500 + 300) = 0.375$

**Global Accuracy:**
$$
\text{Global} = 0.625 \times 0.75 + 0.375 \times 0.70 = 0.7313 = 73.13\%
$$

### Code Implementation

```python
def aggregate_fit(
    self,
    server_round: int,
    results: List[Tuple[ClientProxy, FitRes]],
    failures: List[BaseException],
) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
    """Aggregate model parameters using weighted average"""
    
    # Extract parameters and number of samples
    weights_results = [
        (parameters_to_ndarrays(fit_res.parameters), fit_res.num_examples)
        for _, fit_res in results
    ]
    
    # Perform weighted averaging
    parameters_aggregated = ndarrays_to_parameters(
        aggregate(weights_results)
    )
    
    return parameters_aggregated, {}

def aggregate(results: List[Tuple[NDArrays, int]]) -> NDArrays:
    """Compute weighted average of parameters"""
    
    # Calculate total number of examples
    num_examples_total = sum(num_examples for (_, num_examples) in results)
    
    # Create weighted average
    weighted_weights = [
        [layer * num_examples for layer in weights]
        for weights, num_examples in results
    ]
    
    # Sum all weighted weights
    weights_prime: NDArrays = [
        reduce(np.add, layer_updates)
        for layer_updates in zip(*weighted_weights)
    ]
    
    # Divide by total examples
    return [
        layer / num_examples_total
        for layer in weights_prime
    ]
```

---

## 5. FL Training Workflow

### Complete Round Lifecycle

```
1. Server Initialization
   ↓
2. Wait for min_available_clients (1 hospital)
   ↓
3. Server sends global model parameters to hospital
   ↓
4. Hospital receives parameters via gRPC
   ↓
5. Hospital trains model locally (5 epochs)
   ↓
6. Hospital sends updated parameters back
   ↓
7. Server receives parameters
   ↓
8. Server aggregates parameters (FedAvg)
   ↓
9. Server updates global model
   ↓
10. Server registers model on blockchain
   ↓
11. Repeat steps 3-10 for next round
```

### Timing Breakdown (Per Round)

| Phase | Duration | Details |
|-------|----------|---------|
| Parameter Download | ~5 seconds | 56.7 MB transfer |
| Local Training | ~3.5 minutes | 5 epochs on 529 images |
| Parameter Upload | ~5 seconds | 56.7 MB transfer |
| Aggregation | < 1 second | Weighted average |
| Blockchain Logging | ~2 seconds | Transaction confirmation |
| **Total** | **~4 minutes** | Per round |

---

## 6. Client Synchronization

### The Deadlock Problem

**Original Issue:**
```python
# BAD: Server requested parameters before clients connected
def initialize_parameters(self, client_manager):
    # This runs immediately, before any clients connect!
    return get_initial_parameters()
```

**Result**: Server waited for parameters that would never come.

### Your Solution

```python
def initialize_parameters(self, client_manager):
    """Wait for clients before requesting parameters"""
    
    logger.info("Waiting for clients to connect...")
    
    # Wait for minimum clients
    while True:
        num_clients = client_manager.num_available()
        if num_clients >= self.min_available_clients:
            logger.success(f"{num_clients} clients connected")
            break
        time.sleep(1)
    
    # Now request parameters from a connected client
    sample_client = client_manager.sample(1)[0]
    ins = GetParametersIns(config={})
    get_params_res = sample_client.get_parameters(ins=ins, timeout=None)
    
    return get_params_res.parameters
```

**Why This Works:**
1. Explicitly waits for `min_available_clients`
2. Only requests parameters after clients connect
3. Prevents deadlock by ensuring client availability

---

## 7. gRPC Keepalive Configuration

### The Timeout Problem

**Original Issue**: Clients disconnected after ~22 minutes due to gRPC keepalive timeout.

### Your Solution

```python
# File: hospital_node/src/main.py

import os

# Set gRPC environment variables
os.environ['GRPC_KEEPALIVE_TIME_MS'] = '10000'        # Ping every 10s
os.environ['GRPC_KEEPALIVE_TIMEOUT_MS'] = '5000'      # Timeout after 5s
os.environ['GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS'] = '1'  # Allow pings
os.environ['GRPC_HTTP2_MIN_RECV_PING_INTERVAL_WITHOUT_DATA_MS'] = '5000'
os.environ['GRPC_HTTP2_MAX_PINGS_WITHOUT_DATA'] = '0'  # Unlimited pings

# Now start Flower client
fl.client.start_numpy_client(
    server_address="54.173.119.88:8080",
    client=client
)
```

**Configuration Explained:**

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `GRPC_KEEPALIVE_TIME_MS` | 10000 | Send ping every 10 seconds |
| `GRPC_KEEPALIVE_TIMEOUT_MS` | 5000 | Wait 5 seconds for pong |
| `GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS` | 1 | Allow pings even when idle |
| `GRPC_HTTP2_MIN_RECV_PING_INTERVAL_WITHOUT_DATA_MS` | 5000 | Accept pings every 5 seconds |
| `GRPC_HTTP2_MAX_PINGS_WITHOUT_DATA` | 0 | No limit on pings |

**Why This Works:**
- Prevents connection drops during long training
- Maintains connection even when no data is being sent
- Detects disconnections quickly (5s timeout)

---

## 8. FL Client Implementation

### File Location
```
hospital_node/src/fl_trainer.py
```

### Flower Client Class

```python
class FlowerClient(fl.client.NumPyClient):
    """Flower client for hospital node"""
    
    def __init__(self, model, x_train, y_train, x_test, y_test):
        self.model = model
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
    
    def get_parameters(self, config):
        """Return current model parameters"""
        return self.model.get_weights()
    
    def fit(self, parameters, config):
        """Train model with provided parameters"""
        # Update model with global parameters
        self.model.set_weights(parameters)
        
        # Train locally
        history = self.model.fit(
            self.x_train,
            self.y_train,
            epochs=5,
            batch_size=32,
            validation_split=0.1
        )
        
        # Return updated parameters and metrics
        return self.model.get_weights(), len(self.x_train), {
            "accuracy": float(history.history["accuracy"][-1]),
            "loss": float(history.history["loss"][-1])
        }
    
    def evaluate(self, parameters, config):
        """Evaluate model with provided parameters"""
        # Update model
        self.model.set_weights(parameters)
        
        # Evaluate
        loss, accuracy = self.model.evaluate(self.x_test, self.y_test)
        
        return float(loss), len(self.x_test), {"accuracy": float(accuracy)}
```

---

## 9. Model Architecture

### TB Detection CNN

```python
def create_model():
    """Create CNN for TB detection"""
    model = tf.keras.Sequential([
        # Convolutional layers
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
        tf.keras.layers.MaxPooling2D((2, 2)),
        
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        
        tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        
        # Dense layers
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model
```

**Model Statistics:**
- **Total Parameters**: 56 arrays (~56.7 MB)
- **Trainable Parameters**: ~15 million
- **Input**: 224x224x3 RGB images
- **Output**: Binary classification (TB vs Normal)

---

## 10. Training Results

### Performance Progression

| Round | Accuracy | Loss | Improvement |
|-------|----------|------|-------------|
| 1 | 72.59% | 0.5842 | Baseline |
| 2 | 73.16% | 0.5693 | +0.57% |
| 3 | 96.98% | 0.1406 | +23.82% |
| 4 | 97.92% | 0.1054 | +0.94% |

**Key Insight**: Dramatic improvement in Round 3 suggests model found optimal features.

---

## 11. Key Files You Should Know

### FL Server Files
| File | Purpose | Your Contribution |
|------|---------|-------------------|
| `aggregator/src/flower_server.py` | Flower server | Complete implementation |
| `aggregator/src/main.py` | Server startup | Configured Flower launch |

### FL Client Files
| File | Purpose | Your Contribution |
|------|---------|-------------------|
| `hospital_node/src/fl_trainer.py` | Flower client | Complete implementation |
| `hospital_node/src/main.py` | Client startup | gRPC keepalive config |
| `hospital_node/src/tb_model.py` | CNN model | Model architecture |

---

## 12. Presentation Talking Points

### Opening (30 seconds)
"I implemented the Flower aggregator server and federated learning logic that coordinates training across hospitals without sharing patient data. The system uses Federated Averaging to combine model updates while preserving privacy."

### Technical Deep Dive (2 minutes)

**Federated Averaging:**
"We use FedAvg, which computes a weighted average of model parameters from each hospital. Hospitals with more training data have proportionally more influence on the global model. This is mathematically optimal and ensures fairness."

**Client Synchronization:**
"I solved a critical deadlock issue where the server requested parameters before clients connected. The solution was to explicitly wait for `min_available_clients` before requesting initial parameters."

**gRPC Keepalive:**
"Training rounds take 3-4 minutes, but gRPC was timing out after 22 minutes of inactivity. I configured keepalive to ping every 10 seconds, maintaining connections throughout the entire FL process."

**Round Timeout:**
"I increased the round timeout from 60 seconds to 600 seconds (10 minutes) to accommodate parameter transfer and training time. This prevents premature round failures."

### Demo Points
1. Show Flower server logs with client connections
2. Explain FedAvg formula with example calculation
3. Show training progression (72% → 97% accuracy)
4. Display gRPC keepalive configuration

### Closing (30 seconds)
"The FL system successfully trains a TB detection model across hospitals while maintaining data privacy. The model improved from 72% to 97% accuracy over 4 rounds, demonstrating the effectiveness of federated learning."

---

## 13. Common Questions & Answers

**Q: Why Federated Averaging instead of other algorithms?**
A: "FedAvg is the most widely used FL algorithm. It's simple, effective, and has strong theoretical guarantees. More complex algorithms like FedProx or FedNova could be explored for non-IID data."

**Q: How do you handle hospitals with different data distributions?**
A: "FedAvg uses weighted averaging based on dataset size. Hospitals with more data have more influence. For highly non-IID data, we could use techniques like FedProx or personalization layers."

**Q: What if a hospital drops out mid-round?**
A: "Flower handles this gracefully. If a client fails, the round continues with remaining clients. The `min_fit_clients` parameter ensures we have enough participants."

**Q: How do you prevent malicious hospitals from poisoning the model?**
A: "Currently, we trust all participants. For production, we'd implement Byzantine-robust aggregation, gradient clipping, or differential privacy to detect and mitigate attacks."

**Q: Can you add more hospitals dynamically?**
A: "Yes! Flower supports dynamic client joining. New hospitals can connect at any time and participate in subsequent rounds."

---

## Summary Checklist

Before presentation, make sure you can explain:
- ✅ What is Federated Learning and why for healthcare
- ✅ Flower framework and why we chose it
- ✅ FedAvg algorithm and mathematical formula
- ✅ Weighted averaging with example calculation
- ✅ Client synchronization fix (deadlock solution)
- ✅ gRPC keepalive configuration
- ✅ Round timeout increase (60s → 600s)
- ✅ FL training workflow (11 steps)
- ✅ Model architecture (CNN for TB detection)
- ✅ Training results (72% → 97% accuracy)
- ✅ File locations for all FL code
- ✅ How Flower handles client failures

**You've got this! 🚀**
