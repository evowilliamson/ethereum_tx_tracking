#!/bin/bash
# Commands to run in Railway shell to restore QuestDB backup

echo "============================================================"
echo "QuestDB Restore on Railway"
echo "============================================================"
echo ""

# Google Drive direct download link (converted from view link)
FILE_ID="1_vkGVnI6ZmGkkZ2qau1DjL9un2ODyx1-"
DOWNLOAD_URL="https://drive.google.com/uc?export=download&id=${FILE_ID}"

echo "Step 1: Download backup from Google Drive..."
echo "URL: $DOWNLOAD_URL"
echo ""

# Download the file
cd /tmp
echo "Downloading backup file..."
wget --no-check-certificate "$DOWNLOAD_URL" -O questdb_backup.tar.gz

# If wget fails due to Google Drive confirmation, try with gdown or curl
if [ ! -f questdb_backup.tar.gz ] || [ ! -s questdb_backup.tar.gz ]; then
    echo "⚠ wget failed, trying alternative method..."
    # Google Drive sometimes requires confirmation for large files
    # Try with curl and handle the confirmation page
    curl -L "https://drive.google.com/uc?export=download&id=${FILE_ID}" -o questdb_backup.tar.gz
fi

# Verify download
if [ -f questdb_backup.tar.gz ] && [ -s questdb_backup.tar.gz ]; then
    FILE_SIZE=$(du -sh questdb_backup.tar.gz | cut -f1)
    echo "✓ Downloaded: questdb_backup.tar.gz ($FILE_SIZE)"
else
    echo "✗ Download failed!"
    exit 1
fi

echo ""
echo "Step 2: Stop QuestDB..."
questdb stop || echo "QuestDB not running or already stopped"

echo ""
echo "Step 3: Backup existing data (optional)..."
cd /data/questdb
if [ -d . ] && [ "$(ls -A . 2>/dev/null)" ]; then
    mv . ../questdb_backup_old_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    echo "✓ Existing data backed up"
else
    echo "No existing data to backup"
fi

echo ""
echo "Step 4: Extract backup..."
tar -xzf /tmp/questdb_backup.tar.gz

echo ""
echo "Step 5: Verify files..."
ls -lah | head -20

echo ""
echo "Step 6: Start QuestDB..."
questdb start -d /data/questdb

echo ""
echo "============================================================"
echo "✓ Restore complete!"
echo "============================================================"
echo ""
echo "Verify with:"
echo "  python3 -c \"from questdb import get_questdb_connection; conn = get_questdb_connection(); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM crypto_hourly'); print(f'Total rows: {cur.fetchone()[0]}'); conn.close()\""
echo ""




