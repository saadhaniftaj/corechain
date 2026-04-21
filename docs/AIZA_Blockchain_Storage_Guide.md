# Aiza's Final Panel Guide: Blockchain & Storage Architecture

## Your Responsibility
**Blockchain Immutable Audit Trail, Smart Contract Validation, Reward Distribution, and Data Persistence**

You built CoreChain's custom Python blockchain that records every FL event — hospital registrations, model updates, weight aggregations, and token rewards — as an immutable, tamper-proof audit trail with Proof-of-Work consensus.

---

## 1. Blockchain Architecture Overview

### Technology Stack (ACTUAL — NOT Ethereum/Ganache)

| Technology | Purpose | Why |
|---|---|---|
| **Custom Python Blockchain** | Immutable ledger | Full control, lightweight, no external deps |
| **SHA-256 Proof-of-Work** | Consensus mechanism | Tamper-proof blocks |
| **FastAPI (port 7050)** | Blockchain REST API | Dashboard + aggregator integration |
| **JSON Persistence** | Block storage | Survives container restarts |
| **Smart Contracts (Python)** | Validation + rewards | Business logic enforcement |

> **CRITICAL**: We do NOT use Ethereum or Ganache. The old docs were wrong. We built a **custom lightweight blockchain from scratch in Python** — this is actually more impressive to explain because you built it yourself rather than using a pre-built platform.

### Directory Structure
```
blockchain/
├── src/
│   ├── main.py                 ← Entry point (starts API on port 7050)
│   ├── blockchain_core.py      ← Block + Blockchain classes (PoW mining)
│   ├── fabric_api.py           ← FastAPI REST endpoints (17 routes)
│   └── smart_contracts.py      ← ModelUpdateValidator, RewardDistributor, AuditLogger
├── requirements.txt
└── Dockerfile
```

---

## 2. Blockchain Core — `blockchain_core.py`

### The Block Class (Lines 14–63)

Every block contains:

```python
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index              # Block position in chain (0, 1, 2...)
        self.timestamp = timestamp      # ISO-8601 datetime
        self.transactions = transactions # List of transaction dicts
        self.previous_hash = previous_hash # Hash of the previous block
        self.nonce = nonce              # Proof-of-Work counter
        self.hash = self.calculate_hash()  # SHA-256 of everything above
```

### Hash Calculation (Lines 32–42)
```python
def calculate_hash(self) -> str:
    block_string = json.dumps({
        'index': self.index,
        'timestamp': self.timestamp,
        'transactions': self.transactions,
        'previous_hash': self.previous_hash,
        'nonce': self.nonce
    }, sort_keys=True)
    return hashlib.sha256(block_string.encode()).hexdigest()
```

**Why `sort_keys=True`?** Ensures deterministic serialization — without it, different key orderings would produce different hashes for identical data.

### Proof-of-Work Mining (Lines 44–52)
```python
def mine_block(self, difficulty: int):
    target = '0' * difficulty   # e.g., difficulty=4 → target = "0000"
    while self.hash[:difficulty] != target:
        self.nonce += 1
        self.hash = self.calculate_hash()
```

**How it works**: The miner increments `nonce` from 0 upward, recalculating the hash each time, until the hash starts with 4 zeros (`0000...`). This requires ~65,536 attempts on average (16⁴). Finding such a hash is computationally expensive but verifying it is instant — this asymmetry is the foundation of blockchain security.

**Example mined block hash**: `0000a7f3b2c1d4e5...` ← starts with 4 zeros

### The Blockchain Class (Lines 66–264)

```python
class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []                    # List of Block objects
        self.pending_transactions = []     # Tx pool (unmined)
        self.difficulty = 4                # PoW difficulty
        self._create_genesis_block()       # Block #0
```

#### Genesis Block (Lines 80–95)
The first block has no predecessor:
```python
def _create_genesis_block(self):
    genesis_block = Block(
        index=0,
        timestamp=datetime.now().isoformat(),
        transactions=[{
            'type': 'GENESIS',
            'message': 'CoreChain Genesis Block'
        }],
        previous_hash='0'   # No previous block
    )
    genesis_block.mine_block(self.difficulty)  # Mine it
    self.chain.append(genesis_block)
```

#### Transaction Pool & Auto-Mining (Lines 101–118)
```python
def add_transaction(self, transaction):
    self.pending_transactions.append(transaction)
    
    # Auto-mine when 5 transactions accumulate
    if len(self.pending_transactions) >= 5:
        self.mine_pending_transactions()
    
    # Return SHA-256 hash of the transaction as receipt
    tx_hash = hashlib.sha256(
        json.dumps(transaction, sort_keys=True).encode()
    ).hexdigest()
    return tx_hash
```

#### Chain Validation (Lines 146–167)
Three integrity checks per block:
```python
def is_chain_valid(self):
    for i in range(1, len(self.chain)):
        current = self.chain[i]
        previous = self.chain[i - 1]
        
        # 1. Hash integrity — recalculate and compare
        if current.hash != current.calculate_hash():
            return False  # Block data was tampered
        
        # 2. Chain linkage — previous_hash must match
        if current.previous_hash != previous.hash:
            return False  # Chain was broken/reordered
        
        # 3. Proof-of-Work — hash must start with 0000
        if not current.hash.startswith('0' * self.difficulty):
            return False  # PoW was faked
    
    return True
```

**Why this matters for the panel**: If anyone modifies even a single byte in Block #3, its hash changes, which breaks Block #4's `previous_hash` pointer, which cascades and invalidates every subsequent block. This is how immutability works.

---

## 3. Smart Contracts — `smart_contracts.py`

### 3.1 ModelUpdateValidator (Lines 22–71)

Validates every hospital model submission before it's accepted:

```python
class ModelUpdateValidator(SmartContract):
    def execute(self, update_data):
        # Check 1: Required fields exist
        for field in ['hospital_id', 'round', 'accuracy', 'samples_trained']:
            if field not in update_data:
                return False, f"Missing: {field}"
        
        # Check 2: Hospital is registered on-chain
        registrations = self.blockchain.get_transactions_by_type('HOSPITAL_REGISTRATION')
        if not any(reg['hospital_id'] == hospital_id for reg in registrations):
            return False, "Hospital not registered"
        
        # Check 3: Accuracy is in valid range [0.0, 1.0]
        if not (0.0 <= accuracy <= 1.0):
            return False, "Invalid accuracy"
        
        # Check 4: No duplicate submissions per round
        existing = [tx for tx in self.blockchain.get_transactions_by_hospital(hospital_id)
                     if tx.get('type') == 'MODEL_UPDATE' and tx.get('round') == round_num]
        if existing:
            return False, "Duplicate submission"
        
        return True, "Validation successful"
```

### 3.2 RewardDistributor (Lines 74–168)

**The exact reward formula** (this is what appears on the dashboard leaderboard):

```python
def execute(self, hospital_id, round_num, accuracy, samples_contributed, total_samples):
    # Step 1: Base reward (flat fee for participating)
    reward = 10.0
    
    # Step 2: Accuracy bonus (0–5 tokens)
    accuracy_bonus = accuracy * 5.0     # e.g., 0.85 accuracy → 4.25 tokens
    reward += accuracy_bonus
    
    # Step 3: Sample contribution bonus (0–5 tokens)
    contribution_ratio = samples_contributed / total_samples
    sample_bonus = contribution_ratio * 5.0  # e.g., 600/1000 → 3.0 tokens
    reward += sample_bonus
    
    # Step 4: Quality multiplier (>90% accuracy → 1.2x)
    if accuracy > 0.9:
        reward *= 1.2
    
    return round(reward, 2)
```

**Full formula**:
```
reward = (base + accuracy_bonus + sample_bonus) × quality_multiplier

Where:
  base            = 10.0 tokens
  accuracy_bonus  = local_accuracy × 5.0
  sample_bonus    = (hospital_samples / total_samples) × 5.0
  quality_mult    = 1.2 if accuracy > 0.9, else 1.0
```

**Example**: Hospital Alpha with 85% accuracy, contributed 600 out of 1000 total samples:
```
= (10.0 + 0.85×5.0 + 0.6×5.0) × 1.0
= (10.0 + 4.25 + 3.0) × 1.0
= 17.25 tokens
```

### 3.3 AuditLogger (Lines 171–277)

Records every event immutably and provides queryable audit trail:

```python
class AuditLogger(SmartContract):
    def execute(self, event_type, event_data):
        transaction = {'type': event_type, **event_data, 'timestamp': datetime.now().isoformat()}
        return self.blockchain.add_transaction(transaction)
    
    def get_audit_trail(self, hospital_id=None, event_type=None, limit=100):
        # Filters: by hospital, by event type, with pagination
        
    def get_training_summary(self):
        # Returns: total_rounds, total_updates, participating_hospitals,
        #          avg_accuracy, best_accuracy, latest_global_accuracy
```

---

## 4. Blockchain REST API — `fabric_api.py`

17 endpoints running on **port 7050** inside the blockchain container:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/blockchain/transaction` | Submit new transaction |
| `POST` | `/api/blockchain/mine` | Manually trigger mining |
| `GET` | `/api/blockchain/chain` | Get entire chain |
| `GET` | `/api/blockchain/block/{index}` | Get specific block |
| `GET` | `/api/blockchain/validate` | Validate chain integrity |
| `GET` | `/api/blockchain/stats` | Get blockchain statistics |
| `GET` | `/api/blockchain/transactions` | Get all transactions (newest first) |
| `GET` | `/api/blockchain/transactions/type/{type}` | Filter by transaction type |
| `GET` | `/api/blockchain/hospital/{id}/transactions` | Get hospital's transactions |
| `GET` | `/api/blockchain/hospital/{id}/rewards` | Get hospital's total rewards |
| `GET` | `/api/blockchain/leaderboard` | Hospital ranking by rewards |
| `GET` | `/api/blockchain/audit` | Queryable audit trail |
| `GET` | `/api/blockchain/training/summary` | Training activity summary |
| `POST` | `/api/blockchain/validate/update` | Validate model update via smart contract |

### How the Dashboard Accesses the Blockchain

The dashboard (browser) can't directly hit port 7050 (firewall). Instead, NGINX proxies it:

```
Browser → http://54.91.23.82/blockchain-api/stats
         ↓ NGINX reverse proxy
NGINX  → http://127.0.0.1:7050/stats
         ↓
Blockchain API → returns stats JSON
```

Configured in `dashboard/nginx.conf` lines 49–53:
```nginx
location /blockchain-api/ {
    proxy_pass http://127.0.0.1:7050/;
}
```

---

## 5. Transaction Types & Data Flow

### Every transaction type that flows through the blockchain:

| Type | Triggered When | Data Recorded | Logged By |
|------|---------------|---------------|-----------|
| `GENESIS` | Chain creation | Genesis message | Blockchain init |
| `HOSPITAL_REGISTRATION` | Hospital connects via gRPC | hospital_id, name, dataset_size, dataset_type | grpc_server.py |
| `MODEL_UPDATE` | Hospital sends trained weights | hospital_id, round, accuracy, loss, samples_trained | flower_server.py |
| `MODEL_AGGREGATION` | Server aggregates all weights | round, global_accuracy, global_loss, participants, total_samples | flower_server.py |
| `REWARD_DISTRIBUTION` | After aggregation | hospital_id, round, reward_tokens, accuracy, samples_contributed | flower_server.py |

### Complete Data Flow for One Training Round

```
Hospital Alpha trains locally
    ↓
Sends weights + metrics to Flower server
    ↓
flower_server.py aggregate_fit() fires:
    ├── Logs MODEL_UPDATE to blockchain (per hospital)
    ├── Runs FedAvg aggregation
    ├── Logs MODEL_AGGREGATION to blockchain
    ├── Calculates reward via _calculate_reward()
    └── Logs REWARD_DISTRIBUTION to blockchain (per hospital)
    ↓
Blockchain auto-mines when 5 transactions accumulate
    ↓
Dashboard polls /blockchain-api/stats → displays live count
Dashboard polls /api/blockchain/transactions → shows audit trail
```

---

## 6. Data Persistence Architecture

### What Gets Persisted Where

| Data | Location | Format | Persistence |
|------|----------|--------|-------------|
| Blockchain chain | `/app/data/blockchain.json` | JSON | ✅ Saved on shutdown, loaded on startup |
| X-ray dataset | `/data/` (Docker volume) | Synthetic NumPy arrays | ✅ Generated on boot |
| Training state | In-memory (`training_state` dict) | Python dict | ❌ Lost on restart |
| Model weights | In-memory (Flower) | NumPy arrays | ❌ Lost on restart |
| Hospital registry | In-memory (`registered_hospitals`) | Python dict | ❌ But reconstructable from blockchain |

### Blockchain File Persistence (fabric_api.py lines 61–80)

```python
@app.on_event("startup")
async def startup_event():
    blockchain.load_from_file('/app/data/blockchain.json')  # Restore chain

@app.on_event("shutdown")
async def shutdown_event():
    blockchain.save_to_file('/app/data/blockchain.json')    # Persist chain
```

---

## 7. Presentation Talking Points

### Opening (30 seconds)
"I built CoreChain's custom blockchain from scratch in Python — not using Ethereum or any third-party platform. Every federated learning event is permanently recorded with SHA-256 Proof-of-Work consensus, creating an immutable audit trail that no single party can manipulate."

### Technical Deep Dive (3 minutes)

**Blockchain Design:**
"Each block contains a list of transactions, a SHA-256 hash, and a pointer to the previous block's hash. Mining requires finding a nonce that makes the block hash start with four zeros — this takes roughly 65,000 iterations on average and makes tampering computationally infeasible."

**Smart Contracts:**
"I implemented three smart contracts in Python:
1. **ModelUpdateValidator** — validates every hospital submission (checks registration, accuracy range, prevents duplicates)
2. **RewardDistributor** — calculates token rewards using a three-component formula: base participation fee, accuracy bonus, and sample contribution ratio, with a 1.2x multiplier for >90% accuracy
3. **AuditLogger** — provides queryable audit trail with filters by hospital and event type"

**Chain Integrity:**
"Validation checks three things per block: hash recalculation matches stored hash, previous_hash matches the prior block, and the hash satisfies Proof-of-Work difficulty. If someone tampers with Block 3, it cascades and invalidates every block after it."

### Demo Points
1. Open `http://54.91.23.82/` → scroll to "Blockchain Statistics" — show live block count
2. Show "Recent Blockchain Transactions" section — point out HOSPITAL_REGISTRATION, MODEL_UPDATE, REWARD_DISTRIBUTION
3. Hit `http://54.91.23.82/blockchain-api/api/blockchain/validate` in browser — shows `{"is_valid": true}`
4. Hit `http://54.91.23.82/blockchain-api/api/blockchain/leaderboard` — shows hospital rankings
5. Open `blockchain/src/blockchain_core.py` — walk through `mine_block()` and `is_chain_valid()`

### Closing (30 seconds)
"This blockchain ensures complete transparency — hospitals can audit every model update, every weight aggregation, and every reward distribution. The Proof-of-Work consensus guarantees that no entity can retroactively alter the training history."

---

## 8. Panel Q&A Preparation

**Q: Why build a custom blockchain instead of using Ethereum?**
A: "Ethereum requires gas fees, external node infrastructure, and adds unnecessary complexity. Our custom blockchain gives us full control, zero cost, and the same core guarantees — immutability, transparency, and tamper-proof audit trails. For a healthcare research system, this is more practical."

**Q: What happens if someone tampers with a block?**
A: "The hash changes, which breaks the chain linkage to the next block, which cascades and invalidates every subsequent block. Our `is_chain_valid()` method detects this by recalculating all hashes and checking chain linkage on every validation call."

**Q: How is data persisted?**
A: "The blockchain is serialized to JSON on container shutdown and reloaded on startup. This means the audit trail survives restarts. Model weights are intentionally kept in-memory for performance — they can be retrained, but the blockchain record of their hashes is permanent."

**Q: How are rewards fair?**
A: "The formula has three components: a flat participation fee (10 tokens), an accuracy bonus proportional to local model quality (0–5 tokens), and a contribution bonus proportional to dataset size relative to total (0–5 tokens). Hospitals with larger, higher-quality datasets earn proportionally more."

**Q: Can a hospital cheat by submitting fake accuracy?**
A: "The ModelUpdateValidator smart contract checks that accuracy is in [0,1] range and prevents duplicate submissions. In production, we'd add gradient-level validation. But even with inflated accuracy, the FedAvg aggregation on the server side would detect inconsistent weights."

---

## 9. Key Code References

| What to show | File | Lines | Key function |
|---|---|---|---|
| Block structure | `blockchain/src/blockchain_core.py` | 14–63 | `Block.__init__`, `calculate_hash`, `mine_block` |
| PoW mining | `blockchain/src/blockchain_core.py` | 44–52 | `mine_block()` |
| Chain validation | `blockchain/src/blockchain_core.py` | 146–167 | `is_chain_valid()` |
| Reward formula | `blockchain/src/smart_contracts.py` | 81–127 | `RewardDistributor.execute()` |
| Update validation | `blockchain/src/smart_contracts.py` | 25–71 | `ModelUpdateValidator.execute()` |
| Leaderboard | `blockchain/src/smart_contracts.py` | 129–168 | `get_leaderboard()` |
| REST API endpoints | `blockchain/src/fabric_api.py` | 83–282 | All `@app.get/post` routes |
| Transaction logging | `aggregator/src/flower_server.py` | 53–120 | `aggregate_fit()` |
