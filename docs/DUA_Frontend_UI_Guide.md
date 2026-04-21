# Dua's Final Panel Guide: Frontend Dashboard & UI

## Your Responsibility
**Aggregator Dashboard Design, Real-Time Data Visualization, API Integration, and User Experience**

You built the central CoreChain monitoring dashboard — a single-page application that provides real-time visibility into federated learning training, hospital connections, blockchain audit trails, accuracy/loss charting, and the reward leaderboard.

---

## 1. Frontend Architecture Overview

### Technology Stack

| Technology | Purpose | Why Chosen |
|---|---|---|
| **HTML5** | Semantic page structure | Native, no build step |
| **CSS3 (Custom)** | Design system + animations | Full control, no framework bloat |
| **Vanilla JavaScript** | Fetch API, DOM manipulation, polling | Zero dependencies, ~400 lines |
| **Chart.js 4.4.0** | Accuracy/Loss/Reward charts | Lightweight, beautiful charts |
| **Inter (Google Font)** | Modern typography | Clean, professional, medical-grade |
| **NGINX** | Static file serving + reverse proxy | Routes `/api/` and `/blockchain-api/` |

### File Structure
```
dashboard/
├── index.html          ← Single file: HTML + CSS + JS (639 lines)
├── login.html          ← JWT authentication page
├── nginx.conf          ← Reverse proxy configuration
└── Dockerfile          ← NGINX-based container
```

### Architecture Flow
```
Browser (port 80)
    ↓ HTTP
NGINX (dashboard container)
    ├── /                  → serves index.html (static)
    ├── /login             → serves login.html
    ├── /api/*             → proxy to aggregator REST API (:8000)
    ├── /blockchain-api/*  → proxy to blockchain API (:7050)
    └── /ws                → proxy to WebSocket server (:8001)
```

---

## 2. Design System — CSS Variables (Lines 11–23)

```css
:root {
    --pearl: #f8f9fa;          /* Page background */
    --pearl-dark: #e9ecef;     /* Section backgrounds */
    --yellow: #fbbf24;         /* Primary brand color */
    --yellow-dark: #f59e0b;    /* Hover states, accents */
    --text-dark: #1f2937;      /* Headings, primary text */
    --text-light: #6b7280;     /* Secondary text, labels */
    --card: #ffffff;           /* Card backgrounds */
    --border: #e5e7eb;         /* Dividers, borders */
    --green: #10b981;          /* Connected/success states */
    --red: #ef4444;            /* Error/offline states */
    --blue: #3b82f6;           /* Info accents */
}
```

**Color Psychology:**
- **Yellow/Amber** (#fbbf24): Warmth, trust, optimism — appropriate for healthcare
- **Pearl White** (#f8f9fa): Clinical cleanliness, professional
- **Dark Gray** (#1f2937): High-contrast readability

---

## 3. Page Layout — 5 Tabbed Sections

The dashboard uses a **tab-based navigation** system with 5 panels:

### Tab Bar (Lines 49–53)
```css
.tab-bar { display: flex; gap: 0.4rem; background: var(--pearl-dark); 
           border-radius: 12px; padding: 4px; }
.tab-btn.active { background: var(--card); color: var(--text-dark); 
                  box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
```

| Tab | Content | Key Data |
|-----|---------|----------|
| **Training** | Progress bar, round indicator, hospital list | `current_round`, `connected_hospitals` |
| **Accuracy** | Chart.js line chart of accuracy per round | `accuracy_history[]` |
| **Loss** | Chart.js line chart of loss per round | `loss_history[]` |
| **Leaderboard** | Hospital rankings by reward tokens | `/api/rewards` |
| **Audit Trail** | Blockchain transaction log | `/blockchain-api/api/blockchain/transactions` |

---

## 4. Hero Section — Top Metrics Cards (Lines 56–100)

Four real-time status cards at the top:

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Waiting/     │ │  Current     │ │  Global      │ │  Connected   │
│  Training     │ │  Round       │ │  Accuracy    │ │  Hospitals   │
│  Status       │ │  3/10        │ │  0.7842      │ │  2           │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Card hover animation:**
```css
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(251,191,36,0.12);
}
```

---

## 5. JavaScript — API Integration & Polling

### Core Configuration (Lines 349–351)
```javascript
const API_URL = '';                          // Same-origin (proxied by NGINX)
const BLOCKCHAIN_URL = '/blockchain-api';    // NGINX proxies to :7050
```

### The Polling Loop (Lines 355–365)
```javascript
// Poll every 5 seconds for live data
setInterval(() => {
    loadStatus();           // GET /api/status → top metrics
    loadHospitals();        // GET /api/hospitals → hospital cards
    loadMetricsHistory();   // GET /api/metrics/history → chart data
    loadBlockchainStats();  // GET /blockchain-api/api/blockchain/stats
    loadTransactions();     // GET /blockchain-api/api/blockchain/transactions
    loadRewards();          // GET /api/rewards → leaderboard
}, 5000);
```

### loadStatus() — Top Metrics Update (Lines 370–410)
```javascript
async function loadStatus() {
    const res = await fetch(`${API_URL}/api/status`);
    const data = await res.json();
    
    // Update hero cards
    document.getElementById('status-text').textContent = 
        data.is_training ? 'Training' : 'Waiting for Hospitals';
    document.getElementById('current-round').textContent = 
        `${data.current_round}/${data.total_rounds}`;
    document.getElementById('global-accuracy').textContent = 
        data.global_accuracy.toFixed(4);
    document.getElementById('connected-hospitals').textContent = 
        data.connected_hospitals;
    
    // Update progress bar width
    const pct = data.progress_percentage;
    document.getElementById('progress-fill').style.width = pct + '%';
    document.getElementById('progress-pct').textContent = Math.round(pct) + '%';
}
```

### loadMetricsHistory() — Chart Updates (Lines 420–460)
```javascript
async function loadMetricsHistory() {
    const res = await fetch(`${API_URL}/api/metrics/history`);
    const data = await res.json();
    
    if (data.accuracy_history && data.accuracy_history.length > 0) {
        // Update Chart.js accuracy chart
        accuracyChart.data.labels = data.accuracy_history.map((_, i) => `R${i+1}`);
        accuracyChart.data.datasets[0].data = data.accuracy_history;
        accuracyChart.update();
        
        // Update loss chart
        lossChart.data.labels = data.loss_history.map((_, i) => `R${i+1}`);
        lossChart.data.datasets[0].data = data.loss_history;
        lossChart.update();
    }
}
```

### loadBlockchainStats() — Blockchain Section (Lines 461–482)
```javascript
async function loadBlockchainStats() {
    try {
        const res = await fetch(`${BLOCKCHAIN_URL}/api/blockchain/stats`);
        const stats = await res.json();
        
        document.getElementById('blockchain-blocks').textContent = stats.total_blocks;
        document.getElementById('blockchain-txs').textContent = stats.total_transactions;
        document.getElementById('blockchain-valid').textContent = 
            stats.is_valid ? '✅ Valid' : '❌ Corrupted';
        document.getElementById('blockchain-status').textContent = 'Online';
    } catch (e) {
        document.getElementById('blockchain-status').textContent = 
            'Blockchain service offline';
    }
}
```

**IMPORTANT**: The `BLOCKCHAIN_URL` was changed from `http://${window.location.hostname}:7050` (which failed because port 7050 is firewalled) to `/blockchain-api` (which routes through NGINX on port 80). This was the fix for the "Blockchain service offline" bug.

### loadHospitals() — Hospital Cards
```javascript
async function loadHospitals() {
    const res = await fetch(`${API_URL}/api/hospitals`);
    const data = await res.json();
    
    const container = document.getElementById('hospitals-container');
    container.innerHTML = data.hospitals.map(h => `
        <div class="hospital-card">
            <div class="hospital-header">
                <span class="hospital-name">${h.hospital_name}</span>
                <span class="status-dot ${h.status}"></span>
            </div>
            <div class="hospital-meta">${h.dataset_size} samples · ${h.dataset_type}</div>
            <div class="hospital-status">${h.status}</div>
        </div>
    `).join('');
}
```

---

## 6. Chart.js Configuration

### Accuracy Chart
```javascript
accuracyChart = new Chart(document.getElementById('accuracy-chart'), {
    type: 'line',
    data: { labels: [], datasets: [{
        label: 'Global Accuracy',
        data: [],
        borderColor: '#10b981',        // Green line
        backgroundColor: 'rgba(16,185,129,0.1)',
        tension: 0.4,                  // Smooth curves
        fill: true
    }]},
    options: { scales: { y: { beginAtZero: true, max: 1 }}}
});
```

### Loss Chart
```javascript
lossChart = new Chart(document.getElementById('loss-chart'), {
    type: 'line',
    data: { labels: [], datasets: [{
        label: 'Global Loss',
        data: [],
        borderColor: '#ef4444',        // Red line
        backgroundColor: 'rgba(239,68,68,0.1)',
        tension: 0.4,
        fill: true
    }]}
});
```

---

## 7. Visual Effects & Animations

### Floating Particles Background (Lines 29–32)
```css
.particle { 
    position: absolute; width: 3px; height: 3px; 
    border-radius: 50%; background: var(--yellow); 
    animation: floatUp 12s linear infinite; 
}
@keyframes floatUp { 
    0% { transform: translateY(0); opacity: 0; } 
    10% { opacity: 0.7; } 
    100% { transform: translateY(-110vh); opacity: 0; } 
}
```
20 yellow particles float upward continuously — gives the dashboard a "data flowing" feeling.

### Connection Status Pulse
```css
.status-dot.connected {
    background: #10b981;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(16,185,129,0.7); }
    70% { box-shadow: 0 0 0 10px rgba(16,185,129,0); }
    100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
}
```

### Hero Title Gradient
```css
.hero h1 {
    background: linear-gradient(92deg, #ea580c, #f97316, #fb923c, #ea580c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
```

---

## 8. NGINX Reverse Proxy — `nginx.conf`

```nginx
server {
    listen 80;
    root /var/www/html;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }       # SPA fallback
    location /api/ { proxy_pass http://127.0.0.1:8000; }    # REST API
    location /blockchain-api/ { proxy_pass http://127.0.0.1:7050/; }  # Blockchain
    location /ws { 
        proxy_pass http://127.0.0.1:8001; 
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";              # WebSocket upgrade
    }
}
```

**Why NGINX?** The browser can only access port 80. All internal services (REST on 8000, blockchain on 7050, WebSocket on 8001) are accessed through NGINX reverse proxy paths.

---

## 9. API Endpoints Consumed by Dashboard

| Endpoint | HTTP | Returns | Updates |
|----------|------|---------|---------|
| `/api/status` | GET | `{current_round, total_rounds, global_accuracy, global_loss, is_training, connected_hospitals, blockchain_connected, progress_percentage}` | Hero cards, progress bar |
| `/api/hospitals` | GET | `{hospitals: [{hospital_id, hospital_name, dataset_size, dataset_type, status}]}` | Hospital cards |
| `/api/metrics/history` | GET | `{accuracy_history: [...], loss_history: [...]}` | Chart.js graphs |
| `/api/rewards` | GET | `{hospitals: [{hospital_id, total_rewards, rounds_participated}]}` | Leaderboard tab |
| `/blockchain-api/api/blockchain/stats` | GET | `{total_blocks, total_transactions, is_valid, difficulty}` | Blockchain section |
| `/blockchain-api/api/blockchain/transactions` | GET | `{transactions: [{type, hospital_id, block_index, timestamp}]}` | Audit trail tab |

---

## 10. Presentation Talking Points

### Opening (30 seconds)
"I designed and built the central monitoring dashboard — a single-page application that provides real-time visibility into federated learning training across all hospitals. It shows live accuracy charts, hospital connections, blockchain audit trails, and the reward leaderboard, all updating every 5 seconds."

### Technical Deep Dive (3 minutes)

**Design System:**
"I chose an amber-and-pearl color scheme with the Inter typeface to convey medical professionalism. The design uses CSS custom properties for consistency, subtle glassmorphism effects, and animated floating particles for visual engagement."

**Real-Time Data:**
"The dashboard polls 6 API endpoints every 5 seconds via the Fetch API: training status, hospital list, accuracy/loss history, blockchain statistics, transactions, and reward rankings. Chart.js renders live-updating line charts for accuracy trends and loss curves."

**NGINX Proxy:**
"Since the browser can only reach port 80, I configured NGINX as a reverse proxy with 4 upstream routes: `/api/` to the REST API on port 8000, `/blockchain-api/` to the blockchain on 7050, `/ws` for WebSocket upgrades, and `/` for the static dashboard."

### Live Demo Flow
1. Open `http://54.91.23.82/` → show hero section with live metrics
2. Point at "Connected Hospitals: 2" and the hospital cards
3. Click "Accuracy" tab → show the line chart filling in
4. Click "Leaderboard" tab → show hospital rankings with token counts
5. Click "Audit Trail" tab → show blockchain transactions flowing
6. Scroll to "Blockchain Statistics" → show blocks, transactions, validity

---

## 11. Panel Q&A Preparation

**Q: Why not use React or Vue?**
A: "For a monitoring dashboard with straightforward data binding, vanilla JS with the Fetch API is sufficient and adds zero build complexity. The entire UI is a single 639-line HTML file — no build step, instant deployment, and total control."

**Q: Why poll instead of WebSockets for everything?**
A: "Polling every 5 seconds is simple, resilient to connection drops, and sufficient for federated learning rounds that take minutes each. We have WebSocket infrastructure ready (port 8001 proxied via NGINX) for future real-time push if needed."

**Q: How does the blockchain section work?**
A: "The dashboard fetches from `/blockchain-api/api/blockchain/stats` and `/blockchain-api/api/blockchain/transactions`. NGINX proxies these to the blockchain container on port 7050. If the blockchain container is down, the dashboard gracefully shows 'Blockchain service offline' rather than crashing."

**Q: Is it responsive?**
A: "Yes — the grid layout uses CSS Grid with responsive breakpoints. On mobile, cards stack vertically. On desktop, the metrics grid uses 4 columns. The tab navigation adapts to screen width."

---

## 12. Key Code References

| What to show | File | Lines | Key detail |
|---|---|---|---|
| CSS design tokens | `dashboard/index.html` | 11–23 | `:root` variables |
| Particle animation | `dashboard/index.html` | 29–32 | `@keyframes floatUp` |
| Tab switching JS | `dashboard/index.html` | 355–365 | `setInterval` polling |
| Status card update | `dashboard/index.html` | 370–410 | `loadStatus()` |
| Chart.js integration | `dashboard/index.html` | 420–460 | `loadMetricsHistory()` |
| Blockchain fix | `dashboard/index.html` | 351 | `BLOCKCHAIN_URL = '/blockchain-api'` |
| NGINX proxy | `dashboard/nginx.conf` | 20–53 | All proxy routes |
