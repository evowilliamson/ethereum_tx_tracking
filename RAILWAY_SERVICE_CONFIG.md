# Railway Service Configuration Steps

Based on your Railway settings page, here's what to configure:

## ✅ Already Configured (Good!)

- ✅ **Source Repo**: `evowilliamson/evm-dex-trades-extractor` ✓
- ✅ **Branch**: `main` ✓
- ✅ **Source is connected** ✓

---

## 🔧 Settings to Change

### 1. Build Section - CRITICAL!

**Current:** Builder = "Railpack" (Default) ❌

**Change to:**
1. Click on **"Builder"** dropdown
2. Select **"Dockerfile"** (NOT Railpack, NOT Nixpacks)
3. This tells Railway to use your Dockerfile

**After selecting Dockerfile, you might see:**
- **Dockerfile Path** field → Set to: `questdb/Dockerfile`
- **Build Context** or **Root Directory** → Try: `questdb/` (or leave empty to start)

---

### 2. Build Command (Optional)

**Custom Build Command:**
- **Leave empty** (Docker handles the build automatically)
- OR if Railway requires it, you can leave default

---

### 3. Deploy Section

**Start Command:**
- **Leave empty** (entrypoint.sh handles starting QuestDB)
- OR set to: `/usr/local/bin/entrypoint.sh` if Railway requires a start command

**Restart Policy:**
- ✅ Already set to "On Failure" ✓ (Good!)

---

### 4. Root Directory (IMPORTANT!)

**Add Root Directory:**
1. Click **"Add Root Directory"**
2. Set to: `questdb/`
3. This tells Railway to run builds from the `questdb/` directory

**Why:** Your Dockerfile is in `questdb/Dockerfile`, so Railway needs to know the context.

---

### 5. Volume Configuration (CRITICAL!)

**Volume settings are NOT in the list you showed me.** They're usually in a separate section:

1. Look for **"Volumes"** or **"Storage"** tab in the service settings
2. OR look in the left sidebar for "Volumes"
3. Click **"+ New Volume"** or **"Add Volume"**
4. Configure:
   - **Name**: `questdb-data` (or any name)
   - **Mount Path**: `/data/questdb` ⚠️ **Must be exactly this**
   - **Size**: 50GB (or smaller)
5. Click **"Add"** or **"Create"**

**If you can't find Volumes section:**
- It might be in a different tab (check tabs at top)
- It might be in the service overview page (not settings)
- Railway UI varies, but volumes are essential!

---

### 6. Networking (Optional but Recommended)

**Public Networking:**
- You can click **"Generate Domain"** if you want web console access
- Not required for operation
- Port 80 should auto-detect

---

## Quick Checklist

- [ ] Builder: Change from "Railpack" to **"Dockerfile"**
- [ ] Dockerfile Path: Set to `questdb/Dockerfile` (if field appears)
- [ ] Root Directory: Add `questdb/`
- [ ] Start Command: Leave empty (or set to `/usr/local/bin/entrypoint.sh`)
- [ ] Volume: Create volume at `/data/questdb` (check Volumes section)
- [ ] Networking: Optional - Generate domain if you want web access

---

## Step-by-Step Instructions

### Step 1: Change Builder
1. Scroll to **"Build"** section
2. Find **"Builder"** dropdown
3. Change from "Railpack" to **"Dockerfile"**
4. If "Dockerfile Path" field appears, set to: `questdb/Dockerfile`

### Step 2: Set Root Directory
1. Find **"Add Root Directory"** (in Source or Build section)
2. Click it
3. Enter: `questdb/`
4. Save

### Step 3: Configure Start Command
1. Scroll to **"Deploy"** section
2. Find **"Start Command"** field
3. **Leave empty** (or set to `/usr/local/bin/entrypoint.sh`)
4. Save

### Step 4: Add Volume (IMPORTANT!)
1. Look for **"Volumes"** section (might be in different tab/section)
2. Click **"+ New Volume"**
3. Set:
   - Mount Path: `/data/questdb`
   - Size: 50GB
4. Save

### Step 5: Save All Changes
1. Make sure to click **"Save"** or changes auto-save
2. Railway will trigger a new deployment

---

## After Configuration

1. Railway will automatically trigger a new build
2. Watch the **"Deployments"** tab
3. Check build logs to verify Docker build works
4. Check service logs to verify QuestDB starts

---

## Troubleshooting

### "Dockerfile not found" error
- Verify Root Directory is set to `questdb/`
- Verify Dockerfile Path is `questdb/Dockerfile` (or just `Dockerfile` if root is `questdb/`)

### Can't find Volume settings
- Check different tabs in service settings
- Check service overview page (not settings page)
- Volumes might be project-level (check project settings)

### Builder dropdown doesn't show "Dockerfile"
- Refresh the page
- Railway should detect Dockerfile automatically
- Try selecting "Nixpacks" first, then change to Dockerfile

---

## Summary

**Most Important Changes:**
1. ✅ Builder: **Dockerfile** (not Railpack)
2. ✅ Root Directory: **`questdb/`**
3. ✅ Volume: **`/data/questdb`** (find in Volumes section)
4. ✅ Start Command: **Empty** (or entrypoint.sh)

**Save and deploy!** Railway will build your Docker image and start QuestDB.



