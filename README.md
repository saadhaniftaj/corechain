# CoreChain: Collaborative Medical AI Platform

**Federated Learning + Blockchain for Privacy-Preserving TB Detection**

## Overview

CoreChain is a collaborative research platform that enables hospitals to jointly train medical AI models without sharing raw patient data. The system uses:

- **Federated Learning** (Flower framework) for distributed model training
- **Homomorphic Encryption** for gradient protection
- **Blockchain** for immutable audit trails and reward distribution
- **Real-time Dashboard** for monitoring training progress

## Use Case

Multi-hospital Tuberculosis (TB) detection using chest X-ray analysis with Shenzhen and Montgomery datasets.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Hospital Node  │     │  Hospital Node  │     │  Hospital Node  │
│   (Laptop 1)    │     │   (Laptop 2)    │     │   (Laptop 3)    │
│                 │     │                 │     │                 │
│  - Local Data   │     │  - Local Data   │     │  - Local Data   │
│  - FL Client    │     │  - FL Client    │     │  - FL Client    │
│  - TB Model     │     │  - TB Model     │     │  - TB Model     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │      Encrypted Model Updates (gRPC)          │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Central Aggregator    │
                    │     (Main Laptop)       │
                    │                         │
                    │  - Flower Server        │
                    │  - Model Aggregation    │
                    │  - REST API             │
                    │  - WebSocket Server     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Blockchain Layer      │
                    │                         │
                    │  - Audit Trail          │
                    │  - Smart Contracts      │
                    │  - Reward Distribution  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Dashboard (Browser)   │
                    │                         │
                    │  - Real-time Metrics    │
                    │  - Blockchain Viewer    │
                    │  - Hospital Network     │
                    └─────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 3+ laptops on the same LAN network
- Python 3.10+ (for local development)

### 1. Start Aggregator (Main Laptop)

```bash
# Clone the repository
cd corechain

# Start aggregator services
docker-compose -f docker-compose.aggregator.yml up --build

# Services will be available at:
# - Flower Server: port 8080
# - REST API: http://localhost:8000
# - WebSocket: ws://localhost:8001
# - Blockchain API: http://localhost:7050
```

### 2. Start Hospital Nodes (Other Laptops)

On each hospital laptop:

```bash
# Create .env file
cat > .env << EOF
HOSPITAL_ID=hospital_1
HOSPITAL_NAME=General Hospital 1
AGGREGATOR_IP=192.168.1.100  # Replace with aggregator laptop IP
AGGREGATOR_PORT=50051
DATASET_TYPE=shenzhen
EOF

# Start hospital node
docker-compose -f docker-compose.hospital.yml up --build
```

### 3. Open Dashboard

Open browser and navigate to:
```
http://<aggregator-ip>:3000
```

## Project Structure

```
corechain/
├── aggregator/                 # Central aggregator service
│   ├── src/
│   │   ├── main.py            # Main entry point
│   │   ├── flower_server.py   # Flower FL server
│   │   ├── grpc_server.py     # gRPC communication
│   │   ├── rest_api.py        # Dashboard API
│   │   ├── websocket_server.py # Real-time updates
│   │   └── blockchain_client.py # Blockchain interaction
│   ├── Dockerfile
│   └── requirements.txt
│
├── hospital_node/             # Hospital node service
│   ├── src/
│   │   ├── main.py            # Main entry point
│   │   ├── fl_trainer.py      # Flower client
│   │   ├── grpc_client.py     # gRPC communication
│   │   ├── tb_model.py        # TB detection CNN
│   │   └── data_loader.py     # Dataset handling
│   ├── Dockerfile
│   └── requirements.txt
│
├── blockchain/                # Blockchain service
│   ├── src/
│   │   ├── main.py            # Main entry point
│   │   ├── blockchain_core.py # Blockchain implementation
│   │   ├── smart_contracts.py # Validation & rewards
│   │   └── fabric_api.py      # REST API
│   ├── Dockerfile
│   └── requirements.txt
│
├── shared/                    # Shared utilities
│   ├── encryption.py          # Homomorphic encryption
│   └── __init__.py
│
├── .proto/                    # Protocol buffers
│   └── corechain.proto        # gRPC definitions
│
├── dashboard/                 # React dashboard (to be created)
│   └── ...
│
├── docker-compose.aggregator.yml
├── docker-compose.hospital.yml
└── README.md
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Federated Learning** | Flower (flwr) |
| **Machine Learning** | TensorFlow/Keras |
| **Communication** | gRPC, REST (FastAPI), WebSocket |
| **Encryption** | Paillier (phe library) |
| **Blockchain** | Custom Python blockchain |
| **Frontend** | React + TypeScript + Tailwind CSS |
| **Containerization** | Docker + Docker Compose |

## Key Features

### 1. Privacy-Preserving Training
- Data never leaves hospital premises
- Only encrypted model updates are shared
- Homomorphic encryption for gradient protection

### 2. Blockchain Audit Trail
- Immutable record of all training events
- Transparent contribution tracking
- Automated reward distribution

### 3. Real-time Dashboard
- Live training progress monitoring
- Accuracy/loss visualization
- Blockchain transaction viewer
- Hospital network status

### 4. Smart Contracts
- Model update validation
- Reward calculation (base + accuracy + contribution)
- Audit logging

## API Endpoints

### REST API (Port 8000)

- `GET /api/training/status` - Current training status
- `GET /api/hospitals` - List of registered hospitals
- `GET /api/metrics/history` - Historical metrics
- `GET /api/blockchain/transactions` - Recent transactions
- `GET /api/rewards` - Reward leaderboard

### Blockchain API (Port 7050)

- `POST /api/blockchain/transaction` - Submit transaction
- `GET /api/blockchain/chain` - Get full blockchain
- `GET /api/blockchain/hospital/{id}/rewards` - Get hospital rewards
- `GET /api/blockchain/leaderboard` - Get leaderboard

## Configuration

### Environment Variables

**Aggregator:**
- `GRPC_PORT` - gRPC server port (default: 50051)
- `REST_PORT` - REST API port (default: 8000)
- `WEBSOCKET_PORT` - WebSocket port (default: 8001)
- `BLOCKCHAIN_URL` - Blockchain service URL
- `MIN_CLIENTS` - Minimum clients for FL (default: 2)
- `FL_ROUNDS` - Number of FL rounds (default: 10)

**Hospital Node:**
- `HOSPITAL_ID` - Unique hospital identifier
- `HOSPITAL_NAME` - Hospital display name
- `AGGREGATOR_IP` - Aggregator IP address
- `AGGREGATOR_PORT` - Aggregator gRPC port
- `DATASET_PATH` - Path to TB dataset
- `DATASET_TYPE` - Dataset type (shenzhen/montgomery)
- `LOCAL_EPOCHS` - Local training epochs (default: 5)
- `BATCH_SIZE` - Training batch size (default: 32)
- `LEARNING_RATE` - Learning rate (default: 0.001)

## Development

### Local Development (Without Docker)

1. Install dependencies:
```bash
cd aggregator
pip install -r requirements.txt

cd ../hospital_node
pip install -r requirements.txt

cd ../blockchain
pip install -r requirements.txt
```

2. Generate Protocol Buffers:
```bash
python -m grpc_tools.protoc -I.proto --python_out=./shared --grpc_python_out=./shared .proto/corechain.proto
```

3. Run services:
```bash
# Terminal 1: Blockchain
cd blockchain/src
python main.py

# Terminal 2: Aggregator
cd aggregator/src
python main.py

# Terminal 3: Hospital Node
cd hospital_node/src
python main.py
```

## Troubleshooting

### Connection Issues
- Ensure all laptops are on the same network
- Check firewall settings (allow ports 8000, 8001, 8080, 50051, 7050)
- Verify aggregator IP address in hospital node .env file

### Dataset Issues
- If no dataset is found, synthetic data will be generated automatically
- For real datasets, place images in `/data` directory

### Docker Issues
- Run `docker-compose down -v` to clean up volumes
- Rebuild with `docker-compose up --build --force-recreate`

## License

MIT License

## Contributors

CoreChain Development Team

## Acknowledgments

- Flower Framework for federated learning
- TensorFlow for deep learning
- Shenzhen and Montgomery TB datasets
