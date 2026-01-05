#!/bin/bash
# Backup QuestDB data and check current storage location
# Run this on Railway host while process is running

set -e

echo "============================================================"
echo "QuestDB Data Backup and Location Check"
echo "============================================================"
echo ""

# Find where QuestDB is actually storing data
echo "1. Finding QuestDB data location..."
echo ""

# Check common QuestDB data locations
POSSIBLE_LOCATIONS=(
    "/data/questdb"
    "/root/.questdb"
    "/root/.dex_trades_extractor/.questdb"
    "/var/lib/questdb"
    "/app/.questdb"
)

QUESTDB_DATA_DIR=""
for loc in "${POSSIBLE_LOCATIONS[@]}"; do
    if [ -d "$loc" ] && [ -n "$(ls -A $loc 2>/dev/null)" ]; then
        echo "   Found data at: $loc"
        SIZE=$(du -sh "$loc" 2>/dev/null | cut -f1)
        echo "   Size: $SIZE"
        
        # Check if it's a mountpoint
        if mountpoint -q "$loc" 2>/dev/null; then
            echo "   ✓ This IS a mountpoint (persistent volume)"
            QUESTDB_DATA_DIR="$loc"
            break
        else
            echo "   ⚠ This is NOT a mountpoint (temporary)"
            if [ -z "$QUESTDB_DATA_DIR" ]; then
                QUESTDB_DATA_DIR="$loc"
            fi
        fi
        echo ""
    fi
done

if [ -z "$QUESTDB_DATA_DIR" ]; then
    echo "   ⚠ Could not find QuestDB data directory"
    echo "   Checking running QuestDB process..."
    
    # Try to find from process
    if pgrep -f questdb > /dev/null; then
        echo "   QuestDB process is running"
        # Check process working directory or data dir from command line
        QUESTDB_PID=$(pgrep -f questdb | head -1)
        if [ -n "$QUESTDB_PID" ]; then
            PROC_CWD=$(readlink -f /proc/$QUESTDB_PID/cwd 2>/dev/null || echo "")
            echo "   Process working directory: $PROC_CWD"
        fi
    fi
else
    echo ""
    echo "   Using data directory: $QUESTDB_DATA_DIR"
fi

echo ""
echo "============================================================"
echo "2. Checking all mount points..."
echo "============================================================"
echo ""
echo "All mounted filesystems:"
df -h | grep -E "(Filesystem|/data|questdb|overlay)" || df -h
echo ""

echo "All mount points:"
mount | grep -E "(/data|questdb)" || echo "   (No /data or questdb mounts found)"
echo ""

echo "============================================================"
echo "3. Creating backup..."
echo "============================================================"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Since both /data and /tmp are likely temporary, we need to download immediately
# Create backup in /tmp temporarily, then download it
BACKUP_FILE="/tmp/questdb_backup_${TIMESTAMP}.tar.gz"

if [ -n "$QUESTDB_DATA_DIR" ] && [ -d "$QUESTDB_DATA_DIR" ]; then
    echo "Backing up: $QUESTDB_DATA_DIR"
    echo "To: $BACKUP_FILE"
    echo ""
    
    # Create backup
    tar -czf "$BACKUP_FILE" -C "$(dirname $QUESTDB_DATA_DIR)" "$(basename $QUESTDB_DATA_DIR)" 2>&1 | while read line; do
        echo "   $line"
    done
    
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
        echo ""
        echo "✓ Backup created successfully!"
        echo "  File: $BACKUP_FILE"
        echo "  Size: $BACKUP_SIZE"
        echo ""
        echo "⚠ IMPORTANT: /tmp is TEMPORARY - download backup IMMEDIATELY!"
        echo ""
        echo "Download command (run from your local machine):"
        echo "  railway run 'cat $BACKUP_FILE' > questdb_backup_${TIMESTAMP}.tar.gz"
        echo ""
        echo "Or stream directly (no /tmp needed):"
        echo "  railway run 'tar -czf - -C $(dirname $QUESTDB_DATA_DIR) $(basename $QUESTDB_DATA_DIR)' > questdb_backup_${TIMESTAMP}.tar.gz"
    else
        echo "✗ Backup failed!"
    fi
else
    echo "⚠ Cannot create backup - QuestDB data directory not found"
    echo ""
    echo "Please check:"
    echo "  1. Is QuestDB running?"
    echo "  2. Where is QuestDB storing data?"
    echo "  3. Check Railway dashboard for volume configuration"
fi

echo ""
echo "============================================================"
echo "4. Current Data Status"
echo "============================================================"
echo ""

if [ -n "$QUESTDB_DATA_DIR" ]; then
    if mountpoint -q "$QUESTDB_DATA_DIR" 2>/dev/null; then
        echo "✓ Data is on a PERSISTENT VOLUME"
        echo "  Location: $QUESTDB_DATA_DIR"
        echo "  Status: Safe - data will persist"
    else
        echo "⚠ Data is on TEMPORARY storage"
        echo "  Location: $QUESTDB_DATA_DIR"
        echo "  Status: At risk - will be lost on restart"
        echo ""
        echo "ACTION REQUIRED:"
        echo "  1. Add volume in Railway dashboard"
        echo "  2. Restore backup to volume location"
        echo "  3. Or let process continue (if it can resume)"
    fi
else
    echo "⚠ Could not determine data location"
fi

echo ""
echo "============================================================"

