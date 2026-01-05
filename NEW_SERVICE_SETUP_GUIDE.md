# Step-by-Step: Create New Railway Service with GitHub

This guide walks you through creating a new Railway service that:
1. ✅ Connects to your GitHub repo
2. ✅ Uses the Docker setup from `questdb/` directory
3. ✅ Handles the existing volume data

---

## Step 1: Commit and Push Docker Changes to GitHub

**Before creating the service, we need the Docker code in GitHub:**

### Check Current Status
```bash
git status
```

### Stage Docker Files
The Docker files should already be staged. If not:
```bash
git add questdb/ CONTEXT.md NEW_SERVICE_DEPLOYMENT.md NEW_SERVICE_SETUP_GUIDE.md
```

### Commit
```bash
git commit -m "Add QuestDB Docker setup (ready for Railway deployment)"
```

### Push to GitHub
```bash
git push origin main
```

**Verify:** Go to GitHub and check that `questdb/` directory exists in your repo.

---

## Step 2: Create New Service in Railway

### 2.1 Go to Railway Dashboard
1. Open https://railway.app
2. Log in to your account
3. Select your **existing project** (the one with `just-shell` service)

### 2.2 Create New Service
1. Click **"+ New"** button (top right or in the project)
2. Select **"GitHub Repo"** (or "Deploy from GitHub repo")
3. Railway will show your GitHub repositories
4. **Select your repository** (`ethereum_tx_tracking` or whatever it's named)
5. Railway will ask: **"Configure a Service"**
6. Click **"Add Service"** or **"Deploy"**

### 2.3 Service Created
- Railway will create a new service
- It will auto-detect your code
- Name it: `questdb-docker` (or Railway will auto-name it, you can rename later)

---

## Step 3: Configure Service for Docker

### 3.1 Go to Service Settings
1. Click on your new service
2. Go to **"Settings"** tab

### 3.2 Configure Build Settings

**Option A: Railway Auto-Detection (Try First)**
- Railway might auto-detect the Dockerfile
- Check the build logs after first deploy
- If it works, skip to Step 4

**Option B: Manual Configuration (If Needed)**
1. Go to **Settings → Build**
2. **Builder:** Select "Dockerfile"
3. **Dockerfile Path:** `questdb/Dockerfile`
4. **Root Directory:** Leave empty (or set to `questdb/` if Railway requires it)
5. **Build Command:** Leave empty (Docker handles it)

**Note:** Railway's UI might vary. Look for:
- "Dockerfile Path"
- "Build Context"
- "Working Directory"

### 3.3 Configure Deploy Settings
1. Go to **Settings → Deploy**
2. **Start Command:** Leave empty (entrypoint.sh handles it)
   - OR: `/usr/local/bin/entrypoint.sh` if Railway requires a start command
3. **Restart Policy:** "On Failure" (default is fine)

---

## Step 4: Configure Volume (Important!)

Railway volumes are **service-specific**. Here are your options:

### Option A: Create New Volume (Recommended for Testing)

**Why:** Safer to test Docker first, then copy data if needed.

1. Go to **Settings → Volumes**
2. Click **"+ New Volume"**
3. **Name:** `questdb-data` (or any name)
4. **Mount Path:** `/data/questdb`
5. **Size:** 50GB (or smaller if you prefer, can expand later)
6. Click **"Add Volume"**

**Result:** New empty volume, safe to test Docker.

### Option B: Try to Attach Existing Volume (Advanced)

**Railway typically doesn't allow sharing volumes between services**, but you can try:

1. Go to **Settings → Volumes**
2. Look for **"Attach Existing Volume"** (if available)
3. Select the volume from `just-shell` service
4. **Mount Path:** `/data/questdb`

**If this option doesn't exist:** Use Option A (create new volume).

**If it works:** The new service will use the same volume, and data will be accessible.

---

## Step 5: Configure Networking

1. Go to **Settings → Networking**
2. Railway should auto-detect port 80
3. **Port:** 80 (HTTP)
4. **Public Domain (optional):** 
   - You can add a domain like `questdb-docker.up.railway.app`
   - This allows web console access
   - Not required for PostgreSQL connections

---

## Step 6: Deploy

### 6.1 Trigger Deployment

**Option A: Automatic (Git Push)**
- Railway auto-deploys when you push to the connected branch
- Since we already pushed, Railway should start building automatically
- If not, trigger manually (see Option B)

**Option B: Manual Trigger**
1. Go to **"Deployments"** tab
2. Click **"Redeploy"** or **"Deploy"** button
3. Railway will build the Docker image

### 6.2 Monitor Build

1. Go to **"Deployments"** tab
2. Click on the active deployment
3. Watch the build logs:
   - Should see: "Building Docker image"
   - Should see: Dockerfile steps
   - Should see: "Build successful"

**Expected Build Steps:**
```
Step 1: FROM eclipse-temurin:17-jre-jammy
Step 2: Install dependencies (wget, curl)
Step 3: Download QuestDB
Step 4: Copy config and entrypoint
Step 5: Build complete
```

---

## Step 7: Verify Deployment

### 7.1 Check Service Logs

1. Go to **"Deployments"** tab
2. Click on latest deployment
3. Click **"View Logs"**

**Look for:**
```
============================================================
QuestDB Container Startup
============================================================
Creating symlink: ~/.questdb -> /data/questdb
Copying configuration file to volume...
✓ Configuration file copied
Starting QuestDB...
```

### 7.2 Test QuestDB

**Via Railway CLI:**
```bash
# Test ping
railway run --service questdb-docker curl http://localhost:80/ping
# Should return: OK
```

**Via Railway Dashboard:**
1. Go to service
2. Click **"Connect"** or **"Shell"**
3. Run: `curl http://localhost:80/ping`
4. Should return: `OK`

### 7.3 Check Volume (If New Volume)

```bash
railway run --service questdb-docker ls -la /data/questdb/
# Should show: conf/, db/ directories
```

### 7.4 Check Data (If Using Existing Volume)

```bash
railway run --service questdb-docker ls -lh /data/questdb/db/
# Should show: ~824MB of data files (if volume shared)
# OR: Empty directory (if new volume)
```

---

## Step 8: Handle Data Migration (If Needed)

### If You Used New Volume (Option A)

Your data (824MB) is still in the old service's volume. Options:

**Option 1: Copy Data from Old Service**
```bash
# From old service, create backup
railway run --service just-shell tar czf /tmp/questdb-backup.tar.gz -C /data/questdb db/

# Download backup (if Railway CLI supports it)
# OR: Use Railway's volume export feature (if available)

# Upload to new service
railway run --service questdb-docker tar xzf /tmp/questdb-backup.tar.gz -C /data/questdb/
```

**Option 2: Keep Old Service as Backup**
- Leave data in old service
- Use new service for new data
- Data is safe in old service

**Option 3: Start Fresh**
- New service starts with empty database
- Old data stays in old service (as backup)
- Resume top1000 process will re-download needed data (slow but safe)

### If You Used Existing Volume (Option B)

Data should already be there! ✅
- Check: `railway run --service questdb-docker ls -lh /data/questdb/db/`
- Should show ~824MB of data
- No migration needed

---

## Step 9: Update Environment Variables (If Needed)

Your Python scripts might need to connect to the new service.

**If running Python in new service:**
- QuestDB connection: `localhost:8812` (same service)

**If running Python in old service:**
- Need to use Railway service networking
- Or use public domain if configured
- Or keep Python in new service too

---

## Quick Checklist

- [ ] Step 1: Git committed and pushed
- [ ] Step 2: New service created in Railway
- [ ] Step 3: Service connected to GitHub repo
- [ ] Step 4: Dockerfile path configured (`questdb/Dockerfile`)
- [ ] Step 5: Volume configured (new or existing)
- [ ] Step 6: Service deployed successfully
- [ ] Step 7: QuestDB starts (check logs)
- [ ] Step 8: QuestDB responds to ping (`curl http://localhost:80/ping`)
- [ ] Step 9: Data accessible (check volume)
- [ ] Step 10: Decide on data migration (if needed)

---

## Troubleshooting

### Build Fails

**Error: "Dockerfile not found"**
- Check Dockerfile path in settings
- Try: `questdb/Dockerfile` or just `Dockerfile` if root is `questdb/`

**Error: "Build context invalid"**
- Set Root Directory to `questdb/` in build settings
- Or move Dockerfile to root (not recommended)

### Service Won't Start

**Check logs:**
```bash
railway logs --service questdb-docker
```

**Common issues:**
- Port 80 already in use (unlikely in new service)
- Volume mount issue
- Entrypoint script permissions

### Volume Issues

**Can't attach existing volume:**
- Railway doesn't support volume sharing (normal)
- Use new volume (Option A)
- Copy data later if needed

**Volume not mounting:**
- Check mount path: `/data/questdb`
- Check volume is created
- Check service settings

---

## Next Steps After Deployment

1. ✅ Verify Docker deployment works
2. ✅ Test QuestDB functionality
3. ✅ Decide on data migration (if needed)
4. ✅ Update CONTEXT.md with new service info
5. ✅ (Optional) Stop old service when confident
6. ✅ (Optional) Resume top1000 process in new service

---

## Summary

**What we're doing:**
1. Create new service (`questdb-docker`)
2. Connect to GitHub (auto-deploys on push)
3. Configure Docker build (`questdb/Dockerfile`)
4. Configure volume (new or existing)
5. Deploy and verify
6. Handle data migration (if needed)

**Your data is SAFE:**
- Old service volume persists
- Can copy data later
- Can keep old service as backup
- Zero risk approach

Ready to start? Begin with Step 1 (commit and push to GitHub)!

