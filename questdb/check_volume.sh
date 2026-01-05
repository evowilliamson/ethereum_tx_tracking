#!/bin/bash
# Script to verify /data is a permanent volume in Railway
# Run this on the Railway host

echo "============================================================"
echo "Checking /data Volume Configuration"
echo "============================================================"
echo ""

# 1. Check if /data exists
echo "1. Checking if /data directory exists..."
if [ -d "/data" ]; then
    echo "   ✓ /data directory exists"
else
    echo "   ✗ /data directory does NOT exist"
    exit 1
fi
echo ""

# 2. Check if /data is a mount point (separate filesystem)
echo "2. Checking if /data is a mount point..."
MOUNT_INFO=$(df -h /data 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✓ /data is a separate filesystem (mounted volume)"
    echo ""
    echo "   Mount information:"
    echo "$MOUNT_INFO" | tail -n +2 | awk '{print "   Filesystem: " $1 "\n   Size: " $2 "\n   Used: " $3 "\n   Available: " $4 "\n   Use%: " $5 "\n   Mounted on: " $6}'
else
    echo "   ⚠ /data might not be a separate mount point"
fi
echo ""

# 3. Check mount details
echo "3. Detailed mount information:"
if command -v mountpoint &> /dev/null; then
    if mountpoint -q /data; then
        echo "   ✓ /data is a mount point (confirmed)"
    else
        echo "   ⚠ /data is NOT a mount point (might be regular directory)"
    fi
else
    echo "   (mountpoint command not available, using alternative check)"
    MOUNT_TYPE=$(findmnt -n -o FSTYPE /data 2>/dev/null)
    if [ -n "$MOUNT_TYPE" ]; then
        echo "   ✓ /data is mounted as: $MOUNT_TYPE"
    else
        echo "   ⚠ Could not determine mount type"
    fi
fi
echo ""

# 4. Check /data/questdb specifically
echo "4. Checking /data/questdb..."
if [ -d "/data/questdb" ]; then
    echo "   ✓ /data/questdb exists"
    
    # Check if it has data
    DATA_SIZE=$(du -sh /data/questdb 2>/dev/null | cut -f1)
    echo "   Data size: $DATA_SIZE"
    
    # List contents
    echo "   Contents:"
    ls -lah /data/questdb | head -10 | awk '{print "     " $0}'
else
    echo "   ⚠ /data/questdb does not exist (will be created on first run)"
fi
echo ""

# 5. Check if it's writable
echo "5. Testing write access..."
TEST_FILE="/data/.volume_test_$(date +%s)"
if touch "$TEST_FILE" 2>/dev/null; then
    echo "   ✓ /data is writable"
    rm -f "$TEST_FILE"
else
    echo "   ✗ /data is NOT writable"
fi
echo ""

# 6. Check Railway-specific indicators
echo "6. Railway-specific checks:"
if [ -d "/data" ] && [ "$(stat -f -c %T /data 2>/dev/null || stat -c %T /data 2>/dev/null)" != "tmpfs" ]; then
    echo "   ✓ /data is not tmpfs (likely persistent volume)"
else
    echo "   ⚠ /data might be tmpfs (temporary)"
fi

# Check for Railway volume indicators
if [ -f "/.railway/volume.json" ] || [ -d "/.railway" ]; then
    echo "   ✓ Railway environment detected"
fi
echo ""

# 7. Summary
echo "============================================================"
echo "Summary:"
echo "============================================================"
if mountpoint -q /data 2>/dev/null || [ -n "$(findmnt -n -o FSTYPE /data 2>/dev/null)" ]; then
    echo "✓ /data appears to be a MOUNTED VOLUME (persistent)"
    echo ""
    echo "This means:"
    echo "  - Data will persist across container restarts"
    echo "  - Data will persist across deployments"
    echo "  - Data is stored separately from container filesystem"
else
    echo "⚠ /data might NOT be a mounted volume"
    echo ""
    echo "This could mean:"
    echo "  - Data might be lost on container restart"
    echo "  - Check Railway dashboard → Volumes section"
    echo "  - Ensure /data is configured as a persistent volume"
fi
echo "============================================================"

