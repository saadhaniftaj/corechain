#!/bin/bash

# CoreChain All-in-One Docker Build and Push Script
# This script builds and pushes the CoreChain container to Docker Hub

set -e

echo "======================================"
echo "CoreChain Docker Build & Push"
echo "======================================"

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-saadhaniftaj}"
IMAGE_NAME="corechain-allinone"
VERSION="${VERSION:-latest}"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"

echo ""
echo "Configuration:"
echo "  Docker Username: $DOCKER_USERNAME"
echo "  Image Name: $IMAGE_NAME"
echo "  Version: $VERSION"
echo "  Full Image: $FULL_IMAGE_NAME"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

echo "✓ Docker is running"

# Build the image
echo ""
echo "Building Docker image..."
docker build -f Dockerfile.allinone -t $FULL_IMAGE_NAME .

if [ $? -eq 0 ]; then
    echo "✓ Docker image built successfully"
else
    echo "✗ Docker build failed"
    exit 1
fi

# Tag as latest if version is not latest
if [ "$VERSION" != "latest" ]; then
    echo ""
    echo "Tagging as latest..."
    docker tag $FULL_IMAGE_NAME ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
fi

# Login to Docker Hub
echo ""
echo "Logging in to Docker Hub..."
echo "Please enter your Docker Hub credentials:"
docker login

if [ $? -ne 0 ]; then
    echo "✗ Docker login failed"
    exit 1
fi

echo "✓ Logged in to Docker Hub"

# Push the image
echo ""
echo "Pushing image to Docker Hub..."
docker push $FULL_IMAGE_NAME

if [ $? -eq 0 ]; then
    echo "✓ Image pushed successfully"
else
    echo "✗ Docker push failed"
    exit 1
fi

# Push latest tag if created
if [ "$VERSION" != "latest" ]; then
    echo ""
    echo "Pushing latest tag..."
    docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
fi

echo ""
echo "======================================"
echo "Build and Push Complete!"
echo "======================================"
echo ""
echo "Your image is now available at:"
echo "  docker pull $FULL_IMAGE_NAME"
echo ""
echo "To run the container:"
echo "  docker run -d -p 80:80 -p 8080:8080 -p 50051:50051 --name corechain $FULL_IMAGE_NAME"
echo ""
echo "======================================"
