#!/bin/bash

# CoreChain Setup Script
# Generates Protocol Buffers and prepares the environment

set -e

echo "======================================"
echo "CoreChain Setup Script"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

echo "✓ Docker found"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

echo "✓ Docker Compose found"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/tb_dataset
mkdir -p models
mkdir -p blockchain/data
mkdir -p shared
echo "✓ Directories created"

# Generate Protocol Buffers
echo ""
echo "Generating Protocol Buffers..."

# Install grpcio-tools if not already installed
pip3 install grpcio-tools --quiet || true

# Generate protobuf files
python3 -m grpc_tools.protoc \
    -I.proto \
    --python_out=./shared \
    --grpc_python_out=./shared \
    .proto/corechain.proto

if [ -f "shared/corechain_pb2.py" ]; then
    echo "✓ Protocol Buffers generated successfully"
else
    echo "✗ Failed to generate Protocol Buffers"
    exit 1
fi

# Create __init__.py in shared if it doesn't exist
if [ ! -f "shared/__init__.py" ]; then
    touch shared/__init__.py
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. For Aggregator (Main Laptop):"
echo "   docker-compose -f docker-compose.aggregator.yml up --build"
echo ""
echo "2. For Hospital Nodes (Other Laptops):"
echo "   - Copy .env.hospital.example to .env"
echo "   - Update AGGREGATOR_IP with the aggregator's IP address"
echo "   - Run: docker-compose -f docker-compose.hospital.yml up --build"
echo ""
echo "3. Access Dashboard:"
echo "   http://<aggregator-ip>:8000/api/training/status"
echo ""
echo "======================================"
