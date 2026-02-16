# CoreChain - Privacy-Preserving Collaborative Medical AI Platform

**Final Year Project (FYP)**  
**Team:** Saad Hanif Taj & Collaborators

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-saadhaniftaj-blue)](https://hub.docker.com/u/saadhaniftaj)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Project Overview

CoreChain is a **privacy-preserving collaborative AI platform** that enables multiple hospitals to jointly train medical AI models (specifically for TB detection) without sharing raw patient data. The system combines:

- **Federated Learning** (Flower framework) - Train together without sharing data
- **Homomorphic Encryption** (Paillier) - Protect model gradients
- **Blockchain** (Custom lightweight) - Immutable audit trail and rewards
- **Real-time Dashboard** - Monitor training progress

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Hospital Node  │     │  Hospital Node  │     │  Hospital Node  │
│   (Laptop 1)    │     │   (Laptop 2)    │     │   (Laptop 3)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │      Encrypted Model Updates (gRPC)          │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Central Aggregator    │
                    │  - Flower Server        │
                    │  - Blockchain           │
                    │  - Dashboard            │
                    └─────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker installed
- 2+ laptops on same network
- Internet connection (for first pull)

### 1. Start Aggregator (Admin)

```bash
docker pull saadhaniftaj/corechain-aggregator:latest

docker run -d \
  -p 80:80 \
  -p 8080:8080 \
  -p 50051:50051 \
  -p 7050:7050 \
  --name corechain-aggregator \
  saadhaniftaj/corechain-aggregator:latest
```

**Access Dashboard:** http://localhost

### 2. Start Hospital Nodes

```bash
docker pull saadhaniftaj/corechain-hospital:latest

docker run -d \
  -e HOSPITAL_ID=hospital_1 \
  -e HOSPITAL_NAME="General Hospital" \
  -e AGGREGATOR_IP=<aggregator-ip> \
  --name hospital-1 \
  saadhaniftaj/corechain-hospital:latest
```

---

## 📁 Project Structure

```
corechain/
├── aggregator/              # Central server
│   ├── src/
│   │   ├── main.py         # Entry point
│   │   ├── flower_server.py # FL coordination
│   │   ├── grpc_server.py  # Hospital communication
│   │   ├── rest_api.py     # Dashboard API
│   │   ├── websocket_server.py # Real-time updates
│   │   └── blockchain_client.py # Blockchain interaction
│   ├── Dockerfile
│   └── requirements.txt
│
├── hospital_node/          # Hospital participant
│   ├── src/
│   │   ├── main.py        # Entry point
│   │   ├── fl_trainer.py  # Flower client
│   │   ├── tb_model.py    # CNN model
│   │   ├── data_loader.py # Dataset handling
│   │   └── grpc_client.py # Aggregator communication
│   ├── Dockerfile
│   └── requirements.txt
│
├── blockchain/             # Audit trail
│   ├── src/
│   │   ├── blockchain_core.py # Core blockchain
│   │   ├── smart_contracts.py # Validation & rewards
│   │   └── fabric_api.py      # REST API
│   └── requirements.txt
│
├── dashboard/              # Web interface
│   └── index.html         # Real-time dashboard
│
├── shared/                 # Shared utilities
│   └── encryption.py      # Paillier HE
│
├── .proto/                 # gRPC definitions
│   └── corechain.proto
│
├── docker/                 # Docker configs
│   ├── nginx.conf
│   └── supervisord.conf
│
├── QUICKSTART.md          # Fast deployment guide
├── DEPLOYMENT.md          # Multi-laptop setup
├── WORKFLOW.md            # System explanation
└── README.md              # This file
```

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Federated Learning** | Flower 1.6.0 | Multi-party training |
| **Machine Learning** | TensorFlow 2.15.0 | TB detection CNN |
| **Communication** | gRPC, FastAPI, WebSocket | Inter-service messaging |
| **Encryption** | Paillier (phe) | Gradient protection |
| **Blockchain** | Custom Python | Audit trail |
| **Frontend** | HTML/CSS/JS | Dashboard |
| **Deployment** | Docker Compose | Orchestration |

---

## 📊 Features Implemented

### ✅ Phase 1: Infrastructure
- Multi-node Docker architecture
- gRPC communication
- REST API for dashboard
- WebSocket for real-time updates

### ✅ Phase 2: Federated Learning
- Flower framework integration
- Custom FedAvg strategy
- TB detection CNN model
- Data preprocessing pipeline
- Paillier homomorphic encryption

### ✅ Phase 3: Blockchain
- Lightweight blockchain core
- Smart contracts (validation, rewards, audit)
- Transaction logging
- Reward distribution

### ✅ Phase 4: Dashboard
- Real-time training monitoring
- Hospital network viewer
- Blockchain transaction explorer
- Responsive UI with animations

---

## 🎓 Team Collaboration

### For Team Members:

**Clone Repository:**
```bash
git clone https://github.com/saadhaniftaj/fyp.git
cd fyp
```

**Local Development:**
```bash
# Generate Protocol Buffers
./setup.sh

# Start aggregator
./start-aggregator.sh

# Start hospital node
./start-hospital.sh
```

**Docker Images:**
- Aggregator: `saadhaniftaj/corechain-aggregator:latest`
- Hospital: `saadhaniftaj/corechain-hospital:latest`

---

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Fast deployment (5 minutes)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Multi-laptop setup guide
- **[WORKFLOW.md](WORKFLOW.md)** - Complete system explanation
- **[SRS.pdf](SRS.pdf)** - Software Requirements Specification

---

## 🎬 Demo Instructions

### Presentation Setup (3 Laptops):

1. **Laptop 1 (Aggregator):** Run aggregator container
2. **Laptop 2-3 (Hospitals):** Run hospital containers
3. **Browser:** Open dashboard to show real-time training

### Expected Results:
- Training completes in ~10 minutes (10 rounds)
- Final accuracy: 80-90%
- Blockchain: 30-50 transactions
- Dashboard: Live updates every 5 seconds

---

## 🔍 Monitoring & Debugging

### View Logs:
```bash
docker logs -f corechain-aggregator
docker logs -f hospital-1
```

### Check Status:
```bash
# Training status
curl http://localhost:8000/api/training/status

# Blockchain stats
curl http://localhost:7050/api/blockchain/stats
```

### Troubleshooting:
- Check `DEPLOYMENT.md` for common issues
- Verify network connectivity between laptops
- Ensure all required ports are open

---

## 🚧 Future Enhancements

- [ ] Add authentication (JWT)
- [ ] Enable HTTPS/TLS
- [ ] Integrate real TB datasets
- [ ] Add model versioning
- [ ] Implement differential privacy
- [ ] Create React dashboard
- [ ] Deploy to cloud (Azure/AWS)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 👥 Contributors

- **Saad Hanif Taj** - [@saadhaniftaj](https://github.com/saadhaniftaj)
- **Team Members** - (Add your names here)

---

## 📧 Contact

- **Email:** contact@vanguardsolutions.cloud
- **GitHub:** https://github.com/saadhaniftaj/fyp
- **Docker Hub:** https://hub.docker.com/u/saadhaniftaj

---

## 🙏 Acknowledgments

- Flower Framework for federated learning
- TensorFlow for deep learning
- Shenzhen and Montgomery TB datasets
- University supervisors and mentors

---

**Built with ❤️ for advancing privacy-preserving medical AI research**
