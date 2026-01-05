# Testing QuestDB Docker Setup

Step-by-step guide to test the QuestDB Docker container locally.

## Prerequisites

- Docker installed
- Docker Compose installed (optional, but recommended)

## Step 1: Build the Image

```bash
cd questdb
docker build -t questdb:latest .
```

**Expected output:**
- Downloads Java base image
- Downloads QuestDB
- Copies config and entrypoint
- Creates image successfully

**Check if it worked:**
```bash
docker images | grep questdb
```

## Step 2: Test with Docker Compose (Recommended)

```bash
cd questdb
docker-compose up
```

**What to look for:**
- Entrypoint script runs
- Symlink is created: `~/.questdb -> /data/questdb`
- Config file is copied
- QuestDB starts successfully
- No errors

**Expected startup output:**
```
============================================================
QuestDB Container Startup
============================================================
Creating symlink: ~/.questdb -> /data/questdb
Copying configuration file to volume...
✓ Configuration file copied
✓ Configuration file found at ~/.questdb/conf/server.conf
Starting QuestDB...
```

## Step 3: Verify QuestDB is Running

**In another terminal, check:**
```bash
# Check if container is running
docker ps | grep questdb

# Check logs
docker-compose logs questdb

# Check if QuestDB is responding
curl http://localhost:80/ping
# Should return: OK
```

## Step 4: Test Web Console

Open in browser:
```
http://localhost:80
```

You should see the QuestDB web console.

## Step 5: Test PostgreSQL Port (8812)

```bash
# Test connection (if you have psql)
psql -h localhost -p 8812 -U admin -d qdb

# Or test with Python
python3 -c "
from questdb import get_questdb_connection
conn = get_questdb_connection()
if conn:
    print('✓ Connected to QuestDB')
    conn.close()
else:
    print('✗ Failed to connect')
"
```

## Step 6: Test Configuration (Port 80)

**Verify port 80 is configured:**
```bash
# Check what port QuestDB is listening on
docker exec questdb netstat -tlnp | grep :80

# Should show QuestDB listening on port 80
```

## Step 7: Test Data Persistence

**1. Create some test data:**
```bash
# Connect and create a test table
docker exec -it questdb questdb -d ~/.questdb
# Then in QuestDB console, run:
# CREATE TABLE test (x INT);
# INSERT INTO test VALUES (1);
```

**2. Stop container:**
```bash
docker-compose down
```

**3. Restart container:**
```bash
docker-compose up -d
```

**4. Verify data persisted:**
```bash
# Check if data is still there
docker exec questdb ls -la /data/questdb/db/
# Should show database files
```

## Step 8: Test Entrypoint Script Manually

```bash
# Run container without starting QuestDB
docker run -it --rm questdb:latest /bin/bash

# Inside container, check:
ls -la ~/.questdb
cat ~/.questdb/conf/server.conf
# Should show symlink and config file
```

## Step 9: Test with Custom Port (if needed)

If you want to test with port 9000 instead of 80 locally:

**Edit `conf/server.conf`:**
```
http.bind.to=0.0.0.0:9000
```

**Rebuild and test:**
```bash
docker-compose down
docker-compose build
docker-compose up
```

**Access at:** http://localhost:9000

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs questdb

# Check if ports are available
netstat -tlnp | grep -E ":(80|8812|9009)"
```

### Config file not found
```bash
# Check if config was copied
docker exec questdb ls -la /opt/questdb-config/
docker exec questdb ls -la ~/.questdb/conf/
```

### Port 80 already in use
```bash
# Use different port mapping
# Edit docker-compose.yml:
ports:
  - "8080:80"  # Map host 8080 to container 80
```

### Volume not working
```bash
# Check volume
docker volume ls
docker volume inspect questdb_questdb_data

# Check mount
docker exec questdb df -h /data/questdb
docker exec questdb mountpoint /data/questdb
```

## Quick Test Script

```bash
#!/bin/bash
# Quick test script

echo "Building image..."
docker build -t questdb:latest questdb/

echo "Starting container..."
docker-compose -f questdb/docker-compose.yml up -d

echo "Waiting for QuestDB to start..."
sleep 10

echo "Testing connection..."
curl -f http://localhost:80/ping && echo "✓ QuestDB is running" || echo "✗ QuestDB not responding"

echo "Checking logs..."
docker-compose -f questdb/docker-compose.yml logs --tail=20 questdb
```

## Success Criteria

✅ Image builds without errors
✅ Container starts successfully
✅ Entrypoint script runs and creates symlink
✅ Config file is copied to volume
✅ QuestDB starts on port 80
✅ Web console accessible at http://localhost:80
✅ PostgreSQL port 8812 is accessible
✅ Data persists after container restart

## Next Steps

Once local testing passes:
1. Test on Railway (deploy)
2. Verify volume mounting works on Railway
3. Test with your actual Python application
4. Monitor resource usage

