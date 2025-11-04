# Deployment Guide

## Pre-Deployment Checklist

### Code & Security
- [ ] All sensitive data in environment variables
- [ ] No hardcoded API keys or secrets
- [ ] `.env` file in `.gitignore`
- [ ] CORS properly configured for production domain
- [ ] SQL injection protection verified
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] HTTPS enforced

### Database
- [ ] Database migrations tested
- [ ] Backup strategy in place
- [ ] Connection pooling configured
- [ ] Database credentials secured

### Environment Variables
- [ ] All required env vars documented
- [ ] Production values set in deployment platform
- [ ] SECRET_KEY is cryptographically secure
- [ ] API keys validated and working

### Testing
- [ ] All API endpoints tested
- [ ] Error handling verified
- [ ] Background tasks working
- [ ] File uploads tested
- [ ] AI generation tested with production keys

## Deployment Options

### Option 1: Railway (Recommended - Easiest)

**Pros**: One-click deploy, auto-scaling, built-in PostgreSQL & Redis

1. Create account at [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Connect your repository
4. Add services:
   - Web (FastAPI)
   - PostgreSQL
   - Redis
   - Celery Worker
   - Celery Beat

5. Set environment variables:
   ```
   SECRET_KEY=<generate-secure-key>
   OPENAI_API_KEY=<your-key>
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   ```

6. Deploy!

**Cost**: ~$20-50/month

### Option 2: Render

**Pros**: Simple, good free tier, managed services

1. Create account at [Render](https://render.com)
2. Create Web Service from GitHub
3. Create PostgreSQL database
4. Create Redis instance
5. Create Background Worker (for Celery)
6. Set environment variables
7. Deploy

**Cost**: Free tier available, ~$15-40/month for production

### Option 3: AWS / DigitalOcean / GCP (Advanced)

**Pros**: Full control, scalable, cost-effective at scale

**Services needed**:
- EC2 / Droplet / Compute Engine (app server)
- RDS / Managed Database (PostgreSQL)
- ElastiCache / Redis
- S3 / Spaces / Cloud Storage (file storage)
- Load Balancer (optional)

**Cost**: ~$30-100/month depending on scale

## Environment Variables for Production

```env
# Application
APP_NAME=Social Automation SaaS
ENV=production
DEBUG=False
SECRET_KEY=<GENERATE-SECURE-KEY-HERE>
API_V1_PREFIX=/api/v1

# Database (provided by hosting platform)
DATABASE_URL=postgresql+asyncpg://...

# Redis (provided by hosting platform)
REDIS_URL=redis://...

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=social-automation-prod

# Google APIs
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback

# Meta/Facebook
META_APP_ID=...
META_APP_SECRET=...

# LinkedIn
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Email (for notifications)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>
FROM_EMAIL=noreply@yourdomain.com

# Frontend URL
FRONTEND_URL=https://app.yourdomain.com
```

## Railway Deployment (Step-by-Step)

### 1. Prepare Repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

### 2. Railway Setup

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will detect the `Dockerfile` automatically

### 3. Add Database

1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway will provide `DATABASE_URL` automatically

### 4. Add Redis

1. Click "New" → "Database" → "Add Redis"
2. Railway will provide `REDIS_URL` automatically

### 5. Configure Environment

Click on your web service → "Variables" → Add:

```
SECRET_KEY=<generate-with: openssl rand -hex 32>
OPENAI_API_KEY=sk-...
ENV=production
DEBUG=False
```

### 6. Add Worker Services

Create two additional services from the same repo:

**Celery Worker:**
- Start Command: `celery -A app.tasks worker --loglevel=info`
- Use same environment variables

**Celery Beat:**
- Start Command: `celery -A app.tasks beat --loglevel=info`
- Use same environment variables

### 7. Deploy

Railway will auto-deploy when you push to main branch.

### 8. Get Your URL

Railway provides a URL like: `https://your-app.railway.app`

## Render Deployment (Step-by-Step)

### 1. Create Web Service

1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repository
4. Configuration:
   - Name: `social-automation-api`
   - Environment: `Docker`
   - Branch: `main`
   - Plan: Starter ($7/month)

### 2. Add PostgreSQL

1. New → PostgreSQL
2. Name: `social-automation-db`
3. Plan: Starter ($7/month)
4. Copy the "Internal Database URL"

### 3. Add Redis

1. New → Redis
2. Name: `social-automation-redis`
3. Plan: Starter ($7/month)
4. Copy the connection URL

### 4. Configure Environment Variables

In Web Service → Environment:

```
DATABASE_URL=<postgres-url>
REDIS_URL=<redis-url>
SECRET_KEY=<secure-key>
OPENAI_API_KEY=sk-...
ENV=production
DEBUG=False
```

### 5. Create Background Worker

1. New → Background Worker
2. Same repository
3. Start Command: `celery -A app.tasks worker --loglevel=info`
4. Add same environment variables

### 6. Deploy

Click "Manual Deploy" → "Deploy latest commit"

## Post-Deployment

### 1. Verify Services

```bash
# Check API health
curl https://your-app.railway.app/health

# Check API docs
open https://your-app.railway.app/docs
```

### 2. Create First Admin User

```bash
curl -X POST "https://your-app.railway.app/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "secure-password",
    "full_name": "Admin User"
  }'
```

### 3. Test Intake Form

Create a test client and submit content via the intake form.

### 4. Monitor Logs

**Railway**: Dashboard → Deployments → Logs
**Render**: Dashboard → Service → Logs

### 5. Set Up Monitoring

- [ ] Set up error tracking (Sentry)
- [ ] Set up uptime monitoring (UptimeRobot)
- [ ] Set up log aggregation (if needed)

## Scaling Considerations

### When to scale:

- More than 100 clients
- More than 1000 posts/day
- Response time > 500ms
- Background job queue backing up

### How to scale:

**Vertical** (easier):
- Upgrade instance size
- Increase database resources
- Add more Redis memory

**Horizontal** (better):
- Add more Celery workers
- Load balancer for API instances
- Read replicas for database

## Backup Strategy

### Database Backups

**Railway/Render**: Automatic daily backups included

**Self-hosted**:
```bash
# Daily backup script
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
```

### Application Backups

- [ ] GitHub repository (code)
- [ ] Database snapshots (data)
- [ ] S3 bucket backups (media)
- [ ] Environment variables documented

## Troubleshooting

### Common Issues

**Database connection failed:**
- Check DATABASE_URL is correct
- Verify database is running
- Check firewall rules

**Celery tasks not running:**
- Verify Redis connection
- Check Celery worker is running
- Review task logs

**OpenAI API errors:**
- Verify API key
- Check billing/credits
- Review rate limits

**File upload fails:**
- Check S3 credentials
- Verify bucket permissions
- Test with smaller files

## Monitoring & Alerts

### Set up alerts for:

- [ ] API downtime
- [ ] Database connection errors
- [ ] High error rates
- [ ] Celery queue backup
- [ ] Disk space low
- [ ] High memory usage

### Recommended tools:

- **Uptime**: UptimeRobot (free)
- **Errors**: Sentry (free tier)
- **Logs**: Railway/Render built-in
- **APM**: New Relic (optional)

## Security Checklist

- [ ] HTTPS enabled (auto on Railway/Render)
- [ ] Environment variables secured
- [ ] Database not publicly accessible
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled
- [ ] Dependencies updated

## Cost Estimates

### Railway (Recommended)
- Web service: $10-20/month
- PostgreSQL: $10/month
- Redis: $5/month
- Workers: $5-10/month each
- **Total**: ~$30-50/month

### Render
- Web service: $7/month
- PostgreSQL: $7/month
- Redis: $7/month
- Workers: $7/month each
- **Total**: ~$28-42/month

### AWS (Self-managed)
- EC2 t3.small: $15/month
- RDS PostgreSQL: $15/month
- ElastiCache Redis: $15/month
- S3: $5/month
- **Total**: ~$50/month

---

**Ready to deploy?** Start with Railway for the easiest experience!
