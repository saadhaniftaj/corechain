# Mahad's Final Panel Guide: Federated Learning & Aggregation

## Your Responsibility
**Flower Server, FedAvg Aggregation Algorithm, CNN Model Architecture, Hospital Client Training, and Multi-Hospital Synchronization**

You built the federated learning engine — the Flower server that coordinates training across multiple hospitals, aggregates model weights using Federated Averaging, and manages the complete training lifecycle from initial parameter distribution through 10 rounds of collaborative learning.

---

## 1. What is Federated Learning? (Elevator Pitch)

**"Bring the model to the data, not the data to the model."**

Multiple hospitals collaboratively train a TB detection AI model **without ever sharing patient X-ray images**. Each hospital trains locally, sends only numerical weight updates (not images), and the server averages them into a better global model. Raw data never leaves the hospital.

### Why FL for Healthcare?
| Concern | How FL Solves It |
|---------|-----------------|
| **Patient Privacy** | X-rays never leave hospital — only model weight numbers are shared |
| **GDPR/HIPAA** | Compliance by design — no personal data transmitted |
| **Data Diversity** | Learn from multiple hospital populations for better generalization |
| **Trust** | No hospital has to trust another — only the aggregator sees weights |

---

## 2. Technology Stack

| Technology | Version | Purpose |
|---|---|---|
| **Flower** | 1.6.0 | FL framework (server + client) |
| **TensorFlow** | 2.15.0 | CNN model training |
| **gRPC** | 1.48.2 | Flower's transport protocol |
| **NumPy** | 1.24.3 | Weight array manipulation |
| **Python** | 3.10 | Runtime |

### Key Files
```
aggregator/src/
├── flower_server.py     ← CoreChainStrategy (custom FedAvg) + reward calculation
├── main.py              ← Boots Flower server on :8080 in background thread

hospital_node/src/
├── fl_trainer.py        ← TBFlowerClient (fit, evaluate, get_parameters)
├── tb_model.py          ← CNN architecture definition
├── data_loader.py       ← X-ray dataset loading + synthetic data generator
├── main.py              ← Hospital boot sequence + Flower connection
```

---

## 3. Flower Server — `flower_server.py`

### CoreChainStrategy Class (Lines 24–208)

This extends Flower's built-in `FedAvg` strategy with custom logging:

```python
class CoreChainStrategy(FedAvg):
    def __init__(self, blockchain_client=None, websocket_server=None, **kwargs):
        super().__init__(**kwargs)
        self.blockchain_client = blockchain_client
        self.websocket_server = websocket_server
        self.current_round = 0
```

### Server Configuration (Lines 211–244)

```python
def create_flower_server(min_clients=2, num_rounds=10, ...):
    strategy = CoreChainStrategy(
        min_fit_clients=min_clients,        # Need 2 hospitals to start training
        min_evaluate_clients=min_clients,    # Need 2 hospitals to evaluate
        min_available_clients=min_clients,   # Wait for 2 before starting
        fraction_fit=1.0,                   # Use 100% of connected clients
        fraction_evaluate=1.0               # Evaluate on 100% of clients
    )
```

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `min_fit_clients` | 2 | Minimum hospitals to train per round |
| `min_evaluate_clients` | 2 | Minimum hospitals to evaluate per round |
| `min_available_clients` | 2 | Wait for 2 hospitals before starting ANY round |
| `fraction_fit` | 1.0 | Use all available hospitals (100%) |
| `fraction_evaluate` | 1.0 | Evaluate on all hospitals |
| `num_rounds` | 10 | Total FL training rounds |

### Starting the Server (Lines 247–277)

```python
def start_flower_server(server_address="0.0.0.0:8080", min_clients=2, num_rounds=10, ...):
    strategy, rounds = create_flower_server(min_clients, num_rounds, ...)
    
    fl.server.start_server(
        server_address=server_address,      # Listen on all interfaces, port 8080
        config=fl.server.ServerConfig(num_rounds=rounds),
        strategy=strategy
    )
    
    # After all rounds complete:
    if training_state:
        training_state['is_training'] = False
```

---

## 4. The FedAvg Algorithm — The Mathematical Heart

### The Formula

Given:
- **K** hospitals (2 in our demo: Alpha and Beta)
- **W_i** = model weight vector from hospital i (all layers flattened into arrays)
- **n_i** = number of training samples at hospital i
- **N** = total samples across all hospitals = Σn_i

**Federated Averaging:**

```
W_global = Σ(i=1 to K) (n_i / N) × W_i
```

**In words**: The new global model is a weighted average of all hospital models, where each hospital's influence is proportional to the amount of data it trained on.

### Why Weighted (Not Simple) Average?

A hospital with 1,000 samples has learned more than one with 100 samples. Weighting by dataset size ensures the global model isn't biased toward small, potentially noisy datasets.

### Example Calculation

**Setup:**
- Hospital Alpha: 8 training samples, accuracy = 0.75, weights = [0.4, 0.6, 0.8]
- Hospital Beta: 8 training samples, accuracy = 0.82, weights = [0.5, 0.7, 0.9]

**Step 1**: Total samples = 8 + 8 = 16

**Step 2**: Weights for averaging:
- Alpha weight = 8/16 = 0.5
- Beta weight = 8/16 = 0.5

**Step 3**: Weighted average per layer:
```
W_global[0] = 0.5 × 0.4 + 0.5 × 0.5 = 0.45
W_global[1] = 0.5 × 0.6 + 0.5 × 0.7 = 0.65
W_global[2] = 0.5 × 0.8 + 0.5 × 0.9 = 0.85
```

**Result**: Global model = [0.45, 0.65, 0.85] — a blend of both hospitals' knowledge.

### Actual Code: `aggregate_fit()` (Lines 40–140)

```python
def aggregate_fit(self, server_round, results, failures):
    self.current_round = server_round
    
    # Step 1: Flower's FedAvg does the actual weight averaging
    aggregated_parameters, aggregated_metrics = super().aggregate_fit(
        server_round, results, failures
    )
    
    # Step 2: Calculate global metrics (weighted by sample count)
    total_examples = sum([fit_res.num_examples for _, fit_res in results])
    
    weighted_accuracy = sum([
        fit_res.metrics.get('accuracy', 0.0) * fit_res.num_examples
        for _, fit_res in results
    ]) / total_examples
    
    weighted_loss = sum([
        fit_res.metrics.get('loss', 0.0) * fit_res.num_examples
        for _, fit_res in results
    ]) / total_examples
    
    # Step 3: Log to blockchain
    if self.blockchain_client:
        # Log each hospital's model update
        for client, fit_res in results:
            self.blockchain_client.log_transaction({
                'type': 'MODEL_UPDATE',
                'hospital_id': str(client.cid),
                'round': server_round,
                'accuracy': fit_res.metrics.get('accuracy', 0.0),
                'loss': fit_res.metrics.get('loss', 0.0),
                'samples_trained': fit_res.num_examples
            })
        
        # Log the aggregation event
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
                'reward_tokens': reward
            })
    
    # Step 4: Update shared dashboard state
    if training_state:
        training_state['current_round'] = server_round
        training_state['global_accuracy'] = weighted_accuracy
        training_state['global_loss'] = weighted_loss
        training_state['is_training'] = True
        training_state['accuracy_history'].append(weighted_accuracy)
        training_state['loss_history'].append(weighted_loss)
    
    return aggregated_parameters, aggregated_metrics
```

### Reward Calculation (Lines 191–208)

```python
def _calculate_reward(self, accuracy, samples, total_samples):
    base_reward = 10.0
    accuracy_bonus = accuracy * 5.0
    sample_bonus = (samples / total_samples) * 5.0 if total_samples > 0 else 0.0
    
    reward = base_reward + accuracy_bonus + sample_bonus
    
    if accuracy > 0.9:
        reward *= 1.2   # Quality multiplier
    
    return round(reward, 2)
```

---

## 5. Hospital Client — `fl_trainer.py`

### TBFlowerClient Class (Lines 16–130)

```python
class TBFlowerClient(fl.client.NumPyClient):
    def __init__(self, hospital_id, model, x_train, y_train, x_test, y_test,
                 local_epochs=5, batch_size=32):
        self.hospital_id = hospital_id
        self.model = model          # TBDetectionModel instance
        self.x_train = x_train      # Training images (NumPy)
        self.y_train = y_train      # Training labels (0=normal, 1=TB)
        self.x_test = x_test        # Test images
        self.y_test = y_test        # Test labels
```

### Three Core Methods

**1. `get_parameters()` — Send current weights to server**
```python
def get_parameters(self, config):
    return self.model.get_weights()   # Returns list of NumPy arrays
```

**2. `fit()` — Receive global weights, train locally, return updated weights**
```python
def fit(self, parameters, config):
    # Step 1: Replace local weights with global weights
    self.model.set_weights(parameters)
    
    # Step 2: Train locally for 5 epochs
    history = self.model.fit(
        self.x_train, self.y_train,
        epochs=self.local_epochs,       # 5
        batch_size=self.batch_size,     # 32
        validation_split=0.1
    )
    
    # Step 3: Return updated weights + metrics
    accuracy = float(history.history["accuracy"][-1])
    loss = float(history.history["loss"][-1])
    
    return self.model.get_weights(), len(self.x_train), {
        "accuracy": accuracy,
        "loss": loss
    }
```

**3. `evaluate()` — Evaluate global model on local test data**
```python
def evaluate(self, parameters, config):
    self.model.set_weights(parameters)
    loss, accuracy = self.model.evaluate(self.x_test, self.y_test)
    return float(loss), len(self.x_test), {"accuracy": float(accuracy)}
```

---

## 6. CNN Model — `tb_model.py`

### Architecture

```
Input: (224, 224, 1)  ← Grayscale chest X-ray

Conv2D(32, 3×3, ReLU) → MaxPool2D(2×2)     → 112×112×32
Conv2D(64, 3×3, ReLU) → MaxPool2D(2×2)     → 56×56×64
Conv2D(128, 3×3, ReLU) → MaxPool2D(2×2)    → 28×28×128
Flatten                                      → 100,352
Dense(256, ReLU) → Dropout(0.5)             → 256
Dense(1, Sigmoid)                           → P(TB positive)
```

| Layer | Parameters | Purpose |
|-------|-----------|---------|
| Conv2D(32) | 320 | Edge/texture detection |
| Conv2D(64) | 18,496 | Shape/pattern detection |
| Conv2D(128) | 73,856 | High-level feature detection |
| Dense(256) | 25,690,368 | Classification reasoning |
| Dense(1) | 257 | Binary output (TB yes/no) |

**Loss**: Binary Cross-Entropy: `L = -[y·log(ŷ) + (1-y)·log(1-ŷ)]`  
**Optimizer**: Adam (lr=0.001)  
**Output**: Probability 0–1 (threshold 0.5 → TB positive)

---

## 7. Complete Training Round Lifecycle

```
Round N begins
    │
    ├── Server sends global weights W_global to all hospitals (via gRPC :8080)
    │
    ├── Hospital Alpha receives W_global
    │   ├── Sets local model weights = W_global
    │   ├── Trains on Shenzhen dataset (5 epochs, batch_size=32)
    │   ├── Sends back W_alpha + {accuracy, loss, num_examples}
    │   └── ~10-30 seconds per round (synthetic data)
    │
    ├── Hospital Beta receives W_global (simultaneously)
    │   ├── Same process with Montgomery dataset
    │   └── Sends back W_beta + metrics
    │
    ├── Server aggregate_fit() fires:
    │   ├── FedAvg: W_new = (n_α/N)·W_α + (n_β/N)·W_β
    │   ├── Logs MODEL_UPDATE × 2 to blockchain
    │   ├── Logs MODEL_AGGREGATION to blockchain
    │   ├── Calculates rewards for each hospital
    │   └── Logs REWARD_DISTRIBUTION × 2 to blockchain
    │
    ├── Server aggregate_evaluate() fires:
    │   ├── Each hospital evaluates the new global model on test data
    │   └── Updates training_state with global accuracy/loss
    │
    └── Dashboard updates: charts, progress bar, leaderboard
    
Round N+1 begins...
```

---

## 8. Hospital Synchronization — The Retry Pattern

### The Problem We Solved

The original code had a blocking TCP check (`wait_for_aggregator`) that waited up to 120 seconds for port 8080 to be reachable before even attempting to connect. With `MIN_CLIENTS=2`, this caused a deadlock:
- Flower server waits for 2 hospitals before binding port 8080
- Hospitals wait for port 8080 before connecting
- Nobody connects → nothing starts

### The Solution (hospital_node/src/main.py)

```python
# Old (BROKEN):
if not wait_for_aggregator(aggregator_ip, flower_port, timeout=120):
    logger.warning("Not reachable after 120s")

# New (FIXED): Retry loop that goes straight to Flower connection
while True:
    try:
        logger.info(f"Connecting to Flower at {flower_server_address}...")
        fl.client.start_numpy_client(
            server_address=flower_server_address,
            client=flower_client
        )
        logger.success("Flower round complete")
        break
    except Exception as e:
        logger.warning(f"Not ready yet: {e} — retrying in 5s")
        time.sleep(5)
```

This ensures both hospitals continuously attempt to connect until the Flower server is ready, eliminating the race condition.

---

## 9. Presentation Talking Points

### Opening (30 seconds)
"I implemented the federated learning engine using the Flower framework. The system coordinates training across multiple hospital nodes using Federated Averaging — each hospital trains locally on its private data, and I aggregate their model weights proportionally to create a superior global model, all without any patient data leaving the hospital."

### Technical Deep Dive (3 minutes)

**The Algorithm:**
"Federated Averaging computes a weighted average of model parameters: W_global = Σ(n_i/N) × W_i. Hospitals with more training data have proportionally more influence on the global model. This is mathematically equivalent to training on the combined dataset — but without actually combining the data."

**The Training Loop:**
"Each round, the server sends global weights to all hospitals. Each hospital replaces its local weights, trains for 5 epochs on its local dataset, then sends back the updated weights plus accuracy and loss metrics. The server aggregates using FedAvg, logs everything to the blockchain, calculates rewards, and starts the next round."

**The CNN:**
"The model is a 3-layer CNN with 128 filters, followed by Dense layers with 50% dropout. It takes 224×224 grayscale X-ray images and outputs a binary TB probability. The architecture is intentionally lightweight for federated training on constrained hardware."

**The Synchronization Fix:**
"We solved a critical deadlock: the Flower server needs N clients before binding its port, but clients were waiting for the port before connecting. I replaced the blocking TCP wait with a resilient retry loop that continuously attempts Flower connection every 5 seconds."

### Live Demo Points
1. Open `http://54.91.23.82/` → show 2 hospitals connected
2. Click "Accuracy" tab → show accuracy improving over rounds
3. Click "Loss" tab → show loss decreasing
4. Show aggregator logs: `docker logs corechain_aggregator --tail 20` → see FedAvg metrics
5. Walk through `flower_server.py` aggregate_fit() — show the weighted average calculation

---

## 10. Panel Q&A Preparation

**Q: Why FedAvg instead of FedProx or another algorithm?**
A: "FedAvg is the foundational FL algorithm — it's simple, well-understood, and has strong convergence guarantees. For our balanced dataset scenario (both hospitals have similar data sizes), FedAvg performs optimally. FedProx adds a proximal term for highly non-IID data, which we don't need in our demo."

**Q: What happens if a hospital drops mid-round?**
A: "Flower handles this gracefully. If a client fails during `fit()`, the round continues with remaining clients as long as `min_fit_clients` is satisfied. The failed client's weights are simply excluded from that round's aggregation."

**Q: How do you prevent a hospital from poisoning the model?**
A: "Currently we trust participants — this is a demo. For production, we'd add Byzantine-robust aggregation (like Krum or Trimmed Mean) that detects and excludes outlier weight updates. The blockchain audit trail also allows post-hoc analysis of suspicious contributions."

**Q: Why 10 rounds? Could you do more?**
A: "10 rounds is sufficient to demonstrate convergence. Each additional round yields diminishing returns as the model approaches its accuracy ceiling. In production, you'd use early stopping — halt when accuracy improvement drops below a threshold."

**Q: What's the communication cost per round?**
A: "The CNN has approximately 25 million parameters. Each parameter is a 32-bit float, so one set of weights is about 100MB uncompressed. Flower uses gRPC with Protocol Buffers, which provides efficient binary serialization, reducing actual transfer size."

---

## 11. Key Code References

| What to show | File | Lines | Key detail |
|---|---|---|---|
| FedAvg aggregation | `aggregator/src/flower_server.py` | 40–140 | `aggregate_fit()` |
| Reward calculation | `aggregator/src/flower_server.py` | 191–208 | `_calculate_reward()` |
| Server config | `aggregator/src/flower_server.py` | 211–244 | `create_flower_server()` |
| Server startup | `aggregator/src/flower_server.py` | 247–277 | `start_flower_server()` |
| Flower client fit() | `hospital_node/src/fl_trainer.py` | 46–90 | `TBFlowerClient.fit()` |
| Flower client evaluate() | `hospital_node/src/fl_trainer.py` | 92–110 | `evaluate()` |
| CNN architecture | `hospital_node/src/tb_model.py` | 30–73 | `_build_model()` |
| Retry sync fix | `hospital_node/src/main.py` | 55–68 | `while True` retry loop |
| Data loader | `hospital_node/src/data_loader.py` | 117–169 | `_create_synthetic_data()` |
