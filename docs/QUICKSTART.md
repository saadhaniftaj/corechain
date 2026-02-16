# CoreChain - Quick Start Guide

## 🎉 Docker Images Now Available!

Both CoreChain containers are now live on Docker Hub:

- **Aggregator:** `saadhaniftaj/corechain-aggregator:latest`
- **Hospital Node:** `saadhaniftaj/corechain-hospital:latest`

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Start Aggregator (Admin Laptop)

```bash
docker pull saadhaniftaj/corechain-aggregator:latest

docker run -d \
  -p 80:80 \
  -p 8080:8080 \
  -p 50051:50051 \
  -p 7050:7050 \
  -p 8000:8000 \
  -p 8001:8001 \
  --name corechain-aggregator \
  saadhaniftaj/corechain-aggregator:latest
```

**Access Dashboard:** http://localhost

---

### Step 2: Start Hospital Nodes (Other Laptops)

**Find Aggregator IP:**
```bash
# On Mac
ipconfig getifaddr en0

# On Linux
hostname -I | awk '{print $1}'
```

**Run Hospital Container:**
```bash
docker pull saadhaniftaj/corechain-hospital:latest

docker run -d \
  -e HOSPITAL_ID=hospital_1 \
  -e HOSPITAL_NAME="General Hospital" \
  -e AGGREGATOR_IP=192.168.1.100 \
  -e AGGREGATOR_PORT=50051 \
  -e DATASET_TYPE=shenzhen \
  --name hospital-node-1 \
  saadhaniftaj/corechain-hospital:latest
```

**Repeat for each hospital** (change HOSPITAL_ID and HOSPITAL_NAME)

---

## 📊 What Happens Next

1. **Automatic Registration:** Hospital nodes connect to aggregator
2. **Training Starts:** When MIN_CLIENTS (default: 2) hospitals connect
3. **10 Rounds:** Federated learning runs for 10 rounds
4. **Real-Time Updates:** Dashboard shows live progress
5. **Blockchain Logging:** All events recorded immutably

---

## 🔍 Monitoring

### View Logs:
```bash
# Aggregator
docker logs -f corechain-aggregator

# Hospital
docker logs -f hospital-node-1
```

### Check Status:
```bash
# Training status
curl http://localhost:8000/api/training/status

# Hospitals
curl http://localhost:8000/api/hospitals

# Blockchain
curl http://localhost:7050/api/blockchain/stats
```

---

## 🛠️ Configuration

### Aggregator Environment Variables:
- `MIN_CLIENTS` - Minimum hospitals to start (default: 2)
- `FL_ROUNDS` - Number of training rounds (default: 10)
- `DIFFICULTY` - Blockchain mining difficulty (default: 4)

### Hospital Environment Variables:
- `HOSPITAL_ID` - Unique identifier (required)
- `HOSPITAL_NAME` - Display name (required)
- `AGGREGATOR_IP` - Aggregator IP address (required)
- `DATASET_TYPE` - shenzhen or montgomery (default: shenzhen)
- `LOCAL_EPOCHS` - Training epochs per round (default: 5)
- `BATCH_SIZE` - Training batch size (default: 32)

---

## 🎬 Demo Workflow

### Presentation Setup (3 Laptops):

**Laptop 1 (Aggregator):**
```bash
docker run -d -p 80:80 -p 8080:8080 -p 50051:50051 -p 7050:7050 \
  --name corechain-aggregator \
  saadhaniftaj/corechain-aggregator:latest
```

**Laptop 2 (Hospital 1):**
```bash
docker run -d \
  -e HOSPITAL_ID=hospital_1 \
  -e HOSPITAL_NAME="General Hospital" \
  -e AGGREGATOR_IP=<aggregator-ip> \
  --name hospital-1 \
  saadhaniftaj/corechain-hospital:latest
```

**Laptop 3 (Hospital 2):**
```bash
docker run -d \
  -e HOSPITAL_ID=hospital_2 \
  -e HOSPITAL_NAME="City Medical Center" \
  -e AGGREGATOR_IP=<aggregator-ip> \
  --name hospital-2 \
  saadhaniftaj/corechain-hospital:latest
```

**Open Dashboard:** http://<aggregator-ip>

---

## 🔧 Troubleshooting

### Container won't start:
```bash
docker logs corechain-aggregator
docker logs hospital-node-1
```

### Can't connect to aggregator:
```bash
# Check network
ping <aggregator-ip>

# Check firewall
# Allow ports: 80, 8000, 8001, 8080, 50051, 7050
```

### Reset everything:
```bash
docker stop corechain-aggregator hospital-node-1
docker rm corechain-aggregator hospital-node-1
docker pull saadhaniftaj/corechain-aggregator:latest
docker pull saadhaniftaj/corechain-hospital:latest
# Start again
```

---

## 📦 What's Inside

### Aggregator Container:
- Flower Server (FL coordination)
- REST API (dashboard data)
- WebSocket Server (real-time updates)
- Blockchain Service (audit trail)
- Dashboard (web UI)
- gRPC Server (hospital communication)

### Hospital Container:
- Flower Client (FL participation)
- TB Detection Model (CNN)
- Data Loader (dataset handling)
- gRPC Client (aggregator communication)
- Encryption (gradient protection)

---

## 🎯 Success Checklist

- [ ] Aggregator running and accessible
- [ ] Dashboard loads at http://localhost
- [ ] Hospital nodes connect successfully
- [ ] Training starts automatically
- [ ] Dashboard shows real-time updates
- [ ] Blockchain records transactions
- [ ] Final accuracy > 80%

---

## 📚 Additional Resources

- **Full Documentation:** See `WORKFLOW.md`
- **Deployment Guide:** See `DEPLOYMENT.md`
- **Architecture:** See `README.md`

---

## 🆘 Support

**Docker Hub:**
- https://hub.docker.com/r/saadhaniftaj/corechain-aggregator
- https://hub.docker.com/r/saadhaniftaj/corechain-hospital

**Issues:** Check logs with `docker logs -f <container-name>`

---

**CoreChain is ready for your presentation!** 🎊
