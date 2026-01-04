#!/bin/bash
# Setup script for DEX Trades Extractor
# Installs Python dependencies and sets up QuestDB

set -e

echo "============================================================"
echo "DEX Trades Extractor - Setup Script"
echo "============================================================"
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ Warning: Not in a virtual environment"
    echo "  It's recommended to use a virtual environment"
    echo "  Create one with: python3 -m venv venv"
    echo "  Activate with: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Step 1: Install Python dependencies
echo "============================================================"
echo "Step 1: Installing Python dependencies"
echo "============================================================"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "✗ Error: pip is not installed"
    echo "  Please install pip first"
    exit 1
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "Installing required Python packages..."
echo ""

# Note: psycopg2-binary is installed by install_questdb.sh when QuestDB is installed

# Install other common dependencies (if requirements.txt exists)
if [ -f requirements.txt ]; then
    echo ""
    echo "Installing dependencies from requirements.txt..."
    $PIP_CMD install -r requirements.txt
else
    echo ""
    echo "ℹ requirements.txt not found, skipping"
fi

echo ""
echo "✓ Python dependencies installed successfully!"
echo ""

# Step 2: Setup QuestDB
echo "============================================================"
echo "Step 2: Setting up QuestDB"
echo "============================================================"
echo ""

# Create data directory
QUESTDB_DATA_DIR="$HOME/.dex_trades_extractor/.questdb"
mkdir -p "$QUESTDB_DATA_DIR"
echo "✓ Created QuestDB data directory: $QUESTDB_DATA_DIR"
echo ""

# Check if QuestDB is installed
if command -v questdb &> /dev/null; then
    echo "QuestDB binary detected. Setup complete!"
    echo ""
    echo "To start QuestDB, run:"
    echo "  ./start_questdb.sh"
    echo ""
    echo "Or manually:"
    echo "  questdb start -d $QUESTDB_DATA_DIR"
    echo ""
else
    echo "⚠ QuestDB not found."
    echo ""
    echo "Installation options:"
    echo ""
    echo "Option 1: Using installation script (Ubuntu/Debian):"
    echo "  ./install_questdb.sh"
    echo ""
    echo "Option 2: Manual installation:"
    echo "  1. Visit: https://questdb.io/get-questdb/"
    echo "  2. Follow installation instructions"
    echo "  3. Run this script again"
    echo ""
    echo "For now, you can still use the CSV-only mode"
    echo "(QuestDB functionality will be disabled)"
    echo ""
fi

# Step 3: Create file directories
echo "============================================================"
echo "Step 3: Creating data directories"
echo "============================================================"
echo ""

FILES_DIR="$HOME/.dex_trades_extractor/.files"
mkdir -p "$FILES_DIR/price/cryptocompare"
echo "✓ Created data directories:"
echo "  - $FILES_DIR/price/cryptocompare"
echo ""

# Summary
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Summary:"
echo "  ✓ Python dependencies installed"
echo "  ✓ Data directories created"
echo ""
if command -v questdb &> /dev/null; then
    echo "  ✓ QuestDB ready to use"
    echo ""
    echo "Next steps:"
    echo "  1. Start QuestDB: ./start_questdb.sh"
    echo "  2. Run your download scripts"
    echo ""
else
    echo "  ⚠ QuestDB not installed (optional - CSV mode still works)"
    echo ""
    echo "Next steps:"
    echo "  1. Install QuestDB (optional): https://questdb.io/get-questdb/"
    echo "  2. Run your download scripts"
    echo ""
fi

