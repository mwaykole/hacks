#!/bin/bash

set -e

ENGINE=${1:-podman}
FINAL_IMAGE=${2:-"quay.io/mwaykole/test:mnist-multiarch"}
PLATFORMS=${3:-"linux/amd64,linux/arm64,linux/ppc64le"}

BASE_IMAGE="quay.io/mwaykole/test:mnist-8-1"
INTERIM_IMAGE="quay.io/mwaykole/test:mnist-interim"
CONTAINER_NAME="mnist-setup-container"

echo "=========================================="
echo "Multi-arch build configuration:"
echo "Engine: ${ENGINE}"
echo "Base Image: ${BASE_IMAGE}"
echo "Final Image: ${FINAL_IMAGE}"
echo "Platforms: ${PLATFORMS}"
echo "=========================================="

# Pull the base image
echo "Pulling base image..."
$ENGINE pull ${BASE_IMAGE}

# Run container to perform any necessary setup
echo "Starting container for setup..."
$ENGINE rm ${CONTAINER_NAME} --force 2>/dev/null || true
$ENGINE run -d --name ${CONTAINER_NAME} ${BASE_IMAGE} tail -f /dev/null

# Execute any setup commands inside the container (if needed)
# Add your setup commands here, for example:
# $ENGINE exec ${CONTAINER_NAME} /path/to/setup.sh
# $ENGINE exec ${CONTAINER_NAME} pip install additional-package

echo "Waiting for setup to complete..."
sleep 5

# Commit the container to create interim image
echo "Creating interim image..."
$ENGINE commit ${CONTAINER_NAME} ${INTERIM_IMAGE}

# Stop and remove the container
echo "Cleaning up container..."
$ENGINE stop ${CONTAINER_NAME}
$ENGINE rm ${CONTAINER_NAME} --force

# Push interim image to registry
echo "Pushing interim image..."
$ENGINE push ${INTERIM_IMAGE}

# Multi-arch build (Podman vs Docker)
if [[ "$ENGINE" == "podman" ]]; then
    echo "Building multi-arch image using Podman manifest..."
    
    # Remove existing manifest if it exists
    $ENGINE manifest rm ${FINAL_IMAGE} 2>/dev/null || true
    
    # Remove existing image if it exists (not a manifest)
    $ENGINE rmi ${FINAL_IMAGE} 2>/dev/null || true
    
    # Create manifest
    $ENGINE manifest create ${FINAL_IMAGE}
    
    # Build and add each platform to manifest
    IFS=',' read -ra PLATFORM_ARRAY <<< "$PLATFORMS"
    for PLATFORM in "${PLATFORM_ARRAY[@]}"; do
        echo "Building for platform: ${PLATFORM}"
        PLATFORM_TAG="${FINAL_IMAGE}-${PLATFORM//\//-}"
        
        # Remove existing platform image if exists
        $ENGINE rmi ${PLATFORM_TAG} 2>/dev/null || true
        
        $ENGINE build \
            --platform ${PLATFORM} \
            --build-arg BASE_IMAGE=${INTERIM_IMAGE} \
            -f Dockerfile.multiarch \
            -t ${PLATFORM_TAG} \
            .
        
        $ENGINE manifest add ${FINAL_IMAGE} ${PLATFORM_TAG}
    done
    
    # Push manifest
    echo "Pushing multi-arch manifest..."
    $ENGINE manifest push ${FINAL_IMAGE}
    
else
    # Docker buildx approach
    echo "Setting up buildx builder..."
    $ENGINE buildx create --name multiarch-builder --driver docker-container --use 2>/dev/null || $ENGINE buildx use multiarch-builder
    
    echo "Building multi-arch image using Docker buildx..."
    $ENGINE buildx build \
        --platform ${PLATFORMS} \
        --push \
        --build-arg BASE_IMAGE=${INTERIM_IMAGE} \
        -f Dockerfile.multiarch \
        -t ${FINAL_IMAGE} \
        .
fi

echo "=========================================="
echo "Multi-arch build completed successfully!"
echo "Image: ${FINAL_IMAGE}"
echo "Platforms: ${PLATFORMS}"
echo "=========================================="

# Clean up interim image (optional)
# $ENGINE rmi ${INTERIM_IMAGE}

