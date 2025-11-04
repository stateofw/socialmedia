# Production Setup Guide

This guide walks you through setting up all third-party integrations needed for production deployment.

## Quick Setup Summary

**Critical Issues Fixed:**
- ✅ Bcrypt password hashing (downgraded to v4.x for passlib compatibility)
- ✅ Authentication system working
- ✅ OpenAI integration installed
- ✅ Redis and Celery installed for background jobs

**What's Working:**
- Core API and authentication
- Admin dashboard and UI
- Client management
- Content submission via intake forms
- Database models and migrations

**What Needs Configuration:**
- OpenAI API key (for AI content generation)
- Social media API credentials (for posting)
- SMTP settings (for email notifications)
- AWS S3 or equivalent (for file storage - optional)

---

## 1. OpenAI Setup (Required for AI Features)

### Get Your API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create new secret key
5. Copy the key (starts with `sk-`)

### Add to .env

```env
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

### Test It

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "topic": "Test content generation",
    "tone": "professional"
  }'
```

**Cost**: ~$0.01-0.03 per post generation with GPT-4

---

## 2. Facebook & Instagram Setup

### Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Business" type
4. Fill in app details:
   - App Name: "Your Company Social Automation"
   - Contact Email: your-email@domain.com

### Add Products

1. Click "Add Product"
2. Add "Facebook Login"
3. Add "Instagram Basic Display"

### Get Credentials

1. Settings → Basic
2. Copy **App ID** and **App Secret**

### Configure OAuth Redirect

1. Facebook Login → Settings
2. Add OAuth Redirect URI:
   ```
   https://yourdomain.com/auth/facebook/callback
   ```

### Add Permissions

Required permissions:
- `pages_manage_posts` - Post to Facebook Pages
- `instagram_basic` - Access Instagram account
- `instagram_content_publish` - Post to Instagram

### Add to .env

```env
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
```

### Testing

1. Go to App Dashboard → Roles → Test Users
2. Create test user
3. Use test credentials to connect account

**Cost**: Free (Facebook/Instagram API)

---

## 3. LinkedIn Setup

### Create LinkedIn App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click "Create App"
3. Fill in details:
   - App Name: "Your Company Social Automation"
   - LinkedIn Page: Your company page
   - Privacy Policy URL: https://yourdomain.com/privacy
   - App Logo: Upload your logo

### Add Products

1. Request access to "Share on LinkedIn" product
2. Request access to "Sign In with LinkedIn" product
3. Wait for approval (usually instant)

### Get Credentials

1. Auth tab → Application credentials
2. Copy **Client ID** and **Client Secret**

### Configure Redirect URI

1. Auth tab → OAuth 2.0 settings
2. Add Authorized Redirect URL:
   ```
   https://yourdomain.com/auth/linkedin/callback
   ```

### Add to .env

```env
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
```

**Cost**: Free (LinkedIn API)

---

## 4. Google Business Profile Setup

### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "Social Automation"
3. Enable APIs:
   - Google Business Profile API
   - Google My Business API

### Create OAuth Credentials

1. APIs & Services → Credentials
2. Create OAuth 2.0 Client ID
3. Application type: "Web application"
4. Authorized redirect URIs:
   ```
   https://yourdomain.com/auth/google/callback
   ```

### Get Credentials

1. Copy **Client ID**
2. Copy **Client Secret**

### Add to .env

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```

**Cost**: Free (Google API)

---

## 5. Email/SMTP Setup (Notifications)

### Option A: Gmail (Development/Small Scale)

1. Enable 2-Factor Authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate app password for "Mail"
4. Copy the 16-character password

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=noreply@yourdomain.com
```

**Limits**: 500 emails/day
**Cost**: Free

### Option B: SendGrid (Recommended for Production)

1. Sign up at [SendGrid](https://sendgrid.com/)
2. Verify your domain (optional but recommended)
3. Settings → API Keys → Create API Key
4. Copy the API key

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
```

**Limits**: 100 emails/day (free), 40k-100k/month (paid)
**Cost**: Free tier available, $15-20/month for production

### Option C: AWS SES (Scalable)

1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Verify your sending domain
3. Create SMTP credentials
4. Copy SMTP username and password

```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
FROM_EMAIL=noreply@yourdomain.com
```

**Limits**: 62,000 emails/month (free tier)
**Cost**: $0.10 per 1,000 emails after free tier

### Test Email

```python
# Test script: test_email.py
from app.services.email import EmailService

email = EmailService()
await email.send_welcome_email("test@example.com", "Test User")
```

---

## 6. File Storage (Optional but Recommended)

### Option A: AWS S3

1. Create S3 bucket: `your-app-media-prod`
2. Set bucket to private
3. Create IAM user with S3 access
4. Generate access keys

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-app-media-prod
```

**Cost**: ~$0.023/GB/month + transfer costs

### Option B: Cloudflare R2 (Cheaper)

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. R2 → Create bucket
3. Manage R2 API Tokens → Create API token
4. Copy credentials

```env
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name
```

**Cost**: 10GB free storage, no egress fees

### Option C: Local Storage (Development Only)

Files will be stored locally in `app/static/uploads/`

```env
# Leave S3 settings empty
AWS_ACCESS_KEY_ID=
S3_BUCKET_NAME=
```

---

## 7. Background Jobs (Celery Setup)

### Start Celery Worker

```bash
# Terminal 1: Start Celery worker
celery -A app.tasks worker --loglevel=info

# Terminal 2: Start Celery beat (scheduler)
celery -A app.tasks beat --loglevel=info
```

### Or Use Supervisor (Production)

```bash
# Install supervisor
sudo apt-get install supervisor

# Create config: /etc/supervisor/conf.d/celery.conf
[program:celery-worker]
command=/path/to/venv/bin/celery -A app.tasks worker --loglevel=info
directory=/path/to/app
user=your-user
autostart=true
autorestart=true

[program:celery-beat]
command=/path/to/venv/bin/celery -A app.tasks beat --loglevel=info
directory=/path/to/app
user=your-user
autostart=true
autorestart=true
```

### Verify Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

---

## 8. Production Environment File

Create `.env.production` with all your production values:

```env
# Application
APP_NAME=Social Automation SaaS
ENV=production
DEBUG=False
SECRET_KEY=your-super-secure-secret-key-min-32-chars
API_V1_PREFIX=/api/v1

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4-turbo-preview

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket

# Social Media APIs
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback

META_APP_ID=your-app-id
META_APP_SECRET=your-secret

LINKEDIN_CLIENT_ID=your-id
LINKEDIN_CLIENT_SECRET=your-secret

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-key
FROM_EMAIL=noreply@yourdomain.com

# Frontend
FRONTEND_URL=https://app.yourdomain.com
```

---

## 9. Testing Checklist

### Before Going Live

```bash
# 1. Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass","full_name":"Test"}'

# 2. Test login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=testpass"

# 3. Create a client (use token from login)
curl -X POST "http://localhost:8000/api/v1/clients" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Client",
    "email": "client@test.com",
    "industry": "Technology"
  }'

# 4. Test AI generation (if OpenAI key configured)
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "topic": "AI in business",
    "tone": "professional"
  }'

# 5. Test health endpoint
curl http://localhost:8000/health
```

### Manual UI Testing

1. Open http://localhost:8000
2. Navigate to admin login: http://localhost:8000/admin/login
3. Log in with test credentials
4. Create a test client
5. Get intake form URL
6. Submit test content via intake form
7. Approve content in dashboard

---

## 10. Security Hardening

### Before Production

- [ ] Change SECRET_KEY to cryptographically secure value:
  ```bash
  openssl rand -hex 32
  ```

- [ ] Set DEBUG=False in production

- [ ] Use HTTPS (automatic on Railway/Render)

- [ ] Configure CORS for your specific domains only

- [ ] Set up rate limiting (built into FastAPI)

- [ ] Enable database SSL connection

- [ ] Use environment variables (never hardcode secrets)

- [ ] Set up database backups

- [ ] Configure log rotation

- [ ] Set up monitoring and alerts

---

## 11. Cost Summary

### Minimum Production Setup

| Service | Provider | Cost/Month |
|---------|----------|------------|
| Hosting | Railway/Render | $20-30 |
| Database | Included | $0 |
| Redis | Included | $0 |
| OpenAI API | Usage-based | $10-50 |
| Email (SendGrid) | Free tier | $0-15 |
| Domain | Namecheap | $10-15 |
| **Total** | | **$40-110/month** |

### Optional Add-ons

- File Storage (S3/R2): $5-20/month
- Monitoring (Sentry): Free tier available
- Uptime Monitoring: Free (UptimeRobot)
- CDN (Cloudflare): Free tier available

---

## 12. Going Live Checklist

- [ ] All API keys configured and tested
- [ ] OpenAI API working
- [ ] Social media OAuth flows tested
- [ ] Email notifications sending
- [ ] Database migrations applied
- [ ] Celery workers running
- [ ] Redis connected
- [ ] HTTPS enabled
- [ ] CORS configured
- [ ] Admin user created
- [ ] Test client created
- [ ] Intake form tested
- [ ] Content generation tested
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Domain configured
- [ ] DNS pointed to hosting

---

## Need Help?

- Check logs first: `docker logs <container>` or platform dashboard
- Test API endpoints at `/docs` (Swagger UI)
- Verify environment variables are loaded
- Check database connections
- Ensure Redis is running
- Review Celery worker logs

**You're ready for production!** 🚀
