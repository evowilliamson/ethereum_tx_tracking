#!/bin/bash
# Setup git repository on Railway in persistent volume
# Run this in Railway SSH shell

set -e

REPO_URL="https://github.com/evowilliamson/evm-dex-trades-extractor.git"
REPO_DIR="/data/evm-dex-trades-extractor"

echo "Setting up git repository on Railway..."
echo "Repository: $REPO_URL"
echo "Target directory: $REPO_DIR"
echo ""

# Check if /data exists (Railway persistent volume)
if [ ! -d "/data" ]; then
    echo "⚠ Warning: /data directory not found"
    echo "  Railway volumes should be mounted at /data"
    echo "  Creating /data directory..."
    mkdir -p /data
fi

# Clone or update repository
if [ -d "$REPO_DIR/.git" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd "$REPO_DIR"
    git pull origin main
    echo "✓ Repository updated"
else
    echo "Cloning repository..."
    cd /data
    git clone "$REPO_URL" "$REPO_DIR"
    echo "✓ Repository cloned"
fi

echo ""
echo "Repository location: $REPO_DIR"
echo ""
echo "To use the repository:"
echo "  cd $REPO_DIR"
echo "  git pull origin main  # Pull latest changes"
echo ""




