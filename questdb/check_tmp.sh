#!/bin/bash
# Quick check: Is /tmp a volume or tmpfs?

echo "Checking /tmp filesystem type..."
df -h /tmp
echo ""
mountpoint /tmp 2>/dev/null && echo "/tmp is a mountpoint" || echo "/tmp is NOT a mountpoint"
echo ""
mount | grep " /tmp "
