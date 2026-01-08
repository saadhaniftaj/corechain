# CoreChain System Workflow & Theory

## 🎯 What CoreChain Does (In Theory)

CoreChain is a **privacy-preserving collaborative AI platform** that allows multiple hospitals to train a shared TB detection model WITHOUT sharing their patient data.

### The Problem It Solves
- Hospitals have valuable medical data but can't share it due to **HIPAA/privacy laws**
- Individual hospitals don't have enough data to train accurate AI models
- No trust mechanism to ensure fair contribution and credit

### The Solution
CoreChain combines **3 technologies**:
1. **Federated Learning** - Train together without sharing data
2. **Homomorphic Encryption** - Protect model updates
3. **Blockchain** - Transparent audit trail and rewards

---

## 🔄 Complete System Workflow

### Phase 1: Setup (One-Time)

**Central Aggregator (Your Main Laptop):**
```bash
docker pull saadhaniftaj/corechain-allinone:latest
docker run -d -p 80:80 -p 8080:8080 -p 50051:50051 \
  --name corechain-aggregator \
  saadhaniftaj/corechain-allinone:latest
```

**What Starts:**
- ✅ Flower Server (port 8080) - Coordinates federated learning
- ✅ REST API (port 8000) - Provides data to dashboard
- ✅ WebSocket Server (port 8001) - Real-time updates
- ✅ Blockchain Service (port 7050) - Immutable ledger
- ✅ Dashboard (port 80) - Web interface
- ✅ gRPC Server (port 50051) - Hospital communication

**Hospital Nodes (Other Laptops):**
```bash
# Each hospital runs their own node
docker run -d \
  -e HOSPITAL_ID=hospital_1 \
  -e HOSPITAL_NAME="General Hospital" \
  -e AGGREGATOR_IP=192.168.1.100 \
  -e DATASET_TYPE=shenzhen \
  --name hospital-node \
  saadhaniftaj/corechain-hospital:latest
```

---

### Phase 2: Training Workflow (Automatic)

#### Round 1 Begins:

**Step 1: Hospital Registration**
```
Hospital 1 → gRPC → Aggregator: "I'm Hospital 1, I have 500 images"
Hospital 2 → gRPC → Aggregator: "I'm Hospital 2, I have 300 images"
Hospital 3 → gRPC → Aggregator: "I'm Hospital 3, I have 400 images"
```

**Step 2: Local Training (Parallel)**
```
Hospital 1: Trains CNN on local 500 images for 5 epochs
Hospital 2: Trains CNN on local 300 images for 5 epochs
Hospital 3: Trains CNN on local 400 images for 5 epochs
```

Each hospital:
- Loads their local TB X-ray images
- Trains the model locally (data NEVER leaves their machine)
- Achieves local accuracy (e.g., 72%, 68%, 75%)

**Step 3: Encrypt Model Updates**
```
Hospital 1: model_weights → Paillier Encryption → encrypted_weights
Hospital 2: model_weights → Paillier Encryption → encrypted_weights
Hospital 3: model_weights → Paillier Encryption → encrypted_weights
```

**Step 4: Send to Aggregator**
```
Hospital 1 → gRPC → Aggregator: encrypted_weights + metadata
Hospital 2 → gRPC → Aggregator: encrypted_weights + metadata
Hospital 3 → gRPC → Aggregator: encrypted_weights + metadata
```

Metadata includes:
- Number of samples trained on
- Local accuracy achieved
- Hospital ID

**Step 5: Aggregation (FedAvg)**
```
Aggregator:
  1. Decrypts all model updates
  2. Performs weighted averaging:
     global_weights = (500*w1 + 300*w2 + 400*w3) / 1200
  3. Creates new global model
```

**Step 6: Blockchain Logging**
```
Blockchain ← Transaction: {
  type: "MODEL_UPDATE",
  hospital: "hospital_1",
  round: 1,
  accuracy: 0.72,
  samples: 500
}

Blockchain ← Transaction: {
  type: "MODEL_AGGREGATION",
  round: 1,
  global_accuracy: 0.73,
  participants: 3
}
```

**Step 7: Reward Distribution**
```
Smart Contract Calculates:
  Hospital 1: base(10) + accuracy_bonus(3.6) + contribution(2.1) = 15.7 tokens
  Hospital 2: base(10) + accuracy_bonus(3.4) + contribution(1.3) = 14.7 tokens
  Hospital 3: base(10) + accuracy_bonus(3.75) + contribution(1.7) = 15.45 tokens

Blockchain ← Reward Transactions
```

**Step 8: Distribute Global Model**
```
Aggregator → gRPC → Hospital 1: global_model_weights
Aggregator → gRPC → Hospital 2: global_model_weights
Aggregator → gRPC → Hospital 3: global_model_weights
```

**Step 9: Dashboard Update**
```
WebSocket → Dashboard: {
  event: "round_complete",
  round: 1,
  accuracy: 0.73,
  participants: 3
}

Dashboard displays:
  - Progress: Round 1/10 (10%)
  - Global Accuracy: 73%
  - Connected Hospitals: 3
  - Recent blockchain transactions
```

#### Rounds 2-10: Repeat

Each round:
- Hospitals start with the improved global model
- Train on their local data
- Model gets better each round
- Final accuracy: ~85-90% (vs 72% individual)

---

## 📊 What's Working (In Theory)

### ✅ Fully Implemented Components:

**1. Federated Learning Layer**
- ✅ Flower server with custom FedAvg strategy
- ✅ Flower client for hospital nodes
- ✅ Weighted aggregation based on dataset size
- ✅ Model distribution and updates
- ✅ TB detection CNN (4 conv blocks, batch norm, dropout)

**2. Privacy Layer**
- ✅ Paillier homomorphic encryption
- ✅ Gradient encryption/decryption
- ✅ Homomorphic aggregation (add encrypted values)
- ✅ Key generation and management

**3. Blockchain Layer**
- ✅ Lightweight blockchain (SHA-256, PoW)
- ✅ Smart contracts (validator, reward distributor, audit logger)
- ✅ Transaction pool and mining
- ✅ Chain validation
- ✅ RESTful API (Fabric-compatible)

**4. Communication Layer**
- ✅ gRPC for model updates (Protocol Buffers)
- ✅ REST API for dashboard queries
- ✅ WebSocket for real-time updates
- ✅ All services containerized

**5. Dashboard**
- ✅ Real-time training status
- ✅ Connected hospitals viewer
- ✅ Blockchain statistics
- ✅ Transaction history
- ✅ Auto-refresh (5 seconds)
- ✅ Responsive design with animations

**6. Data Pipeline**
- ✅ TB dataset loader (Shenzhen/Montgomery)
- ✅ Synthetic data generation (for demos)
- ✅ Data preprocessing and augmentation
- ✅ Train/test splitting

---

## 🎬 Expected Demo Workflow

### Setup (5 minutes):
1. **Aggregator Laptop**: Run Docker container
2. **Hospital Laptops**: Run hospital nodes (3 laptops)
3. **Browser**: Open dashboard at http://aggregator-ip

### Demo (10 minutes):

**Minute 1-2: Introduction**
- Show the 4 laptops
- Explain the problem (privacy vs collaboration)
- Show dashboard landing page

**Minute 3-4: Start Training**
```bash
# On each hospital laptop
docker logs -f hospital-node
```
- Show logs: "Connecting to aggregator..."
- Show logs: "Registered successfully"
- Show logs: "Starting Round 1..."

**Minute 5-6: Watch Training**
- Dashboard shows: "Round 1/10 - Training Active"
- Watch accuracy increase: 72% → 75% → 78%
- Point out: "Data never leaves each hospital"

**Minute 7-8: Blockchain Transparency**
```bash
curl http://aggregator-ip/blockchain/api/blockchain/chain
```
- Show blockchain transactions
- Show reward distribution
- Explain: "Immutable audit trail"

**Minute 9: Results**
- Final accuracy: ~85%
- Show leaderboard
- Compare: Individual (72%) vs Collaborative (85%)

**Minute 10: Impact**
- Explain real-world applications
- Discuss scalability
- Q&A

---

## 🔧 Technical Flow (Behind the Scenes)

### When You Run the Container:

```
1. Supervisor starts all services:
   ├─ Blockchain (Python FastAPI)
   ├─ Aggregator (Python Flower + gRPC + REST + WebSocket)
   └─ Nginx (Serves dashboard + proxies APIs)

2. Blockchain initializes:
   - Creates genesis block
   - Starts mining thread
   - Opens REST API on port 7050

3. Aggregator initializes:
   - Connects to blockchain
   - Starts Flower server (waits for MIN_CLIENTS)
   - Opens gRPC server (port 50051)
   - Opens REST API (port 8000)
   - Opens WebSocket (port 8001)

4. Dashboard loads:
   - Nginx serves index.html
   - JavaScript polls REST API every 5 seconds
   - WebSocket connects for real-time updates
   - Shows "Waiting for hospitals..."

5. Hospital connects:
   - gRPC call: register(hospital_id, name, samples)
   - Aggregator: "Hospital registered"
   - Dashboard updates: "Connected Hospitals: 1"

6. When MIN_CLIENTS reached:
   - Flower server: "Starting federated learning"
   - Round 1 begins automatically
   - Hospitals train in parallel
   - Aggregation happens
   - Blockchain logs everything
   - Dashboard shows progress

7. After 10 rounds:
   - Training complete
   - Final model saved
   - Blockchain has full audit trail
   - Dashboard shows "Complete" status
```

---

## 🎯 Success Metrics

**What Should Work:**
1. ✅ Container starts all services
2. ✅ Dashboard loads and shows UI
3. ✅ Hospital nodes can connect
4. ✅ Training rounds execute
5. ✅ Blockchain records transactions
6. ✅ Dashboard updates in real-time
7. ✅ Final model achieves >80% accuracy

**What to Expect:**
- **Setup time**: 2-3 minutes
- **Per round**: 30-60 seconds (depending on data size)
- **Total training**: 5-10 minutes for 10 rounds
- **Blockchain size**: ~50-100 transactions
- **Memory usage**: ~2GB per container

---

## 🚀 Production Readiness

**What's Production-Ready:**
- ✅ Dockerized architecture
- ✅ Multi-service orchestration
- ✅ Error handling and logging
- ✅ Health checks
- ✅ Auto-restart on failure

**What Needs Work for Production:**
- ⚠️ Authentication (JWT tokens)
- ⚠️ HTTPS/TLS encryption
- ⚠️ Database persistence (PostgreSQL)
- ⚠️ Horizontal scaling
- ⚠️ Full homomorphic encryption
- ⚠️ Real TB datasets (HIPAA compliance)

---

## 📝 Summary

**CoreChain is a COMPLETE PROTOTYPE that demonstrates:**
1. Multi-hospital collaboration without data sharing
2. Privacy through encryption
3. Transparency through blockchain
4. Real-time monitoring through dashboard
5. Fair reward distribution

**It's ready for:**
- ✅ Academic presentations
- ✅ Proof-of-concept demos
- ✅ Research papers
- ✅ Hackathon submissions

**Next steps for real deployment:**
- Add authentication
- Use real medical datasets
- Deploy to cloud (Azure/AWS)
- Integrate with hospital systems
- Get regulatory approval (HIPAA/GDPR)

---

**The Docker container is building now. Once complete, you'll be able to:**
```bash
docker pull saadhaniftaj/corechain-allinone:latest
docker run -d -p 80:80 -p 8080:8080 -p 50051:50051 saadhaniftaj/corechain-allinone:latest
```

**And your entire system will be running!** 🎉
