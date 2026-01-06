# SSH into New Docker Service

Since you already have Railway CLI working, you can SSH into your new service!

## SSH into New Service

### Option 1: SSH into New Service Directly

Exit your current SSH session (if needed):
```bash
exit
```

Then SSH into your new service:
```bash
railway ssh --service <your-new-service-name>
```

**Service name examples:**
- `evm-dex-trades-extractor` (if that's what Railway named it)
- `questdb-docker` (if you named it)
- Or whatever name appears in Railway dashboard

### Option 2: Specify Service with Full Command

```bash
railway ssh --service <service-name>
```

### Option 3: List Services First

To see available services:
```bash
railway status
```

Or check in Railway dashboard for the exact service name.

## Once SSH'd into New Service

### Test QuestDB Ping
```bash
curl http://localhost:80/ping
```
Expected: `OK`

### Check Volume
```bash
ls -la /data/questdb/
```
Should show: `conf/`, `db/` directories

### Check QuestDB Process
```bash
ps aux | grep questdb
```
Should show QuestDB process running

### Check Port 80
```bash
netstat -tlnp | grep :80
```
Should show port 80 listening

## Finding Your Service Name

If you're not sure of the service name:

1. **Railway Dashboard:**
   - Go to your project
   - Look at service names listed
   - Use that exact name

2. **Railway CLI:**
   ```bash
   railway status
   ```
   Shows which service you're currently linked to

3. **List all services:**
   ```bash
   railway list
   ```
   (if this command exists in your CLI version)

## Quick Commands

```bash
# Exit current SSH (if in just-shell)
exit

# SSH into new service
railway ssh --service <new-service-name>

# Test QuestDB
curl http://localhost:80/ping

# Check volume
ls -la /data/questdb/

# Exit when done
exit
```

## If You Have Multiple Services

Railway CLI might default to one service. Use `--service` flag to specify which one:

```bash
railway ssh --service just-shell          # Old service
railway ssh --service evm-dex-trades-extractor  # New service (example name)
```

## Summary

Since you already have Railway CLI working:
1. ✅ Exit current SSH (if needed): `exit`
2. ✅ SSH into new service: `railway ssh --service <new-service-name>`
3. ✅ Test: `curl http://localhost:80/ping`
4. ✅ Should return: `OK`

The service name should be visible in your Railway dashboard - use that exact name!



