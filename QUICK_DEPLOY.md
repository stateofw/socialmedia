# 🚀 Quick Deploy Guide

## Fastest Way to Deploy (5 minutes)

### Option A: Railway (Recommended - Easiest)

**Step 1:** Sign up at https://railway.app (free $5 credit)

**Step 2:** Click "New Project" → "Deploy from GitHub"

**Step 3:** Select your repo → Railway auto-detects Dockerfile ✅

**Step 4:** Add PostgreSQL and Redis:
- Click "New" → "Database" → "PostgreSQL"
- Click "New" → "Database" → "Redis"

**Step 5:** Set environment variables (click your web service → Variables):
```bash
SECRET_KEY=<generate with: openssl rand -hex 32>
ENV=production
DEBUG=False
OPENROUTER_API_KEY=your-key
PLACID_API_KEY=your-key
PUBLER_API_KEY=your-key
PUBLER_WORKSPACE_ID=your-workspace-id
```

**Step 6:** Railway auto-deploys! 🎉

**Done!** Visit: `https://your-app.up.railway.app/health`

**Cost:** ~$13/month (minus $5 free credit = $8/month)

---

### Option B: Fly.io (FREE!)

**Step 1:** Run the automated script:
```bash
chmod +x deploy-fly.sh
./deploy-fly.sh
```

The script will:
1. Install Fly CLI
2. Login to Fly.io
3. Create app + PostgreSQL
4. Set all environment variables
5. Deploy!

**Done!** Visit: `https://your-app.fly.dev/health`

**Cost:** $0/month (free tier)

---

### Option C: Render (Good Free Tier)

**Step 1:** Sign up at https://render.com

**Step 2:** Create "New Web Service" from GitHub repo

**Step 3:** Settings:
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Step 4:** Add PostgreSQL (free 90 days)

**Step 5:** Add environment variables (same as Railway)

**Step 6:** Deploy!

**Done!** Visit: `https://your-app.onrender.com/health`

**Cost:** Free (with cold starts) or $7/month (always-on)

---

## Post-Deployment Checklist

After deploying to any platform:

### 1. Test Endpoints
```bash
# Health check
curl https://your-app.com/health

# API docs
open https://your-app.com/docs
```

### 2. Run Database Migrations

**Railway:**
```bash
railway run alembic upgrade head
```

**Fly.io:**
```bash
fly ssh console -C "alembic upgrade head"
```

**Render:**
- Go to Shell tab → Run: `alembic upgrade head`

### 3. Create First Admin User

Visit your `/docs` endpoint and use the `/api/v1/auth/register` endpoint:
```json
{
  "email": "admin@yourdomain.com",
  "password": "YourStrongPassword123",
  "full_name": "Admin User"
}
```

### 4. Test Client Portal

1. Create a client via API
2. Set client password
3. Login to client portal: `/api/v1/client/dashboard`

### 5. Set Up Monitoring (Free)

**UptimeRobot:** https://uptimerobot.com
- Add your `/health` endpoint
- Get email alerts if app goes down
- 50 monitors free

---

## Environment Variables Reference

### Required (Minimum to run)
```bash
SECRET_KEY=xxx                  # openssl rand -hex 32
DATABASE_URL=postgresql://...   # Auto-set by host
REDIS_URL=redis://...          # Auto-set by host or Upstash
OPENROUTER_API_KEY=xxx         # Your OpenRouter key
```

### Content Generation (Required)
```bash
PLACID_API_KEY=xxx             # For branded images
PUBLER_API_KEY=xxx             # For social posting
PUBLER_WORKSPACE_ID=xxx        # Your Publer workspace
```

### Optional but Recommended
```bash
AWS_ACCESS_KEY_ID=xxx          # For S3 media storage
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET_NAME=xxx
ALLOWED_ORIGINS=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

---

## Cost Breakdown

### Ultra-Budget ($0-5/month)
- **Host:** Fly.io free tier
- **Database:** Fly.io Postgres (free)
- **Redis:** Upstash free tier (10K/day)
- **Monitoring:** UptimeRobot free
- **Total:** $0-5/month

### Budget ($8-13/month)
- **Host:** Railway ($5/month)
- **Database:** Railway Postgres ($5/month)
- **Redis:** Railway Redis ($3/month)
- **Monitoring:** UptimeRobot free
- **Total:** $13/month ($8 with free credit)

### Production ($25-50/month)
- **Host:** Railway/Render ($7-15/month)
- **Database:** Managed Postgres ($7-15/month)
- **Redis:** Managed Redis ($3-10/month)
- **CDN:** Cloudflare free
- **Monitoring:** Sentry free tier
- **Domain:** $10/year
- **Total:** $25-50/month

---

## Troubleshooting

### App won't start
1. Check logs: `railway logs` or `fly logs`
2. Verify all required env vars are set
3. Check DATABASE_URL format
4. Ensure migrations ran: `alembic upgrade head`

### Database connection error
```bash
# Check if DATABASE_URL is set
railway run printenv DATABASE_URL

# Verify format (should be postgresql+asyncpg://...)
# Railway might set it as postgresql:// - add +asyncpg
```

### Port binding error
- Ensure your app binds to `0.0.0.0:$PORT`
- Check Dockerfile uses correct command
- Verify `PORT` env var is set (Railway/Render auto-set this)

### Static files not loading
- Ensure `/static` and `/media` folders exist
- Check folder permissions
- For Fly.io, ensure persistent volume is mounted

### Cold starts (Render free tier)
- Upgrade to paid tier ($7/month) for always-on
- Or use Railway/Fly.io instead

---

## Scaling

### Railway
```bash
# Scale RAM
railway up --memory 1024

# Scale instances (horizontal)
# Done via dashboard: Settings → Instances
```

### Fly.io
```bash
# Scale RAM
fly scale memory 512

# Scale instances
fly scale count 2

# Auto-scale
fly autoscale set min=1 max=3
```

### Render
- Upgrade plan in dashboard
- Enable auto-scaling (Standard plan+)

---

## Domain Setup

### 1. Get a Domain
- Namecheap: ~$10/year
- Cloudflare: ~$10/year
- Google Domains: ~$12/year

### 2. Point to Your App

**Railway:**
1. Dashboard → Settings → Domains
2. Add custom domain
3. Add CNAME record: `yourdomain.com` → `your-app.up.railway.app`

**Fly.io:**
```bash
fly certs add yourdomain.com
fly certs add www.yourdomain.com
```
Then add DNS records (Fly will show you which)

**Render:**
1. Dashboard → Settings → Custom Domains
2. Add your domain
3. Add CNAME: `yourdomain.com` → `your-app.onrender.com`

### 3. Update Environment Variables
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### 4. SSL/TLS
✅ All platforms provide free SSL automatically!

---

## Next Steps After Deployment

1. ✅ Set up monitoring (UptimeRobot)
2. ✅ Configure backups (database snapshots)
3. ✅ Add custom domain
4. ✅ Set up CI/CD (GitHub Actions)
5. ✅ Configure error tracking (Sentry)
6. ✅ Set up billing alerts
7. ✅ Document your environment variables
8. ✅ Create a staging environment

---

## Support

- **Railway:** https://railway.app/help
- **Fly.io:** https://community.fly.io
- **Render:** https://render.com/docs

**Need help?** Check logs first:
- Railway: `railway logs`
- Fly.io: `fly logs`
- Render: Dashboard → Logs tab

---

**Ready to deploy?** Pick a platform and follow the steps above! 🚀

Recommended for beginners: **Railway** (easiest)
Recommended for budget: **Fly.io** (free)
