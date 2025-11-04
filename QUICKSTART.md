# Quick Start Guide

Get your Social Automation SaaS running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- OpenAI API key

## Step 1: Setup Environment

```bash
# Run setup script
./setup.sh

# OR manually:
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=any-random-string-here
```

## Step 2: Start Application

```bash
docker-compose up -d
```

Wait ~30 seconds for services to start.

## Step 3: Test the API

Visit http://localhost:8000/docs to see the interactive API documentation.

### Create a Test Client

```bash
curl -X POST "http://localhost:8000/api/v1/clients" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Landscaping Co",
    "industry": "landscaping",
    "city": "Brewster",
    "state": "NY",
    "service_area": "Putnam County",
    "monthly_post_limit": 8,
    "platforms_enabled": ["facebook", "instagram", "google_business"]
  }'
```

### Submit Content via Intake Form

```bash
curl -X POST "http://localhost:8000/api/v1/intake/form" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Landscaping Co",
    "topic": "We completed a beautiful backyard transformation",
    "content_type": "before_after",
    "focus_location": "Brewster, NY",
    "notes": "Mention eco-friendly practices",
    "auto_post": false
  }'
```

### Check Generated Content

```bash
curl "http://localhost:8000/api/v1/content"
```

You should see:
- AI-generated caption
- Hashtags
- Call-to-action
- Status: `pending_approval`

## Step 4: View Logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f web

# Just Celery worker
docker-compose logs -f celery_worker
```

## Step 5: Stop Application

```bash
docker-compose down
```

## Troubleshooting

### "Connection refused" errors
Wait 30-60 seconds after `docker-compose up` for all services to start.

### "OpenAI API error"
Make sure your `OPENAI_API_KEY` is set correctly in `.env`.

### Database errors
Reset the database:
```bash
docker-compose down -v
docker-compose up -d
```

## Next Steps

1. **Add Social Media Credentials**: Configure Facebook, Instagram, Google Business API credentials in platform_configs table
2. **Set up WordPress**: Add WordPress site credentials to enable blog posting
3. **Configure Storage**: Set up AWS S3 or Cloudflare R2 for media uploads
4. **Build Frontend**: Create admin dashboard with HTMX
5. **Deploy**: Push to Railway, Render, or AWS

## API Endpoints Reference

### Clients
- `POST /api/v1/clients` - Create client
- `GET /api/v1/clients` - List clients
- `GET /api/v1/clients/{id}` - Get client
- `PATCH /api/v1/clients/{id}` - Update client

### Content
- `POST /api/v1/content` - Create content
- `GET /api/v1/content` - List content
- `GET /api/v1/content/{id}` - Get content
- `PATCH /api/v1/content/{id}` - Update content
- `POST /api/v1/content/{id}/approve` - Approve for posting

### Intake (Public)
- `POST /api/v1/intake/form` - Submit content
- `POST /api/v1/intake/upload` - Upload media

## Testing with Postman

Import this collection URL into Postman:
`http://localhost:8000/openapi.json`

## Development

To run locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Start services
uvicorn app.main:app --reload

# In another terminal
celery -A app.tasks worker --loglevel=info

# In another terminal
celery -A app.tasks beat --loglevel=info
```

---

Need help? Check the full [README.md](README.md)
