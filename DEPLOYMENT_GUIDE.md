# 🚀 Deployment Guide - FastAPI Social Automation SaaS

This guide covers deploying your FastAPI application to **Railway** and **Render** (recommended platforms for Python/FastAPI apps).

**⚠️ Note:** Vercel is optimized for Node.js/Next.js apps. For FastAPI, use Railway, Render, or Fly.io instead.

---

## 🎯 Quick Comparison

| Platform | Free Tier | Ease of Use | Database | Best For |
|----------|-----------|-------------|----------|----------|
| **Railway** | $5/month credit | ⭐⭐⭐⭐⭐ Easiest | Built-in PostgreSQL | Quick deploys |
| **Render** | Yes (limited) | ⭐⭐⭐⭐ Easy | Built-in PostgreSQL | Free tier projects |
| **Fly.io** | Yes (limited) | ⭐⭐⭐ Moderate | Separate PostgreSQL | Advanced control |

---

## 🚂 Option 1: Deploy to Railway (Recommended - Easiest)

Railway is the **fastest and easiest** way to deploy FastAPI apps with PostgreSQL.

### Step 1: Prepare Your Repository

1. Make sure all changes are committed:
```bash
git add .
git commit -m "Ready for deployment"
```

2. Push to GitHub:
```bash
git push origin main
```

### Step 2: Deploy on Railway

1. **Sign up** at [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will auto-detect your Python app!

### Step 3: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database" → "Add PostgreSQL"**
3. Railway automatically creates a database and sets `DATABASE_URL`

### Step 4: Set Environment Variables

In Railway dashboard, go to **Variables** and add:

```bash
ENV=production
DEBUG=False
SECRET_KEY=<generate with: openssl rand -hex 32>
OPENROUTER_API_KEY=sk-or-v1-...
PUBLER_API_KEY=your-publer-key
PLACID_API_KEY=placid-...
ALLOWED_ORIGINS=https://your-app.up.railway.app
FRONTEND_URL=https://your-app.up.railway.app
```

### Step 5: Update Database Connection

Railway provides `DATABASE_URL` automatically. The app will auto-convert it from `postgres://` to `postgresql+asyncpg://`.

### Step 6: Deploy!

Railway automatically deploys on every git push. Your app will be live at:
```
https://your-app-name.up.railway.app
```

### Step 7: Set Up Monthly Counter Reset

**Option A: Railway Cron (if available)**
1. In Railway, check for Cron Jobs feature
2. Schedule: `0 0 1 * *` (midnight on 1st of month)
3. Command: `python reset_monthly_counters.py`

**Option B: External Cron Service**
1. Create endpoint in your app to trigger reset
2. Use [cron-job.org](https://cron-job.org) to call it monthly
3. Secure with API key

---

## 🎨 Option 2: Deploy to Render

Render offers a generous free tier perfect for testing and small projects.

### Step 1: Create Render Account

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account

### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. Configure:
   - **Name**: `social-automation-saas`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Name it (e.g., `social-automation-db`)
3. Select **Free tier** for testing
4. Create database

### Step 4: Set Environment Variables

In Render dashboard, add these environment variables:

```bash
DATABASE_URL=<copy Internal Database URL from PostgreSQL service>
ENV=production
DEBUG=False
SECRET_KEY=<generate with: openssl rand -hex 32>
OPENROUTER_API_KEY=sk-or-v1-...
PUBLER_API_KEY=your-publer-key
PLACID_API_KEY=placid-...
ALLOWED_ORIGINS=https://your-app.onrender.com
FRONTEND_URL=https://your-app.onrender.com
PYTHON_VERSION=3.11
```

### Step 5: Deploy!

Render auto-deploys on every push. Your app will be live at:
```
https://your-app-name.onrender.com
```

**Note:** Free tier may spin down after inactivity (takes ~30 seconds to wake up).

---

## 🛠️ Post-Deployment Checklist

After deploying to either platform:

### 1. Test Core Functionality
- [ ] Landing page loads
- [ ] Admin login works (`/admin/login`)
- [ ] Client login works (`/client/login`)
- [ ] Content creation works
- [ ] Publer integration works
- [ ] Image generation works
- [ ] Engagement metrics display

### 2. Create Admin User
Access your deployment shell and run:
```bash
python -c "from app.core.security import hash_password; print(hash_password('your-password'))"
```

Then manually insert into database or use your existing admin.

### 3. Monitor Logs
- **Railway**: Dashboard → Logs tab
- **Render**: Dashboard → Logs section

### 4. Set Up Domain (Optional)
Both Railway and Render support custom domains:
- Railway: Settings → Domains
- Render: Settings → Custom Domain

---

## 🔒 Security Reminders

Before going live:

1. ✅ Set `DEBUG=False`
2. ✅ Use strong `SECRET_KEY` (run: `openssl rand -hex 32`)
3. ✅ Set `ENV=production`
4. ✅ Use HTTPS (automatic on Railway/Render)
5. ✅ Restrict `ALLOWED_ORIGINS` to your domain only
6. ✅ Keep API keys in environment variables (never commit)
7. ✅ Set up monthly counter reset cron job

---

## 📊 Monitoring

### Railway
- Built-in metrics dashboard
- Real-time logs
- Usage tracking
- Resource monitoring

### Render
- Service metrics
- Log streaming
- Health checks
- Automatic HTTPS

---

## 💰 Cost Estimates

### Railway
- **Hobby**: $5/month credit (enough for testing)
- **Developer**: $20/month (production-ready)
- **Team**: Custom pricing

### Render
- **Free**: 750 hours/month (1 service, spins down)
- **Starter**: $7/month (always-on, better resources)
- **Standard**: $25/month (production-ready)

---

## 🆘 Troubleshooting

### "Application Failed to Start"
- Check logs for detailed error
- Verify `requirements.txt` includes all dependencies
- Ensure `DATABASE_URL` is properly formatted
- Check Python version matches your local

### "ModuleNotFoundError"
- Add missing package to `requirements.txt`
- Commit and push to trigger redeploy

### "Database Connection Failed"
- Verify `DATABASE_URL` environment variable
- Check if database service is running
- For Railway: Ensure database is in same project
- For Render: Copy **Internal** database URL, not external

### "502 Bad Gateway"
- Check if app is listening on correct PORT
- Railway: App auto-detects PORT
- Render: Use `--port $PORT` in start command
- Check logs for startup errors

### "Engagement Metrics Not Showing"
- Section now shows even with 0 posts
- Verify Publer API key is set
- Check that published posts have `platform_post_ids`
- Monitor logs for API errors

---

## 🎯 Recommended Workflow

1. **Local Development**: SQLite database
2. **Staging**: Render Free Tier with PostgreSQL
3. **Production**: Railway Developer Plan with PostgreSQL

---

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Production Checklist](PRODUCTION_DEPLOYMENT_CHECKLIST.md)

---

## ✅ Pre-Deployment Checklist

Use this before deploying:

```bash
# 1. Run tests (if you have them)
pytest

# 2. Check for syntax errors
python -m py_compile app/**/*.py

# 3. Verify environment variables
cat .env | grep -v "^#" | grep -v "^$"

# 4. Generate new secret key
openssl rand -hex 32

# 5. Backup your database
cp social_automation.db social_automation.db.backup

# 6. Commit all changes
git add .
git commit -m "Ready for production deployment"
git push
```

---

## 🎉 You're Ready to Deploy!

Choose your platform:
- **Easiest**: Railway (auto-detects everything)
- **Free Tier**: Render (great for testing)
- **Advanced**: Fly.io (more control)

**Next Steps:**
1. Follow the deployment steps for your chosen platform
2. Set environment variables
3. Test all functionality
4. Set up monthly counter reset
5. Monitor logs and metrics

**Questions?** Check the troubleshooting section or the production checklist!
