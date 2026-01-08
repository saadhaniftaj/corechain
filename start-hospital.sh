#!/bin/bash

# Start Hospital Node Script

set -e

echo "======================================"
echo "CoreChain Hospital Node"
echo "======================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Please create a .env file with the following content:"
    echo ""
    cat .env.hospital.example
    echo ""
    echo "Copy .env.hospital.example to .env and update AGGREGATOR_IP"
    exit 1
fi

# Load .env file
source .env

echo ""
echo "Hospital Configuration:"
echo "  - Hospital ID: $HOSPITAL_ID"
echo "  - Hospital Name: $HOSPITAL_NAME"
echo "  - Aggregator: $AGGREGATOR_IP:$AGGREGATOR_PORT"
echo "  - Dataset: $DATASET_TYPE"
echo ""
echo "======================================"
echo ""

# Start hospital node
echo "Starting hospital node..."
docker-compose -f docker-compose.hospital.yml up --build

echo ""
echo "======================================"
echo "Hospital Node Stopped"
echo "======================================"
