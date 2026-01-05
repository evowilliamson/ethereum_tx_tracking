#!/bin/bash
# Helper script to start QuestDB with custom data directory
# Data directory: ~/.dex_trades_extractor/.questdb/
# Also works on Railway with /data/questdb

set -e

# Use Railway volume if available, otherwise use local directory
if [ -d "/data/questdb" ]; then
    QUESTDB_DATA_DIR="/data/questdb"
else
    QUESTDB_DATA_DIR="$HOME/.dex_trades_extractor/.questdb"
fi

# Create data directory if it doesn't exist
mkdir -p "$QUESTDB_DATA_DIR"

echo "Starting QuestDB..."
echo "Data directory: $QUESTDB_DATA_DIR"
echo ""

# Check if QuestDB binary is available
if command -v questdb &> /dev/null; then
    echo "Configuring system for QuestDB..."
    
    # Set vm.max_map_count (required for QuestDB with large datasets)
    # Recommended: 1048576, minimum: 65530
    CURRENT_MAX_MAP=$(sysctl -n vm.max_map_count 2>/dev/null || echo "0")
    if [ "$CURRENT_MAX_MAP" -lt 1048576 ]; then
        echo "  Setting vm.max_map_count to 1048576 (current: $CURRENT_MAX_MAP)..."
        if sysctl -w vm.max_map_count=1048576 2>/dev/null; then
            echo "  ✓ vm.max_map_count updated"
        else
            echo "  ⚠ Warning: Could not set vm.max_map_count (may require root)"
            echo "    Current value: $CURRENT_MAX_MAP (recommended: 1048576)"
        fi
    else
        echo "  ✓ vm.max_map_count is already sufficient: $CURRENT_MAX_MAP"
    fi
    
    # Set JAVA_HOME if not already set (required for QuestDB without JRE)
    if [ -z "$JAVA_HOME" ]; then
        # Method 1: Use readlink to find Java from java binary (works on Railway)
        if command -v java &> /dev/null; then
            JAVA_PATH=$(readlink -f /usr/bin/java 2>/dev/null | sed "s:bin/java::")
            if [ -n "$JAVA_PATH" ] && [ -d "$JAVA_PATH" ]; then
                export JAVA_HOME="$JAVA_PATH"
            fi
        fi
        
        # Method 2: Try common Java installation paths (fallback)
        if [ -z "$JAVA_HOME" ]; then
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
        
        if [ -n "$JAVA_HOME" ]; then
            echo "  ✓ JAVA_HOME set to: $JAVA_HOME"
        else
            echo "  ⚠ Warning: JAVA_HOME not set (QuestDB may not start)"
        fi
    else
        echo "  ✓ JAVA_HOME already set: $JAVA_HOME"
    fi
    
    echo ""
    echo "Starting QuestDB server..."
    echo "  Web console: http://localhost:9000"
    echo "  PostgreSQL wire protocol: localhost:8812"
    echo "  ILP (InfluxDB Line Protocol): localhost:9009"
    echo ""
    
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
