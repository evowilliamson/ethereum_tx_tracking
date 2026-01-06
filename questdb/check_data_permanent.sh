#!/bin/bash
# Simple script to check if /data is a permanent volume
# Run this on Railway host

echo "============================================================"
echo "Checking if /data is a Permanent Volume"
echo "============================================================"
echo ""

# 1. Check if /data exists
echo "1. Does /data exist?"
if [ -d "/data" ]; then
    echo "   ✓ Yes, /data directory exists"
else
    echo "   ✗ No, /data does not exist"
    exit 1
fi
echo ""

# 2. Check filesystem type
echo "2. What filesystem is /data on?"
FS_INFO=$(df -h /data 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$FS_INFO"
    echo ""
    FS_TYPE=$(df -T /data 2>/dev/null | tail -1 | awk '{print $2}')
    if [ -n "$FS_TYPE" ]; then
        echo "   Filesystem type: $FS_TYPE"
        if [ "$FS_TYPE" = "overlay" ]; then
            echo "   ⚠ This is the container's overlay filesystem (NOT persistent)"
        elif [ "$FS_TYPE" = "tmpfs" ]; then
            echo "   ⚠ This is tmpfs (temporary, in RAM)"
        else
            echo "   ? Unknown filesystem type"
        fi
    fi
else
    echo "   ✗ Could not determine filesystem"
fi
echo ""

# 3. Check if it's a mountpoint
echo "3. Is /data a mountpoint (separate volume)?"
if command -v mountpoint &> /dev/null; then
    if mountpoint -q /data 2>/dev/null; then
        echo "   ✓ YES - /data IS a mountpoint (likely persistent volume)"
        IS_MOUNTPOINT=true
    else
        echo "   ✗ NO - /data is NOT a mountpoint (likely temporary)"
        IS_MOUNTPOINT=false
    fi
else
    # Alternative check using findmnt
    if command -v findmnt &> /dev/null; then
        MOUNT_INFO=$(findmnt /data 2>/dev/null)
        if [ -n "$MOUNT_INFO" ]; then
            echo "   ✓ YES - /data IS mounted (likely persistent volume)"
            echo ""
            echo "   Mount details:"
            echo "$MOUNT_INFO"
            IS_MOUNTPOINT=true
        else
            echo "   ✗ NO - /data is NOT mounted (likely temporary)"
            IS_MOUNTPOINT=false
        fi
    else
        echo "   ? Cannot determine (mountpoint/findmnt commands not available)"
        IS_MOUNTPOINT=unknown
    fi
fi
echo ""

# 4. Check mount details
echo "4. Mount information for /data:"
mount | grep " /data " || echo "   (No specific mount found for /data)"
echo ""

# 5. Summary
echo "============================================================"
echo "SUMMARY:"
echo "============================================================"
if [ "$IS_MOUNTPOINT" = "true" ]; then
    echo "✓ /data IS a permanent volume"
    echo ""
    echo "This means:"
    echo "  - Data in /data will persist across container restarts"
    echo "  - Data in /data will persist across deployments"
    echo "  - Your data is SAFE"
elif [ "$IS_MOUNTPOINT" = "false" ]; then
    echo "✗ /data is NOT a permanent volume"
    echo ""
    echo "This means:"
    echo "  - Data in /data will be LOST on container restart"
    echo "  - Data in /data will be LOST on deployment"
    echo "  - Your data is AT RISK"
    echo ""
    echo "ACTION NEEDED:"
    echo "  - Go to Railway Dashboard → Your Service → Settings → Volumes"
    echo "  - Add a volume mounted at /data"
else
    echo "? Could not determine if /data is permanent"
    echo ""
    echo "Please check Railway Dashboard → Settings → Volumes"
fi
echo "============================================================"



