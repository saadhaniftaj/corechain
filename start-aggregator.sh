#!/bin/bash

# Quick Start Script for CoreChain
# Starts all services on the aggregator laptop

set -e

echo "======================================"
echo "CoreChain Quick Start"
echo "======================================"

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "localhost")
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}' || echo "localhost")
fi

echo ""
echo "Aggregator IP Address: $LOCAL_IP"
echo ""
echo "⚠️  IMPORTANT: Hospital nodes should use this IP address"
echo "   Update AGGREGATOR_IP=$LOCAL_IP in hospital .env files"
echo ""
echo "======================================"
echo ""

# Check if setup has been run
if [ ! -f "shared/corechain_pb2.py" ]; then
    echo "Running setup first..."
    ./setup.sh
    echo ""
fi

# Start services
echo "Starting CoreChain services..."
echo ""

docker-compose -f docker-compose.aggregator.yml up --build

echo ""
echo "======================================"
echo "CoreChain Stopped"
echo "======================================"
