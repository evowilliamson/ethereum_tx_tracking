#!/bin/bash
# Script to migrate QuestDB database from local machine to Railway
# This is the recommended method for moving QuestDB data to Railway

set -e

echo "============================================================"
echo "QuestDB Migration: Local → Railway"
echo "============================================================"
echo ""

# Step 1: Stop QuestDB locally
echo "Step 1: Stopping QuestDB locally..."
if command -v questdb &> /dev/null; then
    STATUS_OUTPUT=$(questdb status 2>&1)
    if echo "$STATUS_OUTPUT" | grep -q "Running"; then
        questdb stop
        echo "✓ QuestDB stopped locally"
    else
        echo "✓ QuestDB already stopped locally"
    fi
else
    echo "⚠ QuestDB not found locally (may already be stopped)"
fi
echo ""

# Step 2: Create backup archive
echo "Step 2: Creating compressed backup archive..."
LOCAL_DB_DIR="$HOME/.dex_trades_extractor/.questdb/db"
BACKUP_FILE="$HOME/questdb_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

if [ ! -d "$LOCAL_DB_DIR" ]; then
    echo "✗ Error: QuestDB data directory not found: $LOCAL_DB_DIR"
    exit 1
fi

cd "$LOCAL_DB_DIR"
tar -czf "$BACKUP_FILE" .
BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "✓ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
echo ""

# Step 3: Instructions for Railway
echo "============================================================"
echo "Step 3: Upload to Railway"
echo "============================================================"
echo ""
echo "Option A: Using Railway CLI (Recommended)"
echo "----------------------------------------"
echo "Run this command to upload the backup to Railway:"
echo ""
echo "  railway run 'cat > /tmp/questdb_backup.tar.gz' < $BACKUP_FILE"
echo ""
echo "Option B: Manual upload via Railway dashboard"
echo "----------------------------------------"
echo "1. Go to Railway dashboard → Your service → Volumes"
echo "2. Use Railway's file upload feature if available"
echo "3. Or use Railway's volume export/import"
echo ""
echo "Option C: Using base64 encoding (for small files)"
echo "----------------------------------------"
echo "If the file is small enough, you can use:"
echo "  base64 $BACKUP_FILE | railway run 'base64 -d > /tmp/questdb_backup.tar.gz'"
echo ""
echo "============================================================"
echo "Step 4: Restore on Railway"
echo "============================================================"
echo ""
echo "After uploading, run these commands in Railway shell:"
echo ""
echo "  # Stop QuestDB"
echo "  questdb stop"
echo ""
echo "  # Navigate to data directory"
echo "  cd /data/questdb"
echo ""
echo "  # Backup existing data (optional)"
echo "  mv . ../questdb_backup_old 2>/dev/null || true"
echo ""
echo "  # Extract the backup"
echo "  tar -xzf /tmp/questdb_backup.tar.gz"
echo ""
echo "  # Verify"
echo "  ls -lah | head -20"
echo ""
echo "  # Start QuestDB"
echo "  questdb start -d /data/questdb"
echo ""
echo "============================================================"
echo "Backup file location: $BACKUP_FILE"
echo "============================================================"

