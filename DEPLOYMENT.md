# Railway Deployment Guide

This guide explains how to deploy the DEX Trades Extractor to Railway.

## Overview

Railway supports two deployment approaches:
1. **Automated Deployment (Recommended)**: Uses Dockerfile for consistent builds
2. **Manual SSH**: Full control but requires manual setup each time

We recommend **automated deployment** for reliability and ease of updates.

## Prerequisites

- Railway Pro account ($20/month plan)
- GitHub repository (or Railway can create one)
- API keys for blockchain explorers (Etherscan, etc.)

## Architecture

The deployment consists of two services:
1. **Python Application**: Runs your extraction scripts
2. **QuestDB**: Time-series database for price data (optional but recommended)

## Step 1: Prepare Your Repository

1. Ensure all files are committed to Git:
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push
   ```

2. Verify these files exist:
   - `Dockerfile`
   - `requirements.txt`
   - `railway.json`
   - `.env.example`

## Step 2: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"** (or create new repo)
4. Select your repository

## Step 3: Add QuestDB Service (Recommended)

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"QuestDB"**
3. Railway will automatically provision QuestDB
4. Note the connection details (they'll be in environment variables)

## Step 4: Configure Environment Variables

1. In your Railway project, go to your Python service
2. Click **"Variables"** tab
3. Add the following variables (click **"Raw Editor"** for bulk import):

```bash
# Blockchain API Keys
ETHERSCAN_API_KEY=your_actual_api_key_here

# Wallet addresses (comma-separated)
WALLET_ADDRESSES=0xYourAddress1,0xYourAddress2

# QuestDB connection (if using QuestDB service)
# These are automatically set if you added QuestDB service
# Otherwise, set manually:
QUESTDB_HOST=${QUESTDB_HOST}
QUESTDB_PORT=${QUESTDB_PORT}
QUESTDB_USER=${QUESTDB_USER}
QUESTDB_PASSWORD=${QUESTDB_PASSWORD}
QUESTDB_DATABASE=${QUESTDB_DATABASE}

# Optional API keys
CRYPTOCOMPARE_API_KEY=your_key_here
COINGECKO_API_KEY=your_key_here
```

**Note**: If you added QuestDB as a service, Railway automatically creates service variables. Reference them using `${SERVICE_NAME_VARIABLE}` syntax.

## Step 5: Configure Build Settings

Railway will automatically detect the `Dockerfile` and build your application.

### Custom Start Commands

You can override the default command in Railway:

1. Go to your service → **"Settings"** → **"Deploy"**
2. Set **"Start Command"** based on what you want to run:

**For one-time extraction:**
```bash
python3 fetch_all_trades.py
```

**For continuous top 1000 download:**
```bash
python3 -c "from download_cryptocompare_hourly import download_top_1000_all_data_resume; download_top_1000_all_data_resume(dry_run=False, exclude_coins=['MON'])"
```

**For interactive shell (debugging):**
```bash
python3 -i
```

## Step 6: Deploy

1. Railway will automatically deploy on every push to your main branch
2. Or click **"Deploy"** button to trigger manual deployment
3. Monitor logs in the **"Deployments"** tab

## Step 7: Access QuestDB Web Console (Optional)

1. In Railway, go to your QuestDB service
2. Click **"Settings"** → **"Networking"**
3. Add a **"Public Domain"** (e.g., `questdb.yourproject.railway.app`)
4. Access QuestDB console at: `http://your-domain:9000`

## Storage Considerations

### QuestDB Data Persistence

- Railway provides **persistent volumes** for databases
- QuestDB data is stored in `/var/lib/questdb` (managed by Railway)
- Data persists across deployments

### Application Data

- CSV files and JSON outputs are stored in the container's filesystem
- For persistent storage, consider:
  1. Using Railway volumes (add volume in service settings)
  2. Uploading to cloud storage (S3, etc.)
  3. Committing to Git (for small outputs)

## Monitoring & Logs

1. **View Logs**: Service → **"Deployments"** → Click deployment → **"View Logs"**
2. **Metrics**: Service → **"Metrics"** tab (CPU, Memory, Network)
3. **Alerts**: Set up in Railway dashboard for failures

## Common Commands via Railway CLI

Install Railway CLI:
```bash
npm i -g @railway/cli
```

Login:
```bash
railway login
```

Link project:
```bash
railway link
```

Run commands:
```bash
railway run python3 download_cryptocompare_hourly.py top1000
```

View logs:
```bash
railway logs
```

## Troubleshooting

### Build Fails

1. Check Dockerfile syntax
2. Verify all dependencies in `requirements.txt`
3. Check build logs for specific errors

### Connection to QuestDB Fails

1. Verify QuestDB service is running
2. Check environment variables are set correctly
3. Ensure service variables are referenced properly (use `${VAR_NAME}`)

### Out of Memory

- Railway Pro plan includes 8GB RAM
- For large operations (top 1000 download), monitor memory usage
- Consider running in batches or using Railway's larger plans

### Rate Limiting

- Add API keys to environment variables
- Implement delays in your scripts (already done)
- Consider Railway's cron jobs for scheduled runs

## Cost Optimization

1. **Stop services when not in use**: Railway charges per hour of runtime
2. **Use Railway Cron**: For scheduled tasks instead of always-on services
3. **Optimize storage**: Clean up old data periodically

## Next Steps

1. Set up monitoring/alerting
2. Configure automated backups for QuestDB
3. Set up CI/CD for automated testing before deployment
4. Consider using Railway's cron jobs for scheduled extractions

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: Create an issue in your repository

