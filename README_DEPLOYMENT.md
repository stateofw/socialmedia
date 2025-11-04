# 🚀 Social Automation SaaS - Complete Deployment Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Deployment Options](#deployment-options)
3. [Recommended Setup](#recommended-setup)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Domain & SSL](#domain--ssl)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Fastest Deployment: Railway (5 minutes)

```bash
# 1. Run the automated script
chmod +x deploy-railway.sh
./deploy-railway.sh

# 2. Follow the prompts
# 3. Your app is live!
```

### Free Deployment: Fly.io (10 minutes)

```bash
# 1. Run the automated script
chmod +x deploy-fly.sh
./deploy-fly.sh

# 2. Enter your API keys when prompted
# 3. Your app is live for FREE!
```

---

## Deployment Options Comparison

| Platform | Cost/Month | Setup Time | Uptime | Best For |
|----------|-----------|------------|--------|----------|
| **Fly.io** | $0-5 | 10 min | 99.99% | 🏆 Free tier seekers |
| **Railway** | $8-13 | 5 min | 99.9% | 🏆 Best developer experience |
| **Render** | $0-24 | 10 min | 99.9% | Testing & prototypes |
| **Digital Ocean** | $12-27 | 15 min | 99.99% | Established businesses |
| **Hetzner VPS** | $4.50 | 60 min | 99.9% | DIY experts |

---

## Recommended Setup

### For Production: Railway

**Why:**
- ✅ Zero DevOps required
- ✅ Built-in PostgreSQL + Redis
- ✅ Auto-deploy from GitHub
- ✅ Great dashboard & logs
- ✅ Persistent storage for media
- ✅ Only $8/month (after free credit)

**Setup:**
1. Sign up: https://railway.app
2. New Project → Deploy from GitHub
3. Add PostgreSQL + Redis databases
4. Set environment variables
5. Done! Auto-deploys on every push

### For Free/Testing: Fly.io

**Why:**
- ✅ Completely free tier (generous limits)
- ✅ 3 VMs included
- ✅ Free PostgreSQL
- ✅ Global edge deployment
- ✅ Great performance

**Limitations:**
- 256MB RAM per VM (workable)
- Need external Redis (Upstash free tier works)
- More CLI-focused (less GUI)

---

## Environment Variables

### Required (Minimum to run)

```bash
# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database (auto-set by Railway/Fly.io)
DATABASE_URL=postgresql+asyncpg://...

# Redis (auto-set by Railway/Fly.io)
REDIS_URL=redis://...

# AI Provider
OPENROUTER_API_KEY=sk-or-v1-xxx
USE_OPENROUTER=True

# Image Generation
PLACID_API_KEY=xxx
PLACID_TEMPLATE_ID=xxx  # Default template

# Social Posting
PUBLER_API_KEY=xxx
PUBLER_WORKSPACE_ID=xxx
```

### Optional but Recommended

```bash
# Environment
ENV=production
DEBUG=False

# CORS (add your domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
FRONTEND_URL=https://yourdomain.com

# File Storage (recommended for production)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET_NAME=xxx
AWS_REGION=us-east-1

# Email Notifications
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=xxx
FROM_EMAIL=noreply@yourdomain.com

# Social Platforms (if needed)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
META_APP_ID=xxx
META_APP_SECRET=xxx
```

---

## Database Setup

### PostgreSQL Configuration

All hosting platforms provide PostgreSQL:
- **Railway:** Auto-configured ✅
- **Fly.io:** Auto-configured ✅
- **Render:** Auto-configured ✅

Your app uses SQLite locally but **must** use PostgreSQL in production.

### Running Migrations

**First deployment:**
```bash
# Railway
railway run alembic upgrade head

# Fly.io
fly ssh console -C "alembic upgrade head"

# Render
# Go to Shell tab → Run: alembic upgrade head
```

**Subsequent deployments:**
Migrations run automatically on startup! ✅

### Creating Tables

Migrations create all tables automatically:
- `users` - Admin users
- `clients` - Your clients
- `contents` - Social media posts
- `platform_configs` - Platform connections

---

## Domain & SSL

### 1. Get a Domain

**Cheap registrars:**
- Namecheap: ~$10/year
- Cloudflare: ~$10/year
- Porkbun: ~$8/year

### 2. Point Domain to App

**Railway:**
```bash
# In Railway dashboard:
Settings → Domains → Add Custom Domain
# Add CNAME: yourdomain.com → your-app.up.railway.app
```

**Fly.io:**
```bash
fly certs add yourdomain.com
fly certs add www.yourdomain.com
# Follow DNS instructions shown
```

**Render:**
```bash
# In Render dashboard:
Settings → Custom Domains → Add Domain
# Add CNAME: yourdomain.com → your-app.onrender.com
```

### 3. SSL/TLS

**All platforms provide FREE SSL automatically!** ✅

No configuration needed. Your app will be:
- `https://yourdomain.com` ✅
- Auto-redirect from HTTP to HTTPS ✅

### 4. Update Environment Variables

After adding domain:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

---

## Monitoring

### Free Uptime Monitoring: UptimeRobot

**Setup (2 minutes):**
1. Sign up: https://uptimerobot.com
2. Add monitor:
   - Type: HTTP(S)
   - URL: `https://your-app.com/health`
   - Interval: 5 minutes
3. Add alert email

**You'll get instant alerts if your app goes down!**

### Free Error Tracking: Sentry

**Setup:**
```bash
pip install sentry-sdk
```

In `app/main.py`:
```python
import sentry_sdk

if settings.ENV == "production":
    sentry_sdk.init(
        dsn="your-sentry-dsn",
        environment=settings.ENV,
        traces_sample_rate=0.1,
    )
```

Get DSN from: https://sentry.io (free tier: 5K events/month)

### Platform-Specific Monitoring

**Railway:**
- Built-in metrics dashboard
- Real-time logs
- Resource usage graphs

**Fly.io:**
```bash
fly logs              # View logs
fly status            # Check status
fly machine list      # List VMs
fly metrics          # View metrics
```

**Render:**
- Logs tab in dashboard
- Metrics tab shows CPU/RAM
- Events tab shows deployments

---

## Troubleshooting

### App Won't Start

**Check logs first:**
```bash
# Railway
railway logs

# Fly.io
fly logs

# Render
# Dashboard → Logs tab
```

**Common issues:**
1. Missing environment variables
2. Database connection error
3. Port binding error
4. Failed migrations

### Database Connection Error

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Fix:**
1. Check `DATABASE_URL` is set correctly
2. Ensure format is: `postgresql+asyncpg://...` (note the `+asyncpg`)
3. Railway/Fly.io set this automatically - verify it exists

**Test connection:**
```bash
# Railway
railway run python -c "from app.core.database import engine; print('Connected!')"

# Fly.io
fly ssh console -C "python -c 'from app.core.database import engine; print(\"Connected!\")'"
```

### Port Binding Error

**Symptoms:**
```
uvicorn.error: Port 8000 is already in use
```

**Fix:**
Most platforms set `PORT` env var. Update your Dockerfile:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
```

Or in code:
```python
import os
port = int(os.getenv("PORT", 8000))
uvicorn.run("app.main:app", host="0.0.0.0", port=port)
```

### Static Files Not Loading

**Symptoms:**
- 404 errors for `/static/*` or `/media/*`
- Images not showing

**Fix:**
1. Ensure folders exist: `mkdir -p app/static media`
2. Check Dockerfile copies them:
   ```dockerfile
   COPY ./app/static /app/app/static
   COPY ./media /app/media
   ```
3. For persistent media (user uploads), use:
   - Railway: Built-in persistent storage ✅
   - Fly.io: Persistent volumes (see `fly.toml`)
   - Render: Persistent disks (add in dashboard)
   - Or use S3 (recommended)

### Migrations Not Running

**Symptoms:**
```
sqlalchemy.exc.ProgrammingError: relation "clients" does not exist
```

**Fix:**
```bash
# Run migrations manually
railway run alembic upgrade head

# Or SSH into container
fly ssh console
alembic upgrade head
```

### Cold Starts (Render Free Tier)

**Symptoms:**
- First request takes 30-60 seconds
- App "wakes up" slowly

**Cause:**
Render free tier spins down after 15 min of inactivity.

**Solutions:**
1. Upgrade to paid tier ($7/month) ← Best solution
2. Use Railway or Fly.io instead
3. Set up "keep-alive" ping (not recommended)

### Out of Memory

**Symptoms:**
```
Killed
```
or
```
Process ran out of memory
```

**Fix:**
1. **Check your plan:**
   - Free tiers: 256-512MB RAM
   - May not be enough for AI operations

2. **Optimize memory usage:**
   - Use pagination for queries
   - Stream large responses
   - Don't load all images in memory

3. **Upgrade RAM:**
   ```bash
   # Railway
   railway up --memory 1024

   # Fly.io
   fly scale memory 1024

   # Render
   # Upgrade to Standard plan (2GB RAM)
   ```

### Redis Connection Error

**Symptoms:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Fix:**
1. Check `REDIS_URL` is set
2. For Fly.io, use Upstash (free tier):
   - Sign up: https://upstash.com
   - Create Redis database
   - Copy connection URL
   - Set as `REDIS_URL`

3. For Railway/Render, add Redis database in dashboard

### SSL Certificate Error

**Symptoms:**
```
ERR_SSL_VERSION_OR_CIPHER_MISMATCH
```

**Fix:**
1. Wait 24-48 hours after adding domain (DNS propagation)
2. Check DNS is pointing correctly:
   ```bash
   dig yourdomain.com
   ```
3. Verify CNAME record is correct
4. Contact platform support if persists

---

## Cost Optimization

### Ultra-Budget Setup ($0-5/month)

```
Host: Fly.io (free tier)
  - 3 shared VMs
  - 256MB RAM each
  - 3GB storage

Database: Fly.io Postgres (free)
  - Shared CPU
  - 1GB storage

Redis: Upstash (free tier)
  - 10K commands/day
  - 256MB storage

Monitoring: UptimeRobot (free)
Error Tracking: Sentry (free tier)
Domain: Namecheap (~$10/year)
SSL: Free (Fly.io) ✅

Total: $0-5/month + $10/year domain
```

### Budget Setup ($8-15/month)

```
Host: Railway
  - 512MB RAM
  - Shared CPU

Database: Railway Postgres
  - Shared tier
  - 1GB storage

Redis: Railway Redis
  - Shared tier

Everything else: Same as above

Total: $13/month ($8 with free credit)
```

### Production Setup ($25-50/month)

```
Host: Railway/Render
  - 1GB+ RAM
  - Dedicated CPU

Database: Managed Postgres
  - 2GB RAM
  - 10GB storage
  - Automated backups

Redis: Managed Redis
  - 256MB

CDN: Cloudflare (free)
Storage: S3 ($0.023/GB)
Monitoring: Sentry Pro ($26/month for 50K events)
Domain: $10/year

Total: $25-50/month
```

---

## Scaling

### When to Scale?

**Scale UP (vertical) when:**
- High CPU usage (>80% consistently)
- Out of memory errors
- Slow response times

**Scale OUT (horizontal) when:**
- High request volume
- Need redundancy/high availability
- Want zero-downtime deploys

### How to Scale

**Railway:**
```bash
# Increase memory
railway up --memory 2048

# Horizontal scaling
# Done in dashboard: Settings → Replicas
```

**Fly.io:**
```bash
# Increase memory
fly scale memory 1024

# Add more VMs
fly scale count 3

# Auto-scaling
fly autoscale set min=1 max=5
```

**Render:**
- Upgrade plan in dashboard
- Enable auto-scaling (Standard+ plan)

### Database Scaling

**When to scale database:**
- More than 1000 clients
- Slow queries (>1 second)
- High connection count

**How:**
1. Add indexes to frequently queried columns
2. Use connection pooling (already in app ✅)
3. Upgrade to larger database instance
4. Consider read replicas for high traffic

---

## Backup & Disaster Recovery

### Database Backups

**Railway:**
- Automatic daily backups ✅
- Restore from dashboard

**Fly.io:**
```bash
# Create backup
fly postgres db backup my-db

# Restore
fly postgres db restore my-db-backup
```

**Render:**
- Automatic daily backups ✅
- Manual backups available
- Restore from dashboard

### Media Files Backup

**If using local storage:**
```bash
# Backup media folder
fly ssh console -C "tar -czf /tmp/media-backup.tar.gz /app/media"
fly ssh sftp get /tmp/media-backup.tar.gz
```

**Recommended: Use S3**
- Automatic redundancy
- Versioning available
- No manual backups needed

### Disaster Recovery Checklist

- [ ] Database backed up (automated)
- [ ] Media files backed up (S3 or manual)
- [ ] Environment variables documented
- [ ] `.env.example` up to date
- [ ] Git repo has all code
- [ ] Can restore from backups < 1 hour
- [ ] Tested recovery process

---

## CI/CD with GitHub Actions

### Auto-Deploy on Push

**Railway:**
- Already set up! ✅
- Every push to main → auto-deploys

**Fly.io:**
Create `.github/workflows/deploy.yml`:
```yaml
name: Fly Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Render:**
- Already set up! ✅
- Every push to main → auto-deploys

---

## Security Best Practices

### Production Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` (32+ chars)
- [ ] HTTPS only (auto-enabled ✅)
- [ ] `ALLOWED_ORIGINS` set to your domain only
- [ ] Database password is strong
- [ ] API keys stored as secrets (not in code)
- [ ] Regular dependency updates
- [ ] CORS configured properly
- [ ] Rate limiting enabled (add middleware)
- [ ] SQL injection protected (SQLAlchemy ✅)
- [ ] XSS protected (FastAPI ✅)

### Environment Variables Security

**Never commit:**
- `.env` file
- API keys
- Database passwords
- Secret keys

**Always:**
- Use platform secrets/environment variables
- Keep `.env.example` updated (without real values)
- Use strong, unique passwords
- Rotate API keys periodically

---

## Support

### Platform Support

- **Railway:** https://railway.app/help
- **Fly.io:** https://community.fly.io
- **Render:** https://render.com/docs

### Common Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- SQLAlchemy Docs: https://docs.sqlalchemy.org
- Alembic Docs: https://alembic.sqlalchemy.org

---

## Summary

**For Beginners:** Use **Railway**
- Easiest setup
- Great dashboard
- Auto-everything
- $8/month (with free credit)

**For Budget:** Use **Fly.io**
- Completely free
- Good performance
- More technical
- CLI-focused

**For Production:** Use **Railway or Digital Ocean**
- Managed services
- Great support
- Auto-scaling
- $25-50/month

---

**Ready to deploy?** Pick a platform and run the deployment script! 🚀

```bash
# Railway (easiest)
./deploy-railway.sh

# Fly.io (free)
./deploy-fly.sh
```

**Questions?** Check the troubleshooting section or platform docs.

**Good luck!** 🎉
