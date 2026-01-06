# Railway Docker Deployment Guide

This guide walks through deploying the QuestDB Docker setup to Railway.

## Current State

- **Service**: `just-shell`
- **QuestDB**: Running as installed binary (not Docker)
- **Volume**: `/data/questdb` (50GB, persistent, 824MB data)
- **Process**: Top 1000 extraction running in resume mode
- **Docker Setup**: ✅ Built and tested locally, ready to deploy

## Deployment Strategy

You have two options:

### Option 1: Update Existing Service (Recommended)

**Pros:**
- Keeps same volume mount (no data migration)
- Simpler - one service to manage
- Same environment variables

**Cons:**
- Requires stopping current QuestDB and top1000 process
- Brief downtime during deployment

**Steps:**
1. Stop the top1000 process (it will be interrupted anyway)
2. Update service to use Docker
3. Deploy
4. Restart top1000 process

### Option 2: Create New Service

**Pros:**
- Can test Docker setup without affecting current service
- No downtime during testing

**Cons:**
- Need to migrate data or use same volume (more complex)
- Two services to manage
- More expensive

**We recommend Option 1** since the volume will persist and data is safe.

---

## Pre-Deployment Checklist

- [ ] Git changes committed and pushed
- [ ] Top1000 process stopped (or let it finish current coin)
- [ ] Current QuestDB data backed up (optional - volume persists)
- [ ] Railway service accessible

---

## Step-by-Step Deployment (Option 1: Update Existing Service)

### Step 1: Commit and Push Git Changes

```bash
# Add all changes
git add CONTEXT.md questdb/ DEPLOYMENT.md

# Commit
git commit -m "Add QuestDB Docker setup (built and tested)"

# Push to main branch
git push origin main
```

### Step 2: Stop Top1000 Process

**Option A: Let it finish current coin (safest)**
- Wait for current coin to complete
- Process will stop naturally

**Option B: Stop immediately**
```bash
# SSH into Railway
railway shell

# Find the process
ps aux | grep download_cryptocompare

# Kill it (if needed)
kill <PID>
```

**Note:** The process will resume from last coin when restarted, so stopping is safe.

### Step 3: Prepare Railway Service

1. Go to Railway Dashboard → Your Project → `just-shell` service
2. Go to **Settings** → **Deploy**
3. Check current configuration:
   - Build command (should auto-detect Dockerfile in `questdb/`)
   - Start command (will need to be updated)

### Step 4: Update Service Configuration

You need to decide: **Run QuestDB only, or QuestDB + Python app?**

**Option A: QuestDB Only (Recommended for now)**
- Service runs QuestDB Docker container
- Volume mount: `/data/questdb`
- Port: 80 (HTTP)

**Option B: Both QuestDB + Python App**
- More complex setup
- Need to manage two processes in one container

**For now, we'll do Option A - QuestDB only.**

### Step 5: Configure Railway Service

1. **Settings → Build:**
   - Builder: Dockerfile
   - Dockerfile Path: `questdb/Dockerfile`
   - Build Context: `questdb/` (or root if Railway supports it)

2. **Settings → Deploy:**
   - Start Command: (leave empty - entrypoint.sh handles it)
   - Or: `/usr/local/bin/entrypoint.sh`

3. **Settings → Volumes:**
   - Ensure volume is mounted at: `/data/questdb`
   - Size: 50GB (already configured)

4. **Settings → Networking:**
   - Port: 80 (auto-detected)
   - No need for public domain (unless you want web console access)

### Step 6: Deploy

**Option A: Automatic (via Git push)**
- Railway auto-builds on push to main
- Monitor in Deployments tab

**Option B: Manual trigger**
- Click "Deploy" button in Railway dashboard

### Step 7: Verify Deployment

1. **Check logs:**
   ```bash
   railway logs
   ```
   Look for:
   - Entrypoint script running
   - Symlink created
   - Config copied
   - QuestDB starting

2. **Test QuestDB:**
   ```bash
   railway run curl http://localhost:80/ping
   # Should return: OK
   ```

3. **Check data persistence:**
   ```bash
   railway run ls -lh /data/questdb/db/
   # Should show existing data files
   ```

### Step 8: Restart Top1000 Process

Once QuestDB is confirmed working:

```bash
railway run python3 download_cryptocompare_hourly.py resume
```

---

## Alternative: Create New Service (Option 2)

If you prefer to test Docker separately:

1. **Create new service:**
   - Railway Dashboard → + New → Database (or Blank Service)
   - Name: `questdb-docker`

2. **Configure:**
   - Dockerfile: `questdb/Dockerfile`
   - Volume: Create new volume or reuse `/data/questdb` (complex)
   - Port: 80

3. **Update Python app connection:**
   - Update `QUESTDB_HOST` env var to new service
   - More complex networking setup

**Not recommended** - Option 1 is simpler.

---

## Post-Deployment

### Verify Everything Works

1. ✅ QuestDB responds to ping
2. ✅ Web console accessible (if public domain added)
3. ✅ Data persisted (824MB still there)
4. ✅ Python app can connect (test with resume command)
5. ✅ Top1000 process can resume

### Update CONTEXT.md

After successful deployment:
- Update "Railway Deployment" section
- Mark Docker as deployed
- Update service status

---

## Troubleshooting

### Build Fails

- Check Dockerfile path is correct
- Verify `questdb/` directory is in git
- Check build logs for errors

### QuestDB Won't Start

- Check logs: `railway logs`
- Verify port 80 is configured
- Check volume mount: `railway run mountpoint /data/questdb`

### Data Missing

- Volume should persist automatically
- Check: `railway run ls -la /data/questdb/db/`
- Verify volume mount in Railway settings

### Can't Connect from Python App

- Verify QuestDB is running: `railway run curl http://localhost:80/ping`
- Check PostgreSQL port 8812 is exposed
- Verify environment variables

---

## Rollback Plan

If something goes wrong:

1. **Stop new deployment**
2. **Reinstall QuestDB binary** (as before)
3. **Restart services**
4. **Data is safe** (volume persists)

---

## Next Steps After Deployment

1. ✅ Verify deployment
2. ✅ Restart top1000 process
3. ✅ Monitor for 24 hours
4. ✅ Update documentation
5. ✅ Consider adding public domain for web console



