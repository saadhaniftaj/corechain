# CoreChain Deployment Guide

## Multi-Laptop Setup Instructions

### Prerequisites

- **3+ Laptops** on the same WiFi/LAN network
- **Docker** and **Docker Compose** installed on all laptops
- **Network Access**: Ensure firewalls allow communication between laptops

---

## Step 1: Prepare Aggregator Laptop (Main Server)

### 1.1 Clone Repository

```bash
git clone <repository-url>
cd corechain
```

### 1.2 Run Setup

```bash
./setup.sh
```

This will:
- Create necessary directories
- Generate Protocol Buffer files
- Verify dependencies

### 1.3 Find Your IP Address

**macOS:**
```bash
ipconfig getifaddr en0
# or
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Linux:**
```bash
hostname -I | awk '{print $1}'
```

**Windows:**
```bash
ipconfig
# Look for IPv4 Address
```

**Example Output:** `192.168.1.100`

⚠️ **IMPORTANT**: Write down this IP address! Hospital nodes will need it.

### 1.4 Start Aggregator Services

```bash
./start-aggregator.sh
```

Or manually:
```bash
docker-compose -f docker-compose.aggregator.yml up --build
```

### 1.5 Verify Services

Open browser and check:
- REST API: `http://localhost:8000`
- Blockchain API: `http://localhost:7050`
- Training Status: `http://localhost:8000/api/training/status`

You should see:
```json
{
  "current_round": 0,
  "total_rounds": 10,
  "is_training": false,
  "connected_hospitals": 0
}
```

---

## Step 2: Prepare Hospital Laptops

### 2.1 Clone Repository (on each hospital laptop)

```bash
git clone <repository-url>
cd corechain
```

### 2.2 Create .env File

Copy the example file:
```bash
cp .env.hospital.example .env
```

Edit `.env` with your configuration:

**Hospital 1:**
```bash
HOSPITAL_ID=hospital_1
HOSPITAL_NAME=General Hospital 1
AGGREGATOR_IP=192.168.1.100  # ← Replace with aggregator's IP
AGGREGATOR_PORT=50051
DATASET_TYPE=shenzhen
```

**Hospital 2:**
```bash
HOSPITAL_ID=hospital_2
HOSPITAL_NAME=City Medical Center
AGGREGATOR_IP=192.168.1.100  # ← Same aggregator IP
AGGREGATOR_PORT=50051
DATASET_TYPE=montgomery
```

**Hospital 3:**
```bash
HOSPITAL_ID=hospital_3
HOSPITAL_NAME=Regional Health Institute
AGGREGATOR_IP=192.168.1.100  # ← Same aggregator IP
AGGREGATOR_PORT=50051
DATASET_TYPE=shenzhen
```

### 2.3 (Optional) Add Real TB Dataset

If you have real TB datasets:

```bash
# Create data directory
mkdir -p data/tb_dataset

# Copy your dataset
# Structure should be:
# data/tb_dataset/
#   ├── normal/
#   │   ├── image1.png
#   │   └── image2.png
#   └── tb/
#       ├── image1.png
#       └── image2.png
```

If no dataset is provided, synthetic data will be generated automatically.

### 2.4 Start Hospital Node

```bash
./start-hospital.sh
```

Or manually:
```bash
docker-compose -f docker-compose.hospital.yml up --build
```

### 2.5 Verify Connection

Check the logs for:
```
✓ Connected to aggregator at 192.168.1.100:50051
✓ Hospital hospital_1 registered successfully
✓ Flower client created
```

---

## Step 3: Monitor Training

### 3.1 Check Aggregator Logs

You should see:
```
Round 1: Aggregating 3 client updates...
Round 1 aggregation complete: accuracy=0.7234, loss=0.5123
```

### 3.2 Query REST API

```bash
# Training status
curl http://192.168.1.100:8000/api/training/status

# Hospital list
curl http://192.168.1.100:8000/api/hospitals

# Metrics history
curl http://192.168.1.100:8000/api/metrics/history

# Blockchain transactions
curl http://192.168.1.100:8000/api/blockchain/transactions

# Reward leaderboard
curl http://192.168.1.100:8000/api/rewards
```

### 3.3 Check Blockchain

```bash
# Get full blockchain
curl http://192.168.1.100:7050/api/blockchain/chain

# Get hospital rewards
curl http://192.168.1.100:7050/api/blockchain/hospital/hospital_1/rewards

# Get leaderboard
curl http://192.168.1.100:7050/api/blockchain/leaderboard
```

---

## Step 4: Presentation Demo

### 4.1 Preparation

1. **Start aggregator** on main laptop
2. **Start all hospital nodes** on other laptops
3. **Open browser** to show real-time metrics

### 4.2 Demo Script

**Minute 1-2: Introduction**
- "CoreChain enables hospitals to collaboratively train AI models without sharing patient data"
- Show the 3 laptops representing different hospitals

**Minute 3-4: Show Architecture**
- Display the architecture diagram
- Explain Federated Learning concept
- Highlight privacy (encryption) and trust (blockchain)

**Minute 5-7: Live Training**
- Start training on all laptops
- Show logs updating in real-time
- Point out:
  - Each hospital training locally
  - Encrypted updates being sent
  - Model aggregation happening
  - Accuracy improving each round

**Minute 8-9: Show Blockchain**
- Query blockchain API to show transactions
- Display reward distribution
- Show leaderboard

**Minute 10: Results & Impact**
- Show final global model accuracy
- Explain how this enables collaborative research
- Discuss real-world applications

---

## Troubleshooting

### Connection Issues

**Problem:** Hospital node can't connect to aggregator

**Solutions:**
1. Verify aggregator IP address:
   ```bash
   ping 192.168.1.100
   ```

2. Check firewall settings:
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
   
   # Linux
   sudo ufw allow 8000,8001,8080,50051,7050/tcp
   ```

3. Ensure all laptops are on the same network:
   ```bash
   # Check network
   ifconfig  # macOS/Linux
   ipconfig  # Windows
   ```

### Docker Issues

**Problem:** Containers won't start

**Solutions:**
1. Clean up old containers:
   ```bash
   docker-compose down -v
   docker system prune -a
   ```

2. Rebuild from scratch:
   ```bash
   docker-compose up --build --force-recreate
   ```

3. Check Docker resources (increase if needed):
   - Docker Desktop → Preferences → Resources
   - Increase CPU and Memory allocation

### Port Conflicts

**Problem:** Port already in use

**Solutions:**
1. Find and kill process:
   ```bash
   # macOS/Linux
   lsof -ti:8000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

2. Change ports in docker-compose files

### Dataset Issues

**Problem:** No dataset found

**Solution:** The system will automatically generate synthetic data. This is fine for demos!

---

## Network Configuration Reference

### Required Ports

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| Flower Server | 8080 | TCP | FL coordination |
| gRPC Server | 50051 | TCP | Model updates |
| REST API | 8000 | TCP | Dashboard API |
| WebSocket | 8001 | TCP | Real-time updates |
| Blockchain API | 7050 | TCP | Blockchain queries |

### Firewall Rules

**macOS:**
```bash
# Allow all CoreChain ports
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/docker
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/bin/docker
```

**Linux (UFW):**
```bash
sudo ufw allow 8000,8001,8080,50051,7050/tcp
sudo ufw reload
```

**Windows:**
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "CoreChain" -Direction Inbound -Protocol TCP -LocalPort 8000,8001,8080,50051,7050 -Action Allow
```

---

## Quick Reference Commands

### Aggregator

```bash
# Start
./start-aggregator.sh

# Stop
docker-compose -f docker-compose.aggregator.yml down

# View logs
docker-compose -f docker-compose.aggregator.yml logs -f

# Restart
docker-compose -f docker-compose.aggregator.yml restart
```

### Hospital Node

```bash
# Start
./start-hospital.sh

# Stop
docker-compose -f docker-compose.hospital.yml down

# View logs
docker-compose -f docker-compose.hospital.yml logs -f

# Restart
docker-compose -f docker-compose.hospital.yml restart
```

### Monitoring

```bash
# Watch training status
watch -n 2 'curl -s http://192.168.1.100:8000/api/training/status | jq'

# Watch blockchain
watch -n 5 'curl -s http://192.168.1.100:7050/api/blockchain/stats | jq'

# Watch rewards
watch -n 5 'curl -s http://192.168.1.100:8000/api/rewards | jq'
```

---

## Success Checklist

Before your presentation, verify:

- [ ] Aggregator laptop is running all services
- [ ] All hospital laptops can ping aggregator IP
- [ ] Hospital nodes successfully connect and register
- [ ] Training starts and completes at least 1 round
- [ ] Blockchain is recording transactions
- [ ] Rewards are being distributed
- [ ] REST API endpoints are responding
- [ ] Logs show no errors

---

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Verify network connectivity: `ping <aggregator-ip>`
3. Review this deployment guide
4. Check the main README.md for architecture details
