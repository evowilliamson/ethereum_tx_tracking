# Deployment Checklist - QuestDB Docker to Railway

## Quick Answers

✅ **Git committed/pushed?** → NO (needs to be done)  
✅ **Stop top1000 process?** → YES (safe to stop, resume works)  
✅ **Stop DB?** → YES (will be replaced by Docker)  
✅ **Create new service?** → NO (update existing `just-shell` service)  
✅ **Data safe?** → YES (volume persists at `/data/questdb`)

---

## Current Status

- ✅ Docker image: Built and tested locally
- ❌ Git: Not committed/pushed
- ⚠️ Process: Top1000 running (needs to stop)
- ⚠️ QuestDB: Running as binary (will be replaced)

---

## Step-by-Step Actions

### 1. Commit Docker Changes to Git

**Staged files (ready to commit):**
- `questdb/` directory (Docker setup)
- `CONTEXT.md` (project context)
- `RAILWAY_DOCKER_DEPLOYMENT.md` (deployment guide)

**To commit:**
```bash
git commit -m "Add QuestDB Docker setup (built and tested, ready for Railway deployment)"
git push origin main
```

**Other modified files** (not staged):
- Various scripts (DEPLOYMENT.md, check_top1000_progress.py, etc.)
- Decide if you want to commit these separately or with Docker changes

---

### 2. Stop Top1000 Process on Railway

**Option A: SSH and stop gracefully**
```bash
railway shell
# Find process
ps aux | grep download_cryptocompare
# Kill it
kill <PID>
```

**Option B: Let it finish current coin**
- Monitor logs: `railway logs`
- Wait for current coin to complete
- Then proceed with deployment

**Safe to stop:** Resume command will continue from last processed coin (DASH, index 150)

---

### 3. Update Railway Service Configuration

1. Go to Railway Dashboard → `just-shell` service
2. **Settings → Build:**
   - Dockerfile Path: `questdb/Dockerfile`
   - Build Context: `questdb/` (check Railway docs for correct syntax)
   
3. **Settings → Volumes:**
   - Verify: `/data/questdb` is mounted (already configured)

4. **Settings → Deploy:**
   - Start Command: (empty or `/usr/local/bin/entrypoint.sh`)

5. **Settings → Networking:**
   - Port: 80 (should auto-detect)

---

### 4. Deploy

**Automatic (recommended):**
- Push to git triggers Railway auto-deploy
- Monitor in Railway dashboard

**Manual:**
- Click "Deploy" button in Railway

---

### 5. Verify Deployment

```bash
# Check logs
railway logs

# Test QuestDB
railway run curl http://localhost:80/ping
# Should return: OK

# Verify data persisted
railway run ls -lh /data/questdb/db/
# Should show ~824MB of data
```

---

### 6. Restart Top1000 Process

```bash
railway run python3 download_cryptocompare_hourly.py resume
```

---

## Important Notes

### Data Safety ✅
- Volume `/data/questdb` is persistent
- 824MB of data will survive deployment
- No data migration needed

### Process Safety ✅
- Top1000 process can be stopped safely
- Resume command continues from last coin
- Last processed: DASH (index 150/1000)

### Deployment Safety ✅
- Docker setup tested locally
- Volume mount same as before
- Entrypoint script handles setup

---

## Rollback Plan

If something goes wrong:
1. Stop Docker deployment
2. Reinstall QuestDB binary (previous method)
3. Data is still in volume
4. Restart services

---

## Recommended Order

1. ✅ Commit and push Docker changes (do this first)
2. ⏸️ Stop top1000 process (optional - can let it finish)
3. ⚙️ Update Railway service configuration
4. 🚀 Deploy (automatic via git push, or manual)
5. ✅ Verify deployment
6. 🔄 Restart top1000 process

---

## Questions?

See `RAILWAY_DOCKER_DEPLOYMENT.md` for detailed guide.

