#!/bin/bash
# Railway QuestDB Setup Script
# Sets vm.max_map_count and JAVA_HOME automatically on SSH login

# Set vm.max_map_count (required for QuestDB with large datasets)
sysctl -w vm.max_map_count=1048576 2>/dev/null || true

# Set JAVA_HOME if not already set
if [ -z "$JAVA_HOME" ]; then
    JAVA_PATH=$(readlink -f /usr/bin/java 2>/dev/null | sed "s:bin/java::")
    if [ -n "$JAVA_PATH" ]; then
        export JAVA_HOME="$JAVA_PATH"
    fi
fi

echo "✓ Railway environment configured:"
echo "  vm.max_map_count: $(sysctl -n vm.max_map_count 2>/dev/null || echo 'N/A')"
echo "  JAVA_HOME: ${JAVA_HOME:-'Not set'}"

