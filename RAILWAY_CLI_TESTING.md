# Testing QuestDB with Railway CLI

## Important Discovery

**Railway does NOT have a web-based shell in the dashboard anymore!**

Instead, you need to use the **Railway CLI** to run commands.

## Option 1: Use Railway CLI `run` Command (Easiest)

### Step 1: Install Railway CLI (if not already installed)

**Quick install:**
```bash
bash <(curl -fsSL cli.new)
```

**Or via npm:**
```bash
npm i -g @railway/cli
```

**Or via Homebrew (macOS):**
```bash
brew install railway
```

### Step 2: Login to Railway

```bash
railway login
```

This opens a browser to authenticate.

### Step 3: Link to Your Project

Navigate to your project directory:
```bash
cd /home/ivo/code/ethereum_tx_tracking
railway link
```

Follow prompts to select:
- Your project
- Your environment (usually "production")

### Step 4: Run Command in Your Service

**To test QuestDB ping:**
```bash
railway run --service <your-service-name> curl http://localhost:80/ping
```

**Replace `<your-service-name>` with:**
- Your service name (e.g., `evm-dex-trades-extractor` or whatever Railway named it)
- Or use service ID if you know it

**To find your service name:**
```bash
railway status
```

### Step 5: Alternative - Just Run Command

If you're already linked to the project, you can specify service:
```bash
railway run curl http://localhost:80/ping
```

But you might need to specify which service if you have multiple services.

## Option 2: Use Railway CLI `ssh` Command (Interactive Shell)

### SSH into Your Service

```bash
railway ssh --service <your-service-name>
```

This gives you an interactive shell where you can run:
```bash
curl http://localhost:80/ping
ls -la /data/questdb/
```

**To exit SSH:**
```bash
exit
```

## Option 3: Test via HTTP Request (External)

If your service has a public domain:

1. **Get your service's public URL:**
   - Go to Railway Dashboard → Your Service → Networking
   - Check if there's a public domain configured
   - Or Railway might auto-generate one

2. **Test from your local machine:**
   ```bash
   curl http://your-service-name.up.railway.app/ping
   ```

But this requires public networking to be enabled.

## Quick Test Commands

### Test QuestDB Ping
```bash
railway run --service <service-name> curl http://localhost:80/ping
```
Expected: `OK`

### Check Volume Directory
```bash
railway run --service <service-name> ls -la /data/questdb/
```
Expected: Shows `conf/` and `db/` directories

### Check QuestDB Process
```bash
railway run --service <service-name> ps aux | grep questdb
```
Expected: Shows QuestDB process running

### Check Port 80
```bash
railway run --service <service-name> netstat -tlnp | grep :80
```
Expected: Shows port 80 listening

## Finding Your Service Name

### Method 1: Railway CLI
```bash
railway status
railway list
```

### Method 2: Railway Dashboard
- Go to your project
- Look at service names listed
- Usually matches your repo name or what you named it

### Method 3: Check Logs
```bash
railway logs
```
Shows which service the logs are from

## Full Example Workflow

```bash
# 1. Install CLI (if needed)
bash <(curl -fsSL cli.new)

# 2. Login
railway login

# 3. Go to project directory
cd /home/ivo/code/ethereum_tx_tracking

# 4. Link project
railway link
# Select your project when prompted

# 5. Test QuestDB (replace service-name)
railway run --service <service-name> curl http://localhost:80/ping

# 6. Check volume
railway run --service <service-name> ls -la /data/questdb/

# 7. (Optional) SSH for interactive access
railway ssh --service <service-name>
```

## Alternative: Just Verify from Logs

Since your logs already show QuestDB started successfully, you can also:

1. **Check service is running:**
   - Railway Dashboard → Your Service → Should show "Running" status

2. **Check logs show QuestDB started:**
   - You already confirmed this! ✅

3. **Monitor logs for any errors:**
   ```bash
   railway logs --service <service-name> --follow
   ```

## Summary

**Railway Dashboard:** ❌ No web shell available

**Railway CLI:** ✅ Use `railway run` or `railway ssh`

**Quick test:**
```bash
railway run --service <your-service-name> curl http://localhost:80/ping
```

**Expected result:** `OK`

## Next Steps

1. Install Railway CLI (if needed)
2. Login: `railway login`
3. Link project: `railway link`
4. Test: `railway run --service <name> curl http://localhost:80/ping`

Since your logs already show QuestDB started successfully, the service is likely working fine! The CLI test is just to confirm it responds to requests.



