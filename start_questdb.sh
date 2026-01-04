#!/bin/bash
# Helper script to start QuestDB with custom data directory
# Data directory: ~/.dex_trades_extractor/.questdb/

set -e

QUESTDB_DATA_DIR="$HOME/.dex_trades_extractor/.questdb"

# Create data directory if it doesn't exist
mkdir -p "$QUESTDB_DATA_DIR"

echo "Starting QuestDB..."
echo "Data directory: $QUESTDB_DATA_DIR"
echo ""

# Check if QuestDB binary is available
if command -v questdb &> /dev/null; then
    echo "Starting QuestDB server..."
    echo "  Web console: http://localhost:9000"
    echo "  PostgreSQL wire protocol: localhost:8812"
    echo "  ILP (InfluxDB Line Protocol): localhost:9009"
    echo ""
    
    # Set JAVA_HOME if not already set (required for QuestDB without JRE)
    if [ -z "$JAVA_HOME" ]; then
        # Try to find Java installation
        if [ -d /usr/lib/jvm/java-17-openjdk-amd64 ]; then
            export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
        elif [ -d /usr/lib/jvm/default-java ]; then
            export JAVA_HOME=/usr/lib/jvm/default-java
        else
            JAVA_DIR=$(find /usr/lib/jvm -maxdepth 1 -type d -name "*openjdk*" 2>/dev/null | head -1)
            if [ -n "$JAVA_DIR" ]; then
                export JAVA_HOME="$JAVA_DIR"
            fi
        fi
    fi
    
    # Check if QuestDB is already running
    STATUS=$(questdb status 2>&1)
    if echo "$STATUS" | grep -q "Running"; then
        echo "QuestDB is already running!"
        questdb status
        exit 0
    fi
    
    questdb start -d "$QUESTDB_DATA_DIR"
    
    echo ""
    echo "✓ QuestDB started successfully!"
    echo ""
    echo "To view logs: questdb status"
    echo "To stop: ./stop_questdb.sh"
    echo "Or manually: questdb stop"
    
else
    echo "Error: QuestDB not found!"
    echo ""
    echo "Installation:"
    echo "  1. Visit: https://questdb.io/get-questdb/"
    echo "  2. Follow installation instructions"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi
