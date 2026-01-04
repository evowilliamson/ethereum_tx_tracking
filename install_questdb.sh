#!/bin/bash
# Install QuestDB on Ubuntu
# This script downloads and installs QuestDB binary

set -e

echo "============================================================"
echo "QuestDB Installation Script for Ubuntu"
echo "============================================================"
echo ""

# Check if running on Ubuntu/Debian
if [ ! -f /etc/os-release ]; then
    echo "✗ Error: Cannot detect operating system"
    exit 1
fi

. /etc/os-release
if [ "$ID" != "ubuntu" ] && [ "$ID" != "debian" ]; then
    echo "⚠ Warning: This script is designed for Ubuntu/Debian"
    echo "  Detected OS: $ID"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if QuestDB is already installed
if command -v questdb &> /dev/null; then
    echo "QuestDB is already installed!"
    questdb version
    echo ""
    read -p "Reinstall anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

# Determine architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    QUESTDB_ARCH="x86_64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    QUESTDB_ARCH="aarch64"
else
    echo "✗ Error: Unsupported architecture: $ARCH"
    echo "  Supported: x86_64, aarch64/arm64"
    exit 1
fi

echo "Detected architecture: $ARCH"
echo ""

# QuestDB version (latest stable)
QUESTDB_VERSION="9.2.3"
# Try with JRE first, fallback to no-jre
QUESTDB_URL_JRE="https://github.com/questdb/questdb/releases/download/${QUESTDB_VERSION}/questdb-${QUESTDB_VERSION}-linux-${QUESTDB_ARCH}.tar.gz"
QUESTDB_URL_NO_JRE="https://github.com/questdb/questdb/releases/download/${QUESTDB_VERSION}/questdb-${QUESTDB_VERSION}-no-jre-bin.tar.gz"

# Installation directory
INSTALL_DIR="/opt/questdb"
BIN_DIR="/usr/local/bin"

echo "Installation details:"
echo "  Version: $QUESTDB_VERSION"
echo "  Architecture: $QUESTDB_ARCH"
echo "  Install directory: $INSTALL_DIR"
echo "  Binary directory: $BIN_DIR"
echo ""

# Check for required tools
if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
    echo "✗ Error: wget or curl is required"
    echo "  Install with: sudo apt-get install wget"
    exit 1
fi

# Check for Java (required for QuestDB)
if ! command -v java &> /dev/null; then
    echo "Java is not installed. QuestDB requires Java."
    echo "Installing Java (OpenJDK 17)..."
    echo ""
    sudo apt-get update
    sudo apt-get install -y openjdk-17-jre-headless
    if ! command -v java &> /dev/null; then
        echo "✗ Error: Failed to install Java"
        echo "  Please install manually: sudo apt install openjdk-17-jre-headless"
        exit 1
    fi
    echo "✓ Java installed successfully"
    echo ""
fi

# Create temporary directory
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "Downloading QuestDB..."
# Try with JRE version first, fallback to no-jre if that fails
cd "$TMP_DIR"
QUESTDB_URL="$QUESTDB_URL_JRE"
echo "  Trying: $QUESTDB_URL"
echo ""

if command -v wget &> /dev/null; then
    wget -q --show-progress "$QUESTDB_URL" -O questdb.tar.gz 2>&1 || {
        echo "  First URL failed, trying no-jre version..."
        QUESTDB_URL="$QUESTDB_URL_NO_JRE"
        echo "  Trying: $QUESTDB_URL"
        wget -q --show-progress "$QUESTDB_URL" -O questdb.tar.gz
    }
else
    curl -L --progress-bar "$QUESTDB_URL" -o questdb.tar.gz 2>&1 || {
        echo "  First URL failed, trying no-jre version..."
        QUESTDB_URL="$QUESTDB_URL_NO_JRE"
        echo "  Trying: $QUESTDB_URL"
        curl -L --progress-bar "$QUESTDB_URL" -o questdb.tar.gz
    }
fi

if [ ! -f questdb.tar.gz ] || [ ! -s questdb.tar.gz ]; then
    echo "✗ Error: Failed to download QuestDB from both URLs"
    echo "  Please check: https://github.com/questdb/questdb/releases"
    exit 1
fi

echo "✓ Download complete"
echo ""

# Extract QuestDB
echo "Extracting QuestDB..."
tar -xzf questdb.tar.gz
echo "✓ Extraction complete"
echo ""

# Find the questdb directory
QUESTDB_DIR=$(find . -maxdepth 1 -type d -name "questdb*" | head -1)
if [ -z "$QUESTDB_DIR" ]; then
    echo "✗ Error: Could not find QuestDB directory in archive"
    exit 1
fi

# Create installation directory
echo "Installing QuestDB..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$QUESTDB_DIR"/* "$INSTALL_DIR"/
echo "✓ Files copied to $INSTALL_DIR"
echo ""

# Create symlink for questdb command
# QuestDB can have different structures, try to find the executable
QUESTDB_BIN=""
if [ -f "$INSTALL_DIR/questdb.sh" ]; then
    QUESTDB_BIN="$INSTALL_DIR/questdb.sh"
elif [ -f "$INSTALL_DIR/bin/questdb.sh" ]; then
    QUESTDB_BIN="$INSTALL_DIR/bin/questdb.sh"
elif [ -f "$INSTALL_DIR/bin/questdb" ]; then
    QUESTDB_BIN="$INSTALL_DIR/bin/questdb"
elif [ -f "$INSTALL_DIR/questdb" ]; then
    QUESTDB_BIN="$INSTALL_DIR/questdb"
fi

if [ -n "$QUESTDB_BIN" ]; then
    sudo ln -sf "$QUESTDB_BIN" "$BIN_DIR/questdb"
    sudo chmod +x "$BIN_DIR/questdb"
    echo "✓ Created symlink: $BIN_DIR/questdb -> $QUESTDB_BIN"
else
    echo "⚠ Warning: Could not find questdb binary"
    echo "  You may need to add $INSTALL_DIR to your PATH"
    echo "  Or create a symlink manually"
fi
echo ""

# Install Python package for QuestDB (psycopg2-binary)
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    # Try with --break-system-packages first (required on newer Ubuntu systems)
    if pip3 install --break-system-packages -q psycopg2-binary 2>/dev/null; then
        echo "✓ Installed psycopg2-binary"
    elif pip3 install -q psycopg2-binary 2>/dev/null; then
        echo "✓ Installed psycopg2-binary"
    else
        echo "⚠ Warning: Failed to install psycopg2-binary via pip3"
        echo "  Install manually with: pip3 install --break-system-packages psycopg2-binary"
        echo "  Or: pip3 install psycopg2-binary"
    fi
elif command -v pip &> /dev/null; then
    if pip install --break-system-packages -q psycopg2-binary 2>/dev/null || pip install -q psycopg2-binary 2>/dev/null; then
        echo "✓ Installed psycopg2-binary"
    else
        echo "⚠ Warning: Failed to install psycopg2-binary via pip"
        echo "  Install manually with: pip install --break-system-packages psycopg2-binary"
    fi
else
    echo "⚠ Warning: pip not found. Please install psycopg2-binary manually:"
    echo "  pip3 install --break-system-packages psycopg2-binary"
fi
echo ""

# Verify installation
if command -v questdb &> /dev/null; then
    echo "✓ QuestDB installed successfully!"
    echo ""
    questdb version
    echo ""
    echo "Installation complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Start QuestDB: ./start_questdb.sh"
    echo "  2. Or manually: questdb start -d ~/.dex_trades_extractor/.questdb"
    echo ""
else
    echo "⚠ Warning: questdb command not found in PATH"
    echo "  You may need to:"
    echo "  1. Add $INSTALL_DIR to your PATH"
    echo "  2. Or use: $INSTALL_DIR/questdb.sh"
    echo ""
fi

