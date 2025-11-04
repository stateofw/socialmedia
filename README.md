# Social Automation SaaS

Expert-level automation for local businesses - automated social media + blog content creation with human tone.

## Features

- 🤖 **AI Content Generation** - GPT-4 powered, human-sounding posts
- 📱 **Multi-Platform Publishing** - Facebook, Instagram, Google Business, LinkedIn
- 📝 **Automated Blog Creation** - SEO-optimized WordPress posts
- 📊 **Client Management** - Multi-client support with usage limits
- 🎯 **Location-First SEO** - Optimized for local search
- ⏰ **Scheduled Posting** - Background job processing with Celery
- 📸 **Media Management** - AWS S3 file storage
- ✅ **Approval Workflow** - Auto-post or manual approval options

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **AI**: OpenAI GPT-4
- **Storage**: AWS S3 / Cloudflare R2
- **Deployment**: Docker

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

### 1. Clone & Setup

```bash
cd social-automation-saas
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` and add your API keys:

```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-openai-key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/social_automation
REDIS_URL=redis://localhost:6379/0
```

### 3. Run with Docker

```bash
docker-compose up -d
```

This starts:
- FastAPI app on `http://localhost:8000`
- PostgreSQL database
- Redis
- Celery worker & beat scheduler

### 4. Run Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
# (Coming soon with Alembic)

# Start FastAPI
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info

# In another terminal, start Celery beat
celery -A app.tasks beat --loglevel=info
```

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT token)
- `POST /api/v1/auth/login/json` - Login with JSON body
- `GET /api/v1/auth/me` - Get current user info

### Admin UI (Cookie-based auth)

- `GET /admin/login` - Login page
- `POST /admin/login` - Process login
- `GET /admin/logout` - Logout
- `GET /admin/dashboard` - Dashboard with approval queue
- `GET /admin/clients` - Client list page
- `POST /admin/content/{id}/approve` - Quick approve (HTMX)

### Client Management (Requires JWT)

- `POST /api/v1/clients` - Create new client
- `GET /api/v1/clients` - List all clients
- `GET /api/v1/clients/{id}` - Get client details
- `GET /api/v1/clients/{id}/intake-url` - Get unique intake link
- `PATCH /api/v1/clients/{id}` - Update client
- `DELETE /api/v1/clients/{id}` - Delete client

### Content Management (Requires JWT)

- `POST /api/v1/content` - Create content
- `GET /api/v1/content` - List content (with filters)
- `GET /api/v1/content/{id}` - Get content details
- `PATCH /api/v1/content/{id}` - Update content
- `POST /api/v1/content/{id}/approve` - Approve & schedule

### Intake Form (Public - Token-based)

- `GET /api/v1/intake/{token}` - Get client by intake token
- `POST /api/v1/intake/{token}/submit` - Submit content via intake form
- `POST /api/v1/intake/upload` - Upload media files

## Usage Example

### 1. Register & Login

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@youragency.com",
    "password": "secure_password_123",
    "full_name": "Agency Admin"
  }'

# Login to get JWT token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@youragency.com&password=secure_password_123"

# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

### 2. Create a Client

```bash
curl -X POST "http://localhost:8000/api/v1/clients" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "business_name": "Elite Landscaping",
    "industry": "landscaping",
    "website_url": "https://elitelandscaping.com",
    "city": "Brewster",
    "state": "NY",
    "service_area": "Putnam County",
    "monthly_post_limit": 8,
    "auto_post": false,
    "brand_voice": "Professional, knowledgeable, friendly",
    "platforms_enabled": ["facebook", "instagram", "google_business"]
  }'

# Returns client with unique intake_token
```

### 3. Get Client Intake Link

```bash
curl -X GET "http://localhost:8000/api/v1/clients/1/intake-url" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Returns: {"intake_url": "http://localhost:8000/intake/abc123def456"}
# Share this link with your client!
```

### 4. Client Submits Content (No Auth Required)

```bash
# Client uses their unique intake token
curl -X POST "http://localhost:8000/api/v1/intake/abc123def456/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "We just completed a stunning backyard transformation in Brewster",
    "content_type": "before_after",
    "focus_location": "Brewster, NY",
    "notes": "Include mention of our eco-friendly practices",
    "media_urls": ["https://s3.amazonaws.com/bucket/image.jpg"]
  }'
```

The system will:
1. ✅ Create content record
2. 🤖 Generate AI caption with per-platform variations
3. 📝 Set status to "pending_approval"
4. 📧 Email team for review

### 5. Approve & Publish

**Option A: Via Admin UI**
- Visit http://localhost:8000/admin/dashboard
- Click "Approve" on pending content
- One-click approval with HTMX

**Option B: Via API**
```bash
curl -X POST "http://localhost:8000/api/v1/content/1/approve" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

This triggers:
1. ✅ Content approved
2. 📱 Published to all enabled platforms with platform-optimized captions
3. 📧 Client notified with post URLs
4. 📊 Usage counter updated

## Project Structure

```
social-automation-saas/
├── app/
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   │   ├── clients.py
│   │   │   ├── content.py
│   │   │   ├── intake.py
│   │   │   └── users.py
│   │   └── __init__.py
│   ├── core/                # Core config
│   │   ├── config.py
│   │   └── database.py
│   ├── models/              # SQLAlchemy models
│   │   ├── client.py
│   │   ├── content.py
│   │   ├── platform_config.py
│   │   └── user.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── client.py
│   │   ├── content.py
│   │   └── user.py
│   ├── services/            # Business logic
│   │   ├── ai.py           # OpenAI integration
│   │   ├── social.py       # Social media APIs
│   │   ├── wordpress.py    # WordPress publishing
│   │   └── storage.py      # S3 file storage
│   ├── tasks/               # Celery tasks
│   │   ├── content_tasks.py
│   │   └── posting_tasks.py
│   ├── templates/           # HTML templates (HTMX)
│   └── main.py              # FastAPI app
├── tests/                   # Unit tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Development Roadmap

### Phase 1 - MVP ✅ COMPLETE
- [x] Project structure
- [x] Database models
- [x] API endpoints
- [x] AI content generation
- [x] Background task processing

### Phase 2 - Core Features ✅ COMPLETE
- [x] Social media API integrations (Facebook, Instagram, Google Business, LinkedIn)
- [x] Per-platform caption optimization (AI-powered)
- [x] File upload & storage (S3)
- [x] Authentication & authorization (JWT + cookie sessions)
- [x] Admin dashboard (HTMX + Tailwind CSS)
- [x] Email notifications (all workflow stages)
- [x] Unique client intake links
- [x] Automated monthly reports
- [x] Celery Beat scheduled tasks

### Phase 3 - Polish (Optional)
- [ ] Real-time analytics dashboard (engagement metrics)
- [ ] Client portal (client-facing UI)
- [ ] Content calendar view
- [ ] White-label options
- [ ] Subscription billing (Stripe)
- [ ] OAuth flows for social media accounts
- [ ] Database migrations (Alembic)

## Deployment

### Deploy to Railway

1. Create account at [Railway](https://railway.app)
2. Connect GitHub repo
3. Add environment variables
4. Deploy!

### Deploy to Render

1. Create account at [Render](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Add environment variables
5. Deploy!

## Environment Variables

See `.env.example` for all required environment variables.

**Required:**
- `SECRET_KEY` - App secret key
- `OPENAI_API_KEY` - OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

**Optional (for production):**
- AWS S3 credentials
- Social media API credentials
- Email SMTP settings

## Contributing

This is a commercial SaaS project. Contributions welcome!

## License

Proprietary - All rights reserved

## Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI
# socialmedia
