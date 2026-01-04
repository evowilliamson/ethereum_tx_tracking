#!/bin/bash
# Helper script to uninstall QuestDB

set -e

echo "QuestDB Uninstaller"
echo "==================="
echo ""

# Check if QuestDB is running and stop it
if command -v questdb &> /dev/null; then
    STATUS=$(questdb status 2>&1)
    if echo "$STATUS" | grep -q "Running"; then
        echo "QuestDB is currently running. Stopping it..."
        questdb stop
        sleep 2
        echo "✓ QuestDB stopped"
        echo ""
    fi
fi

# Remove symlink from /usr/local/bin
if [ -L /usr/local/bin/questdb ] || [ -f /usr/local/bin/questdb ]; then
    echo "Removing QuestDB binary symlink..."
    sudo rm -f /usr/local/bin/questdb
    echo "✓ Removed /usr/local/bin/questdb"
    echo ""
fi

# Remove installation directory
if [ -d /opt/questdb ]; then
    echo "Removing QuestDB installation directory..."
    sudo rm -rf /opt/questdb
    echo "✓ Removed /opt/questdb"
    echo ""
fi

# Ask about data directory
DATA_DIR="$HOME/.dex_trades_extractor/.questdb"
if [ -d "$DATA_DIR" ]; then
    echo "QuestDB data directory found: $DATA_DIR"
    read -p "Remove data directory as well? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$DATA_DIR"
        echo "✓ Removed $DATA_DIR"
    else
        echo "→ Data directory kept at: $DATA_DIR"
    fi
    echo ""
fi

# Ask about Python package (psycopg2-binary)
if python3 -c "import psycopg2" 2>/dev/null; then
    echo "Python package psycopg2-binary is installed"
    read -p "Remove psycopg2-binary? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if pip3 uninstall -y psycopg2-binary 2>/dev/null || pip3 uninstall --break-system-packages -y psycopg2-binary 2>/dev/null; then
            echo "✓ Removed psycopg2-binary"
        else
            echo "⚠ Warning: Failed to remove psycopg2-binary"
            echo "  Remove manually with: pip3 uninstall psycopg2-binary"
        fi
    else
        echo "→ psycopg2-binary kept (may be used by other applications)"
    fi
    echo ""
fi

echo "✓ QuestDB uninstalled successfully!"
echo ""

