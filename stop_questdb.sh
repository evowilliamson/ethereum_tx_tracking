#!/bin/bash
# Helper script to stop QuestDB

set -e

echo "Stopping QuestDB..."
echo ""

# Check if QuestDB binary is available
if command -v questdb &> /dev/null; then
    # Check if QuestDB is running
    if questdb status &> /dev/null; then
        echo "Stopping QuestDB server..."
        questdb stop
        echo "✓ QuestDB stopped successfully!"
        echo ""
        echo "To start again: ./start_questdb.sh"
        exit 0
    else
        echo "QuestDB is not running."
        echo ""
        echo "To start QuestDB: ./start_questdb.sh"
        exit 0
    fi
else
    echo "QuestDB not found!"
    echo ""
    echo "Installation:"
    echo "  1. Visit: https://questdb.io/get-questdb/"
    echo "  2. Follow installation instructions"
    echo "  3. Run: ./start_questdb.sh"
    echo ""
    exit 1
fi
