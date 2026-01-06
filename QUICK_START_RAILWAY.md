# Quick Start: Create New Railway Service

## ✅ Step 1: COMPLETED
- ✅ Docker code committed and pushed to GitHub
- ✅ Repository: `evowilliamson/evm-dex-trades-extractor`
- ✅ Branch: `main`

---

## Step 2: Create New SERVICE (NOT New Project!)

### ⚠️ IMPORTANT: Service vs Project
- **Service** = New container/service within your EXISTING project ✅ (What we want)
- **Project** = Completely new/separate project ❌ (NOT what we want)

### 2.1 Go to Railway Dashboard
1. Open https://railway.app
2. Log in
3. **VERY IMPORTANT: Select your EXISTING project** (the one with `just-shell` service)
   - Make sure you're INSIDE the project (you should see `just-shell` service listed)
   - Do NOT click "New Project" at the top level!

### 2.2 Create New Service from GitHub
**While INSIDE your existing project:**

1. Click **"+ New"** button (should be within the project, not at top level)
2. You should see options like:
   - **"GitHub Repo"** or **"Deploy from GitHub repo"** ✅ Choose this
   - "Empty Service" ✅ This also works
   - **"New Project"** ❌ Do NOT choose this!
3. If you selected "GitHub Repo":
   - Railway will show your repositories
   - **Select:** `evowilliamson/evm-dex-trades-extractor`
   - Click **"Deploy"** or **"Add Service"**
4. This creates a NEW SERVICE in your EXISTING project

### 2.3 Railway Will:
- Create a new service
- Auto-detect code
- Start building (might fail first time - we need to configure Docker)

---

## Step 3: Configure Docker Build

### 3.1 Go to Service Settings
1. Click on your new service (Railway might name it after your repo)
2. Click **"Settings"** tab

### 3.2 Configure Build
1. Go to **"Build"** section (or "Deploy" → "Build")
2. Look for:
   - **"Dockerfile Path"** → Set to: `questdb/Dockerfile`
   - **"Root Directory"** → Try: `questdb/` (or leave empty)
   - **"Build Command"** → Leave empty

**Note:** Railway UI varies. Look for Docker/Dockerfile options.

### 3.3 If Docker Options Not Visible
- Railway might auto-detect Dockerfile
- Check build logs after first deploy
- If build fails, adjust Dockerfile path in settings

---

## Step 4: Configure Volume

### Option A: Create New Volume (Recommended)

1. Go to **"Settings"** → **"Volumes"** (or "Storage")
2. Click **"+ New Volume"** or **"Add Volume"**
3. **Name:** `questdb-data` (or any name)
4. **Mount Path:** `/data/questdb` ⚠️ **Must be exactly this**
5. **Size:** 50GB (or smaller, can expand later)
6. Click **"Add"** or **"Create"**

### Option B: Try Existing Volume (Advanced)

**Railway typically doesn't allow this**, but check:
1. In **"Volumes"** section
2. Look for **"Attach Existing Volume"** (rare)
3. If available, select volume from `just-shell` service
4. **Mount Path:** `/data/questdb`

**If Option B not available:** Use Option A (create new volume)

---

## Step 5: Configure Networking

1. Go to **"Settings"** → **"Networking"**
2. Railway should auto-detect port 80
3. **Port:** 80 (HTTP)
4. **Public Domain (optional):**
   - Click **"Generate Domain"**
   - This allows web console access
   - Not required for operation

---

## Step 6: Deploy

### Option A: Automatic (Already Triggered)
- Railway should start building automatically after creating service
- Check **"Deployments"** tab

### Option B: Manual Trigger
1. Go to **"Deployments"** tab
2. Click **"Redeploy"** or **"Deploy"** button

### Monitor Build
1. Go to **"Deployments"** tab
2. Click on active deployment
3. Watch build logs

**Expected:**
```
Step 1/X : FROM eclipse-temurin:17-jre-jammy
Step 2/X : RUN apt-get update...
Step 3/X : RUN wget QuestDB...
...
Successfully built
```

---

## Step 7: Verify Deployment

### Check Logs
1. **"Deployments"** → Click deployment → **"View Logs"**
2. Look for:
   ```
   QuestDB Container Startup
   Creating symlink: ~/.questdb -> /data/questdb
   Starting QuestDB...
   ```

### Test QuestDB
**Via Railway Dashboard:**
1. Go to service
2. Click **"Connect"** or **"Shell"**
3. Run: `curl http://localhost:80/ping`
4. Should return: `OK`

**Via Railway CLI:**
```bash
railway run --service <service-name> curl http://localhost:80/ping
```

### Check Volume
```bash
railway run --service <service-name> ls -la /data/questdb/
# Should show: conf/, db/ directories
```

---

## Important Notes

### Volume Path
⚠️ **Must be:** `/data/questdb`
- This is hardcoded in entrypoint.sh
- Don't change it

### Data Migration
- If you created new volume: Starts empty (safe, can copy data later)
- If you attached existing volume: Data should be there
- Old service data (824MB) is safe in old volume

### Service Name
- Railway might auto-name it
- You can rename: **Settings** → **Name**

---

## Troubleshooting

### Build Fails: "Dockerfile not found"
- Check Dockerfile path: `questdb/Dockerfile`
- Try setting Root Directory to `questdb/`

### Service Won't Start
- Check logs in Deployments tab
- Verify volume is mounted at `/data/questdb`
- Check port 80 is configured

### Volume Not Mounting
- Verify mount path: `/data/questdb` (exact)
- Check volume is created
- Check service settings

---

## Next Steps After Deployment

1. ✅ Verify QuestDB works (ping test)
2. ✅ Check logs (no errors)
3. ✅ Decide on data migration (if needed)
4. ✅ Update CONTEXT.md with new service info
5. ✅ (Optional) Test Python connection
6. ✅ (Optional) Resume top1000 process in new service

---

## Summary

**What we're doing:**
1. ✅ Code pushed to GitHub
2. ⏳ Create new service in Railway
3. ⏳ Connect to GitHub repo
4. ⏳ Configure Docker build (`questdb/Dockerfile`)
5. ⏳ Configure volume (`/data/questdb`)
6. ⏳ Deploy and verify

**Your data is SAFE:**
- Old service still running
- Data (824MB) safe in old volume
- Zero risk approach

**Ready?** Go to Railway dashboard and create the new service!

