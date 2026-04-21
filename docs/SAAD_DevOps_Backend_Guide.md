# Saad's Final Panel Guide: DevOps, Backend & Infrastructure

## Your Responsibility
**AWS Multi-Node Deployment, Docker Containerization, Backend APIs (REST + gRPC + WebSocket), NGINX Reverse Proxy, CI/CD, and System Integration**

You built and deployed the entire production infrastructure — three EC2 instances (aggregator + two hospital nodes), Docker images, the REST API, gRPC hospital registration service, WebSocket server, JWT authentication, and the NGINX reverse proxy that ties everything together.

---

## 1. Production Architecture — Live on AWS

```
                     ┌──────────────────────────────────────────────────────┐
                     │     Aggregator EC2 (t3.micro) — 54.91.23.82        │
                     │                                                      │
  Browser ──:80────▶ │  NGINX (Reverse Proxy)                              │
                     │    /              → dashboard (static HTML)          │
                     │    /api/          → :8000 (REST API - FastAPI)       │
                     │    /blockchain-api/→ :7050 (Blockchain API)          │
                     │    /ws            → :8001 (WebSocket)                │
                     │                                                      │
                     │  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐  │
                     │  │ Flower Svr  │ │ REST API │ │ Blockchain Node  │  │
                     │  │  :8080      │ │ :8000    │ │ :7050            │  │
                     │  │  gRPC FL    │ │ FastAPI  │ │ FastAPI + PoW    │  │
                     │  └──────┬──────┘ └──────────┘ └──────────────────┘  │
                     │         │ :50051 gRPC Registration                   │
                     │  ┌──────┴──────┐                                     │
                     │  │ gRPC Server │                                     │
                     │  │ Hospital Reg│                                     │
                     │  └─────────────┘                                     │
                     └─────────┬──────────────────────┬─────────────────────┘
                               │                      │
              Flower :8080     │     gRPC :50051      │     Flower :8080
                               │                      │
              ┌────────────────┴──┐              ┌────┴────────────────────┐
              │  Hospital ALPHA   │              │  Hospital BETA          │
              │  52.54.140.7      │              │  54.165.151.110         │
              │  t3.micro EC2     │              │  t3.micro EC2           │
              │                   │              │                         │
              │  Docker container │              │  Docker container       │
              │  corechain-       │              │  corechain-             │
              │  hospital:latest  │              │  hospital:latest        │
              │                   │              │                         │
              │  St. Mary         │              │  City General           │
              │  Regional Medical │              │  Research Hospital      │
              │  Shenzhen dataset │              │  Montgomery dataset     │
              └───────────────────┘              └─────────────────────────┘
```

### AWS Infrastructure Details

| Resource | Value |
|----------|-------|
| **Region** | us-east-1 (N. Virginia) |
| **Instance Type** | t3.micro (1 vCPU, 1GB RAM) — Free Tier |
| **AMI** | Ubuntu 22.04 LTS |
| **Security Group** | sg-0b921698dae8e557b |
| **SSH Key** | corechain-key.pem |
| **Dashboard URL** | http://54.91.23.82/ |

### Security Group Rules (Inbound)

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | My IP | SSH access |
| 80 | TCP | 0.0.0.0/0 | Dashboard (NGINX) |
| 8000 | TCP | 0.0.0.0/0 | REST API |
| 8080 | TCP | 0.0.0.0/0 | Flower FL server |
| 50051 | TCP | 0.0.0.0/0 | gRPC registration |

---

## 2. Docker Architecture

### File Structure
```
Dockerfile.hospital          ← Hospital node image (pushed to Docker Hub)
Dockerfile.aggregator        ← Aggregator image (supervisord)
docker-compose.aggregator.yml ← Aggregator stack (aggregator + blockchain + dashboard)
docker-compose.hospital.yml   ← Hospital stack (for local testing)
dashboard/Dockerfile          ← NGINX dashboard container
```

### Hospital Dockerfile — `Dockerfile.hospital` (Lines 1–32)

```dockerfile
FROM python:3.10-slim

# System deps for OpenCV and TensorFlow
RUN apt-get update && apt-get install -y \
    gcc g++ libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY hospital_node/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hospital_node/ /app/
COPY shared/ /app/shared/
COPY .proto/ /app/.proto/

# Compile gRPC protobuf stubs
RUN python -m grpc_tools.protoc \
    -I/app/.proto \
    --python_out=/app/src \
    --grpc_python_out=/app/src \
    /app/.proto/hospital.proto

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "src/main.py"]
```

**Key decisions:**
- **Multi-architecture**: Built with `docker buildx` for both `linux/amd64` (EC2) and `linux/arm64` (Mac M4)
- **gRPC compiled at build time**: Protobuf stubs generated during `docker build`, not at runtime
- **No cache**: `--no-cache-dir` reduces image size by ~200MB
- **Published to Docker Hub**: `saadhaniftaj/corechain-hospital:latest`

### Aggregator Stack — `docker-compose.aggregator.yml`

```yaml
services:
  aggregator:
    container_name: corechain_aggregator
    build: { context: ., dockerfile: Dockerfile.aggregator }
    network_mode: host           # Shares host network for simplicity
    environment:
      - MIN_CLIENTS=2            # Wait for 2 hospitals before training
      - FL_ROUNDS=10             # 10 rounds of federated learning
      - GRPC_PORT=50051
      - REST_PORT=8000
      - FLOWER_PORT=8080
      - BLOCKCHAIN_URL=http://localhost:7050
    volumes:
      - ./aggregator/src:/app/src    # Live code mount
      - ./shared:/app/shared
      - ./models:/app/models

  blockchain:
    container_name: corechain_blockchain
    build: { context: ., dockerfile: blockchain/Dockerfile }
    network_mode: host
    environment:
      - BLOCKCHAIN_PORT=7050
      - DIFFICULTY=4

  dashboard:
    container_name: corechain_dashboard
    build: { context: ., dockerfile: dashboard/Dockerfile }
    network_mode: host           # Serves on port 80
```

**`network_mode: host`**: All containers share the EC2's network stack — the aggregator on :8000, blockchain on :7050, dashboard on :80, all accessible directly. No Docker-internal networking needed.

---

## 3. Backend APIs

### 3.1 REST API — `aggregator/src/rest_api.py` (295 lines)

**Framework**: FastAPI on port 8000

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/login` | JWT authentication → returns token |
| `POST` | `/api/logout` | Invalidates JWT token |
| `GET` | `/api/status` | Training state (round, accuracy, loss, etc.) |
| `GET` | `/api/hospitals` | List of connected hospitals |
| `GET` | `/api/metrics/history` | Accuracy/loss arrays for charts |
| `GET` | `/api/rewards` | Hospital reward leaderboard |
| `GET` | `/api/blockchain/transactions` | Recent blockchain transactions |
| `GET` | `/api/users` | User management (admin only) |
| `POST` | `/api/users` | Create new user |

#### `/api/status` Response (Lines 63–83)

```python
@app.get("/api/status")
async def get_status():
    return {
        "current_round": training_state.get('current_round', 0),
        "total_rounds": training_state.get('total_rounds', 10),
        "global_accuracy": training_state.get('global_accuracy', 0.0),
        "global_loss": training_state.get('global_loss', 0.0),
        "is_training": training_state.get('is_training', False),
        "connected_hospitals": len(registered_hospitals),
        "total_hospitals": len(registered_hospitals),
        "blockchain_connected": blockchain_client is not None,
        "progress_percentage": (current_round / total_rounds) * 100
    }
```

#### `/api/hospitals` Response (Lines 85–115)

```python
@app.get("/api/hospitals")
async def get_hospitals():
    hospitals = []
    for hid, info in registered_hospitals.items():
        hospitals.append({
            "hospital_id": hid,
            "hospital_name": info.get('hospital_name', hid),
            "dataset_size": info.get('dataset_size', 0),
            "dataset_type": info.get('dataset_type', 'unknown'),
            "status": "connected",
            "registered_at": info.get('registered_at', '')
        })
    return {"hospitals": hospitals}
```

### 3.2 gRPC API — `aggregator/src/grpc_server.py`

**Framework**: grpc.io on port 50051

**Protobuf definition** (`.proto/hospital.proto`):
```protobuf
service HospitalService {
    rpc RegisterHospital(HospitalInfo) returns (RegistrationResponse);
    rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
}

message HospitalInfo {
    string hospital_id = 1;
    string hospital_name = 2;
    int32 dataset_size = 3;
    string dataset_type = 4;
}

message RegistrationResponse {
    bool success = 1;
    string message = 2;
}
```

**Server implementation** (Lines 20–60):
```python
class HospitalServicer(hospital_pb2_grpc.HospitalServiceServicer):
    def RegisterHospital(self, request, context):
        hospital_id = request.hospital_id
        hospital_name = request.hospital_name
        
        # Store in shared state
        registered_hospitals[hospital_id] = {
            'hospital_name': hospital_name,
            'dataset_size': request.dataset_size,
            'dataset_type': request.dataset_type,
            'status': 'connected',
            'registered_at': datetime.now().isoformat()
        }
        
        # Log to blockchain
        if blockchain_client:
            blockchain_client.log_transaction({
                'type': 'HOSPITAL_REGISTRATION',
                'hospital_id': hospital_id,
                'hospital_name': hospital_name,
                'dataset_size': request.dataset_size
            })
        
        return hospital_pb2.RegistrationResponse(
            success=True,
            message=f"Hospital {hospital_name} registered"
        )
```

### 3.3 WebSocket Server — `aggregator/src/websocket_server.py`

**Framework**: websockets library on port 8001

```python
class WebSocketServer:
    def __init__(self, port=8001):
        self.port = port
        self.clients = set()
    
    async def handler(self, websocket, path):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                pass  # Keep connection alive
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, data):
        """Push updates to all connected dashboard clients"""
        message = json.dumps(data)
        for client in self.clients:
            await client.send(message)
```

---

## 4. JWT Authentication — `aggregator/src/auth.py`

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv('JWT_SECRET', 'corechain-secret')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_token(user_id: str, role: str):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
```

Default users seeded on startup via `user_store.py`:
- `admin` / `admin123` (role: admin)
- `viewer` / `viewer123` (role: viewer)

---

## 5. NGINX Reverse Proxy — `dashboard/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;

    root /var/www/html;
    index index.html;

    # Dashboard SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # REST API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Blockchain API proxy
    location /blockchain-api/ {
        proxy_pass http://127.0.0.1:7050/;
        proxy_set_header Host $host;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

**Why NGINX?**
- Browser can only reach port 80 (the only port users see)
- Internal services run on 8000, 7050, 8001 — all firewalled from direct browser access
- NGINX routes by URL path: `/api/` → REST, `/blockchain-api/` → blockchain, `/ws` → WebSocket

---

## 6. Aggregator Boot Sequence — `aggregator/src/main.py`

```python
if __name__ == "__main__":
    # Step 1: Initialize shared state
    training_state = { 'current_round': 0, 'is_training': False, ... }
    registered_hospitals = {}
    
    # Step 2: Connect to blockchain API (port 7050)
    blockchain_client = BlockchainClient(url=os.getenv('BLOCKCHAIN_URL'))
    
    # Step 3: Start gRPC registration server (port 50051) in background
    grpc_thread = threading.Thread(target=start_grpc_server, args=(50051,))
    grpc_thread.daemon = True
    grpc_thread.start()
    
    # Step 4: Start WebSocket server (port 8001) in background
    ws_thread = threading.Thread(target=start_websocket_server)
    ws_thread.daemon = True
    ws_thread.start()
    
    # Step 5: Start Flower FL server (port 8080) in background
    flower_thread = threading.Thread(
        target=start_flower_server,
        kwargs={'min_clients': int(os.getenv('MIN_CLIENTS', 2)),
                'num_rounds': int(os.getenv('FL_ROUNDS', 10))}
    )
    flower_thread.daemon = True
    flower_thread.start()
    
    # Step 6: Start REST API (port 8000) — blocks main thread
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('REST_PORT', 8000)))
```

**5 services running in one container via threading:**
1. REST API (:8000) — main thread
2. Flower Server (:8080) — daemon thread
3. gRPC Server (:50051) — daemon thread
4. WebSocket Server (:8001) — daemon thread
5. Blockchain Client — connects to blockchain container on :7050

---

## 7. Docker Hub — Multi-Architecture Image

### Build Command (executed on Mac M4)
```bash
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -f Dockerfile.hospital \
    -t saadhaniftaj/corechain-hospital:latest \
    --push .
```

This produces a **multi-architecture manifest** on Docker Hub:
- `linux/arm64` — runs natively on Mac M4
- `linux/amd64` — runs natively on AWS EC2 (x86_64)

**Docker Hub**: `docker pull saadhaniftaj/corechain-hospital:latest`

### How Hospital Containers Are Launched on EC2

```bash
docker run -d --name hospital_alpha --restart unless-stopped \
    -e HOSPITAL_ID=hospital_alpha \
    -e HOSPITAL_NAME="St. Mary Regional Medical" \
    -e AGGREGATOR_IP=54.91.23.82 \
    -e AGGREGATOR_PORT=50051 \
    -e FLOWER_PORT=8080 \
    -e DATASET_TYPE=shenzhen \
    saadhaniftaj/corechain-hospital:latest python src/main.py
```

---

## 8. Deployment Workflow

### Full Deployment Steps (what I actually did)

1. **Provision 3 EC2 instances** (t3.micro, Ubuntu 22.04, same security group)
2. **Install Docker** on all three via SSH
3. **Build aggregator stack** on aggregator EC2:
   ```bash
   git clone https://github.com/saadhaniftaj/corechain.git
   cd corechain && docker compose -f docker-compose.aggregator.yml up -d
   ```
4. **Build hospital image natively on EC2** (x86_64 → x86_64, no QEMU):
   ```bash
   docker build -f Dockerfile.hospital -t corechain-hospital:latest .
   ```
5. **Distribute hospital image** to other EC2s via compressed tarball:
   ```bash
   docker save corechain-hospital:latest | gzip > hospital.tar.gz
   scp hospital.tar.gz ubuntu@52.54.140.7:~/
   scp hospital.tar.gz ubuntu@54.165.151.110:~/
   # On each hospital EC2:
   docker load < hospital.tar.gz
   ```
6. **Launch hospitals simultaneously** (critical for MIN_CLIENTS=2):
   ```bash
   ssh ubuntu@52.54.140.7 'docker run -d --name hospital_alpha ...' &
   ssh ubuntu@54.165.151.110 'docker run -d --name hospital_beta ...' &
   wait
   ```
7. **Push multi-arch image to Docker Hub** from Mac for future deployments

---

## 9. Environment Variables

### Aggregator
| Variable | Default | Purpose |
|----------|---------|---------|
| `MIN_CLIENTS` | 2 | Hospitals needed before training starts |
| `FL_ROUNDS` | 10 | Total FL training rounds |
| `REST_PORT` | 8000 | FastAPI REST server port |
| `GRPC_PORT` | 50051 | gRPC registration port |
| `FLOWER_PORT` | 8080 | Flower FL server port |
| `WEBSOCKET_PORT` | 8001 | WebSocket broadcast port |
| `BLOCKCHAIN_URL` | http://localhost:7050 | Blockchain API URL |
| `JWT_SECRET` | corechain-secret | JWT signing key |

### Hospital
| Variable | Default | Purpose |
|----------|---------|---------|
| `HOSPITAL_ID` | hospital_1 | Unique hospital identifier |
| `HOSPITAL_NAME` | General Hospital | Display name |
| `AGGREGATOR_IP` | localhost | Aggregator EC2 IP |
| `AGGREGATOR_PORT` | 50051 | gRPC registration port |
| `FLOWER_PORT` | 8080 | Flower server port |
| `DATASET_TYPE` | shenzhen | Dataset variant (shenzhen/montgomery) |
| `DATASET_PATH` | /data | X-ray data directory |

---

## 10. Presentation Talking Points

### Opening (30 seconds)
"I handled all DevOps and backend infrastructure — deploying three AWS EC2 instances, containerizing every component with Docker, building three backend API protocols, and configuring the NGINX reverse proxy. The entire system runs in production on AWS right now."

### Technical Deep Dive (3 minutes)

**Infrastructure:**
"The system runs on three t3.micro EC2 instances — one aggregator and two independent hospital nodes. The aggregator runs 5 concurrent services in a single container using Python threading: REST API on 8000, Flower server on 8080, gRPC on 50051, WebSocket on 8001, and a blockchain client connecting to port 7050."

**Three API Protocols:**
"I chose the right tool for each job:
1. **gRPC** (port 50051) for hospital registration — binary Protocol Buffers for type-safe, high-performance initial handshake
2. **REST/FastAPI** (port 8000) for dashboard data — JSON over HTTP for simplicity and Swagger auto-docs
3. **WebSocket** (port 8001) for real-time push — persistent bidirectional connection for live dashboard updates"

**Docker Strategy:**
"I built the hospital image with `docker buildx` for both amd64 and arm64, pushed to Docker Hub as `saadhaniftaj/corechain-hospital:latest`. Any EC2 or Mac can pull and run it immediately. The aggregator uses docker-compose with `network_mode: host` for zero-config networking."

**The Synchronization Challenge:**
"The hardest problem was launching 2 hospital containers simultaneously so they both connect to Flower before it starts Round 1. I solved this by replacing the blocking TCP pre-flight check with a resilient retry loop, then launching both hospital containers in parallel via SSH."

### Live Demo Flow
1. Navigate to `http://54.91.23.82/` → show live dashboard
2. SSH into aggregator: `docker ps` → show all 3 containers running
3. Show `docker logs corechain_aggregator --tail 10` → live training logs
4. Hit `http://54.91.23.82:8000/api/status` in browser → raw JSON response
5. Hit `http://54.91.23.82:8000/api/hospitals` → show both hospitals registered

---

## 11. Panel Q&A Preparation

**Q: Why 3 separate EC2 instances instead of running everything on one?**
A: "That would defeat the purpose of federated learning. Each hospital in the real world is a separate organization with its own infrastructure. Running them on separate EC2 instances proves the system works across network boundaries — data stays local, only weight updates travel over the wire."

**Q: Why Docker instead of running directly?**
A: "Docker gives us portable, reproducible environments. The same `corechain-hospital:latest` image runs identically on my Mac (ARM), on EC2 (x86), and anywhere Docker exists. It also isolates dependencies — TensorFlow, Flower, gRPC all packaged together."

**Q: How secure is the system?**
A: "We use AWS Security Groups for network-level access control, SSH key-based authentication for server access, JWT tokens with 30-minute expiry for dashboard auth, and gRPC (which supports TLS) for hospital-aggregator communication. For production, we'd add HTTPS/TLS certificates."

**Q: What's the cost?**
A: "All three instances are t3.micro — AWS Free Tier eligible. Total monthly cost: $0 for the first 12 months, then about $25/month for three instances."

**Q: How would you scale to 100 hospitals?**
A: "The architecture scales horizontally — just launch more hospital containers. Flower natively supports thousands of clients. For the aggregator, we'd add an Application Load Balancer and potentially scale to a larger instance. The NGINX proxy and REST API are already stateless."

---

## 12. Key Code References

| What to show | File | Lines | Key detail |
|---|---|---|---|
| Hospital Dockerfile | `Dockerfile.hospital` | 1–32 | Multi-stage with gRPC compile |
| Aggregator boot | `aggregator/src/main.py` | 30–85 | 5 services starting |
| REST API | `aggregator/src/rest_api.py` | 63–115 | `/api/status`, `/api/hospitals` |
| gRPC server | `aggregator/src/grpc_server.py` | 20–60 | `RegisterHospital()` |
| JWT auth | `aggregator/src/auth.py` | 1–40 | `create_token()` |
| NGINX config | `dashboard/nginx.conf` | 20–53 | 4 proxy routes |
| Docker compose | `docker-compose.aggregator.yml` | 1–30 | `network_mode: host` |
| Hospital retry | `hospital_node/src/main.py` | 55–68 | `while True` retry loop |
| Protobuf def | `.proto/hospital.proto` | 1–25 | Service + message defs |

---

## 13. GitHub Repository

**URL**: https://github.com/saadhaniftaj/corechain

**Latest commits**:
```
ff17fd6 Fix: Replace blocking TCP wait with resilient retry loops for hospital sync
3561f19 FYP Production: gRPC server fix, FedAvg training, dashboard blockchain proxy
3e9e727 Mobility Phase: auth hardening (30-min JWT, logout, auth gate)
4d332dd Repository final cleanup: comprehensive FYP README
```
