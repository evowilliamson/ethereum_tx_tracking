#!/bin/bash
# QuestDB Docker Entrypoint Script
# Handles symlink setup and configuration file copying

set -e

echo "============================================================"
echo "QuestDB Container Startup"
echo "============================================================"

# Create data directory if it doesn't exist (or use mounted volume)
mkdir -p "${QUESTDB_DATA_DIR:-/data/questdb}"

# Create symlink from ~/.questdb to /data/questdb
# This allows QuestDB to use default path while data persists in volume
if [ ! -L ~/.questdb ]; then
    echo "Creating symlink: ~/.questdb -> ${QUESTDB_DATA_DIR:-/data/questdb}"
    ln -sf "${QUESTDB_DATA_DIR:-/data/questdb}" ~/.questdb
fi

# Create conf directory in volume
mkdir -p "${QUESTDB_DATA_DIR:-/data/questdb}/conf"

# Copy config file from image to volume location
# This ensures config is available at ~/.questdb/conf/server.conf (via symlink)
if [ -f /opt/questdb-config/server.conf ]; then
    echo "Copying configuration file to volume..."
    cp /opt/questdb-config/server.conf "${QUESTDB_DATA_DIR:-/data/questdb}/conf/server.conf"
    echo "✓ Configuration file copied"
fi

# Verify config file exists
if [ -f ~/.questdb/conf/server.conf ]; then
    echo "✓ Configuration file found at ~/.questdb/conf/server.conf"
    echo "  (resolves to ${QUESTDB_DATA_DIR:-/data/questdb}/conf/server.conf)"
else
    echo "⚠ Warning: Configuration file not found!"
fi

# Set JAVA_HOME if not already set
if [ -z "$JAVA_HOME" ]; then
    export JAVA_HOME=/opt/java/openjdk
fi

echo ""
echo "QuestDB Configuration:"
echo "  Data directory: ${QUESTDB_DATA_DIR:-/data/questdb}"
echo "  Config file: ~/.questdb/conf/server.conf"
echo "  HTTP port: 80 (configured in server.conf)"
echo "  PostgreSQL port: 8812"
echo "  ILP port: 9009"
echo "============================================================"
echo ""

# If no command provided, start QuestDB
if [ $# -eq 0 ]; then
    echo "Starting QuestDB..."
    exec questdb start -d ~/.questdb
else
    # Execute the command passed to the container
    exec "$@"
fi

