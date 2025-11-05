# Railway Deployment Instructions

Your Railway project is set up! Follow these steps to complete the deployment.

## Step 1: Link to Your App Service

```bash
railway service
```
Select your app service (not PostgreSQL or Redis - those are databases)

## Step 2: Set Environment Variables

Copy and paste these commands one by one in your terminal:

```bash
# Core Configuration
railway variables --set "SECRET_KEY=ce594224f42cf0d48ea78a946a72ef1f763e24086f635ad98efde7968448d2f7"
railway variables --set "ENV=production"
railway variables --set "DEBUG=False"
railway variables --set "API_V1_PREFIX=/api/v1"

# AI Configuration
railway variables --set "USE_OPENROUTER=true"
railway variables --set "OPENROUTER_MODEL=anthropic/claude-3.5-sonnet"
railway variables --set "POLISHER_MODEL=openai/gpt-4-turbo-preview"
railway variables --set "USE_GEMINI=false"
railway variables --set "GEMINI_MODEL=google/gemini-pro-1.5"

# Retry Configuration
railway variables --set "RETRY_DELAY_SECONDS=15"
railway variables --set "MAX_RETRY_ATTEMPTS=3"
```

## Step 3: Set Your API Keys

**REQUIRED** - Replace with your actual keys:

```bash
railway variables --set "OPENROUTER_API_KEY=your-actual-openrouter-key-here"
railway variables --set "PLACID_API_KEY=your-actual-placid-key-here"
railway variables --set "PLACID_TEMPLATE_ID=your-actual-template-id-here"
railway variables --set "PUBLER_API_KEY=your-actual-publer-key-here"
railway variables --set "PUBLER_WORKSPACE_ID=your-actual-workspace-id-here"
```

**OPTIONAL** - If you're using these services:

```bash
railway variables --set "AWS_ACCESS_KEY_ID=your-key"
railway variables --set "AWS_SECRET_ACCESS_KEY=your-secret"
railway variables --set "AWS_REGION=us-east-1"
railway variables --set "S3_BUCKET_NAME=your-bucket"
railway variables --set "GOOGLE_CLIENT_ID=your-id"
railway variables --set "GOOGLE_CLIENT_SECRET=your-secret"
railway variables --set "META_APP_ID=your-id"
railway variables --set "META_APP_SECRET=your-secret"
```

## Step 4: Deploy

```bash
railway up
```

This will build and deploy your application!

## Step 5: Run Database Migrations

After deployment completes:

```bash
railway run alembic upgrade head
```

## Step 6: Get Your App URL

```bash
railway domain
```

Or open your dashboard:
```bash
railway open
```

## Step 7: Test Your Deployment

Visit these URLs (replace with your actual domain):
- Health check: `https://your-app.railway.app/health`
- API docs: `https://your-app.railway.app/docs`
- Admin UI: `https://your-app.railway.app/admin`

## Troubleshooting

**View logs:**
```bash
railway logs
```

**Check status:**
```bash
railway status
```

**Redeploy:**
```bash
railway up --detach
```

## Your Generated SECRET_KEY

Save this somewhere safe:
```
ce594224f42cf0d48ea78a946a72ef1f763e24086f635ad98efde7968448d2f7
```

## Notes

- DATABASE_URL and REDIS_URL are automatically set by Railway (from the postgres and redis services you added)
- Make sure to replace all "your-actual-key-here" placeholders with your real API keys
- The SECRET_KEY above has been pre-generated for you
