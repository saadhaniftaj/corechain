#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════╗"
echo "║     CoreChain Hospital Node v1.0             ║"
echo "║     Federated Learning Client                ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# --- Validate required env vars ---
HOSPITAL_ID="${HOSPITAL_ID:-hospital_1}"
HOSPITAL_NAME="${HOSPITAL_NAME:-General Hospital}"
AGGREGATOR_IP="${AGGREGATOR_IP:-}"
AGGREGATOR_PORT="${AGGREGATOR_PORT:-50051}"
FLOWER_PORT="${FLOWER_PORT:-8080}"
DATASET_TYPE="${DATASET_TYPE:-shenzhen}"

if [ -z "$AGGREGATOR_IP" ]; then
    echo "❌ ERROR: AGGREGATOR_IP is not set."
    echo ""
    echo "Usage:"
    echo "  docker run -e AGGREGATOR_IP=<IP> -e HOSPITAL_ID=hospital_1 -v /path/to/data:/data corechain-hospital"
    echo ""
    exit 1
fi

echo "  Hospital ID:    $HOSPITAL_ID"
echo "  Hospital Name:  $HOSPITAL_NAME"
echo "  Aggregator:     $AGGREGATOR_IP:$FLOWER_PORT (Flower)"
echo "  gRPC Port:      $AGGREGATOR_PORT"
echo "  Dataset Type:   $DATASET_TYPE"
echo ""

# --- Check data mount ---
if [ -d "/data" ] && [ "$(ls -A /data 2>/dev/null)" ]; then
    IMAGE_COUNT=$(find /data -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) 2>/dev/null | wc -l)
    if [ "$IMAGE_COUNT" -gt 0 ]; then
        echo "✅ Dataset mounted at /data ($IMAGE_COUNT images found)"
    else
        echo "⚠️  /data is mounted but no images found. Using synthetic demo data."
    fi
else
    echo "⚠️  No dataset mounted at /data. Using synthetic demo data."
    echo "   To mount your data, add: -v /path/to/xrays:/data"
fi
echo ""

# --- Launch ---
echo "🚀 Starting hospital node..."
exec python src/main.py
