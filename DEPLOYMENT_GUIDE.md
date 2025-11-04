# Deployment Guide: Cheap + High Uptime

## 🏆 Recommended Options (Ranked by Cost)

### Option 1: **Railway** (Easiest + Best Value)
**Cost:** ~$5/month | **Uptime:** 99.9%+ | **Difficulty:** ⭐ Easy

**Why Railway:**
- ✅ Automatic deploys from GitHub
- ✅ Built-in PostgreSQL ($1/month)
- ✅ Built-in Redis (included)
- ✅ Persistent storage for media files
- ✅ Free SSL/TLS
- ✅ Environment variables UI
- ✅ Automatic scaling
- ✅ $5 free credit to start

**Setup:**
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add PostgreSQL
railway add --database postgres

# 5. Add Redis
railway add --database redis

# 6. Set environment variables (via dashboard)
# - Copy all from your .env
# - DATABASE_URL automatically set by Railway
# - REDIS_URL automatically set by Railway

# 7. Deploy
git push railway main
```

**Cost Breakdown:**
- App instance: $5/month (512MB RAM, shared CPU)
- PostgreSQL: $5/month (shared)
- Redis: $3/month (shared)
- **Total: ~$13/month** (Free $5 credit = $8/month effective)

---

### Option 2: **Render** (Great Free Tier)
**Cost:** FREE (with limitations) or $7/month | **Uptime:** 99.9%+ | **Difficulty:** ⭐ Easy

**Why Render:**
- ✅ Generous free tier
- ✅ Auto-deploy from GitHub
- ✅ Free PostgreSQL (90 days, then $7/month)
- ✅ Free SSL/TLS
- ✅ Great documentation

**Free Tier Limitations:**
- ⚠️ Spins down after 15 min inactivity (50 sec cold start)
- ⚠️ 750 hours/month free
- ⚠️ No Redis on free tier

**Setup:**
1. Go to https://render.com
2. Connect GitHub repo
3. Select "Web Service"
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add PostgreSQL database (free 90 days)
7. Set environment variables
8. Deploy!

**Cost Breakdown:**
- **Free tier:** $0 (with cold starts)
- **Paid tier:** $7/month (always-on, 512MB RAM)
- PostgreSQL: FREE 90 days, then $7/month
- Redis (external): $10/month at Upstash
- **Total Paid: ~$24/month** or **$7/month without Redis**

---

### Option 3: **Fly.io** (Most Control)
**Cost:** ~$3-5/month | **Uptime:** 99.99% | **Difficulty:** ⭐⭐ Medium

**Why Fly.io:**
- ✅ Best free tier (3 shared VMs, 160GB outbound)
- ✅ Run anywhere (global edge)
- ✅ PostgreSQL included (free tier)
- ✅ Persistent volumes for media

**Free Tier Generous:**
- Up to 3 shared-cpu-1x 256MB VMs
- 3GB persistent volumes
- 160GB outbound data transfer

**Setup:**
```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Launch app (creates fly.toml)
fly launch

# 4. Create PostgreSQL
fly postgres create

# 5. Attach database
fly postgres attach <db-name>

# 6. Create persistent volume for media
fly volumes create media_data --size 1

# 7. Deploy
fly deploy
```

**Cost Breakdown:**
- **Free tier:** $0 (with 256MB RAM limits)
- **Paid:** ~$3-5/month (512MB RAM)
- PostgreSQL: FREE on shared tier
- Redis: Use Upstash (has free tier!)
- **Total: $0-5/month**

---

### Option 4: **Digital Ocean App Platform**
**Cost:** $5/month | **Uptime:** 99.99% | **Difficulty:** ⭐ Easy

**Why Digital Ocean:**
- ✅ Simple pricing
- ✅ Great documentation
- ✅ Easy PostgreSQL integration ($7/month)
- ✅ Redis available ($15/month)

**Setup:**
1. Go to https://cloud.digitalocean.com/apps
2. Create new app from GitHub
3. Select your repo
4. Add PostgreSQL database
5. Add Redis (optional)
6. Set environment variables
7. Deploy

**Cost Breakdown:**
- Basic app: $5/month (512MB RAM)
- PostgreSQL: $7/month (managed)
- Redis: $15/month (managed) or use Upstash
- **Total: $12-27/month**

---

### Option 5: **VPS (Hetzner)** (Cheapest if you DIY)
**Cost:** $4.50/month | **Uptime:** 99.9%+ | **Difficulty:** ⭐⭐⭐⭐ Hard

**Why Hetzner VPS:**
- ✅ Cheapest option ($4.50/month)
- ✅ Full control
- ✅ 2 vCPU, 4GB RAM, 40GB SSD
- ✅ Best performance per dollar

**Requires:**
- ❌ You manage server setup
- ❌ You manage security
- ❌ You manage SSL/TLS (use Caddy)
- ❌ You manage backups
- ❌ You manage monitoring

**Quick Setup:**
```bash
# SSH into server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
git clone https://github.com/yourusername/your-repo.git
cd your-repo

# Create .env file
nano .env

# Run with Docker Compose
docker-compose up -d
```

**Cost:**
- VPS: $4.50/month
- **Total: $4.50/month**

---

## 🎯 My Recommendation

### For You: **Railway** or **Fly.io**

**Use Railway if:**
- ✅ You want zero DevOps work
- ✅ You need Redis for Celery tasks
- ✅ Budget is $10-15/month
- ✅ You want best DX (developer experience)

**Use Fly.io if:**
- ✅ Budget is tight (<$5/month)
- ✅ You can use external Redis (Upstash free tier)
- ✅ You want edge deployment (faster globally)
- ✅ You're comfortable with CLI tools

---

## 📦 Pre-Deployment Checklist

### 1. Database Migration
Your app uses SQLite locally. For production, migrate to PostgreSQL:

```bash
# In .env, change:
DATABASE_URL=sqlite:///./social_automation.db

# To PostgreSQL (Railway/Render provide this):
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 2. Create Production .env Template
```bash
# Create .env.example for deployment
cat > .env.example << 'EOF'
# App
ENV=production
DEBUG=False
SECRET_KEY=your-secret-key-here
API_V1_PREFIX=/api/v1

# Database (provided by hosting)
DATABASE_URL=postgresql://...

# Redis (provided by hosting or Upstash)
REDIS_URL=redis://...

# OpenRouter (your AI provider)
OPENROUTER_API_KEY=your-key
USE_OPENROUTER=True

# Placid (image generation)
PLACID_API_KEY=your-key
PLACID_TEMPLATE_ID=your-template-id

# Publer (social posting)
PUBLER_API_KEY=your-key
PUBLER_WORKSPACE_ID=your-workspace-id

# CORS (add your production domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
FRONTEND_URL=https://yourdomain.com
EOF
```

### 3. Add Health Check Endpoint
Your app already has `/health` - perfect! ✅

### 4. Static Files
You serve static files from `/static` and `/media`. Make sure:
- These folders exist in production
- Media folder is on persistent storage (not ephemeral)

### 5. Database Migrations
```bash
# Before first deploy, run migrations
alembic upgrade head
```

---

## 🚀 Step-by-Step: Railway Deployment (Recommended)

### Step 1: Prepare Repo
```bash
# Make sure Dockerfile is in root (you already have this ✅)
# Make sure requirements.txt is in root (you have this ✅)

# Create .dockerignore
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
*.db
*.sqlite
*.sqlite3
.env
.env.local
.DS_Store
EOF

# Commit everything
git add .
git commit -m "Prepare for Railway deployment"
git push
```

### Step 2: Railway Setup
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Choose "Deploy from GitHub repo"
5. Select your repo
6. Railway auto-detects Dockerfile ✅

### Step 3: Add PostgreSQL
1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway auto-sets `DATABASE_URL` environment variable ✅

### Step 4: Add Redis
1. Click "New" → "Database" → "Redis"
2. Railway auto-sets `REDIS_URL` environment variable ✅

### Step 5: Set Environment Variables
1. Click on your web service
2. Go to "Variables" tab
3. Add all from your .env:
   - `SECRET_KEY`
   - `OPENROUTER_API_KEY`
   - `PLACID_API_KEY`
   - `PUBLER_API_KEY`
   - `PUBLER_WORKSPACE_ID`
   - `ENV=production`
   - `DEBUG=False`
   - etc.

### Step 6: Configure Domain
1. Railway gives you: `your-app.up.railway.app`
2. Or add custom domain: Settings → Domains

### Step 7: Run Migrations
```bash
# Install Railway CLI locally
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run migrations
railway run alembic upgrade head
```

### Step 8: Deploy!
```bash
# Automatic! Push to GitHub = auto-deploy
git push origin main

# Or manual deploy
railway up
```

### Step 9: Monitor
1. Railway dashboard shows logs in real-time
2. Check health: `https://your-app.up.railway.app/health`
3. Check docs: `https://your-app.up.railway.app/docs`

---

## 💰 Cost Comparison Summary

| Platform | Monthly Cost | Uptime | Ease | Best For |
|----------|-------------|--------|------|----------|
| **Fly.io** | $0-5 | 99.99% | ⭐⭐ | Cheapest |
| **Railway** | $8-13 | 99.9% | ⭐ | Best DX |
| **Render Free** | $0 | 99.9% | ⭐ | Testing |
| **Render Paid** | $24 | 99.9% | ⭐ | No Redis needed |
| **Digital Ocean** | $12-27 | 99.99% | ⭐ | Established |
| **Hetzner VPS** | $4.50 | 99.9% | ⭐⭐⭐⭐ | DIY |

---

## 🎁 Free Tier Options

### Ultra-Budget: **$0/month**
- **Host:** Fly.io (3 free VMs)
- **Database:** Fly.io Postgres (free shared tier)
- **Redis:** Upstash (10K commands/day free)
- **Domain:** Use Fly.io subdomain
- **SSL:** Free ✅

**Limitations:**
- 256MB RAM (tight but workable)
- Shared CPU
- Limited Redis (10K/day)

---

## 🔒 Production Security Checklist

- [ ] Set `ENV=production` and `DEBUG=False`
- [ ] Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Enable HTTPS only
- [ ] Set `ALLOWED_ORIGINS` to your domain only
- [ ] Store secrets in environment variables (never commit .env)
- [ ] Enable database backups (most hosts do this)
- [ ] Set up monitoring (UptimeRobot is free)
- [ ] Configure CORS properly
- [ ] Rate limit API endpoints (add middleware)

---

## 📊 Monitoring (Free)

### UptimeRobot (Free)
- Monitor your `/health` endpoint
- Get alerts when app goes down
- 50 monitors free
- https://uptimerobot.com

### Sentry (Free tier)
```bash
pip install sentry-sdk

# In app/main.py
import sentry_sdk
sentry_sdk.init(dsn="your-dsn", environment="production")
```

---

## 🚨 Need Help?

**Deployment Issues:**
1. Check logs: `railway logs` or dashboard
2. Verify environment variables
3. Check database connection
4. Ensure migrations ran

**Common Errors:**
- Port binding: Use `0.0.0.0` not `127.0.0.1`
- Database URL: Check format for your provider
- Static files: Ensure paths are correct
- Redis connection: Verify REDIS_URL

---

## 📝 Next Steps After Deployment

1. **Set up monitoring** (UptimeRobot)
2. **Configure backups** (database snapshots)
3. **Add domain** (Namecheap ~$10/year)
4. **Set up CI/CD** (GitHub Actions)
5. **Monitor costs** (set billing alerts)

---

**Ready to deploy?** Start with **Railway** - it's the sweet spot of easy + cheap + reliable! 🚀
