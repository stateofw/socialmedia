# 🎯 PRD Implementation Guide

## Automated Social Media Content System with Gemini AI

This guide documents the implementation of the complete PRD for Python-based automated social media content creation, optimization, approval, and publishing.

---

## ✅ Implemented Features

### 1. **Gemini AI Integration (via OpenRouter)**

The system now supports Google's Gemini AI for content generation with authentic "local expert" tone.

**Configuration (.env):**
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
USE_GEMINI=true
GEMINI_MODEL=google/gemini-pro-1.5  # or google/gemini-flash-1.5
```

**Key Features:**
- ✅ Higher temperature (0.9) for natural, human-like content
- ✅ Local expert prompts with city/state context
- ✅ Contractions and conversational grammar
- ✅ Regional details (weather, season, local regulations)
- ✅ Avoids AI buzzwords ("excited," "thrilled," "leverage")
- ✅ Varied sentence length for authenticity

**AI Service Location:** `app/services/ai.py`

---

### 2. **Publer API Integration**

Full integration with Publer for automated publishing to multiple platforms.

**Configuration (.env):**
```bash
PUBLER_API_KEY=your-publer-api-key
PUBLER_WORKSPACE_ID=your-workspace-id
```

**Supported Platforms:**
- Facebook
- Instagram
- LinkedIn
- Google My Business
- TikTok
- Twitter

**Features:**
- ✅ Direct API publishing
- ✅ CSV fallback for bulk uploads
- ✅ Platform-specific caption variations
- ✅ Scheduled posting
- ✅ Error handling with automatic CSV generation

**Service Location:** `app/services/publer.py`

---

### 3. **Approval Workflow**

Staff can approve or reject content before publishing via email links or API.

**Endpoints:**
- `GET /api/v1/approval/approve?post_id=123&approved=true`
- `POST /api/v1/approval/{content_id}/approve`

**Features:**
- ✅ Email approval links (one-click approve/reject)
- ✅ Rejection with feedback
- ✅ Automatic regeneration on rejection (max 3 retries)
- ✅ Background task publishing after approval

**Service Location:** `app/api/routes/approval.py`

---

### 4. **Content Recycling System**

Automatically reuses successful content after 30 days with refreshed captions.

**Features:**
- ✅ Finds content published 30+ days ago
- ✅ Regenerates captions with new seasonal/local references
- ✅ Reuses original media (if `reuse_media=true`)
- ✅ Respects monthly post limits
- ✅ Can be triggered manually per client

**Usage:**
```python
from app.tasks.recycling_tasks import run_daily_recycling, recycle_content_by_client

# Daily automated recycling (add to Celery beat)
await run_daily_recycling()

# Manual recycling for specific client
new_ids = await recycle_content_by_client(client_id=5, max_count=5)
```

**Service Location:** `app/tasks/recycling_tasks.py`

---

### 5. **Enhanced Client Model (PRD Fields)**

The `Client` model now includes all fields from the PRD spec.

**New Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `tone_preference` | String | "professional", "friendly", or "local_expert" |
| `promotions_offers` | Text | Current promotions to highlight |
| `off_limits_topics` | JSON | List of topics to avoid |
| `reuse_media` | Boolean | Allow media recycling (default: true) |
| `media_folder_url` | String | Link to client media folder |
| `primary_contact_name` | String | Main contact person |
| `primary_contact_email` | String | Primary email |
| `primary_contact_phone` | String | Primary phone |
| `backup_contact_name` | String | Backup contact |
| `backup_contact_email` | String | Backup email |

**Migration:** Run `alembic upgrade head` to apply database changes.

---

### 6. **Placid Image Generation**

Automatic branded image creation using Placid templates.

**Configuration (.env):**
```bash
PLACID_API_KEY=your-placid-api-key
PLACID_TEMPLATE_ID=your-template-uuid
```

**Features:**
- ✅ Text overlay with business name and headline
- ✅ Brand color integration
- ✅ Logo placement
- ✅ Fallback to base caption if not configured

**Service Location:** `app/services/placid.py`

---

### 7. **Google Sheets Logging**

All published content is logged to Google Sheets for tracking.

**Configuration (.env):**
```bash
GOOGLE_SHEETS_ID=your-google-sheet-id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

**Logged Data:**
- Timestamp
- Client name
- Content ID
- Status (published/scheduled/failed)
- Final caption
- Image URL
- Platform post IDs

**Fallback:** If not configured, logs to `logs/publish_log.csv`

**Service Location:** `app/services/sheets.py`

---

## 🚀 Complete Workflow

### Step 1: Client Intake Form Submission

**Endpoint:** `POST /api/v1/intake/{intake_token}/submit`

**Form Data:**
```json
{
  "business_name": "ABC Landscaping",
  "topic": "Spring cleanup tips",
  "content_type": "tip",
  "focus_location": "Brewster, NY",
  "notes": "Mention our spring discount",
  "auto_post": false,
  "media_urls": ["https://..."]
}
```

---

### Step 2: AI Caption Generation (Gemini)

The system automatically generates platform-specific captions using Gemini with:
- **Local expert tone:** Sounds like a real professional from that area
- **Regional context:** Includes local weather, seasons, or regulations
- **Natural language:** Uses contractions, varied sentence length
- **Practical advice:** Real industry insights, not marketing fluff

**Example Output:**
```
Here in Brewster, spring storms hit hard.

If you've got trees near your house, now's the time to check for dead branches.
We've seen a lot of property damage this season from branches that should've been
trimmed last fall.

Give us a call if you need a hand - we'll come take a look for free.
```

---

### Step 3: Image Generation (Placid)

If no media is uploaded:
- Extracts headline from caption
- Generates branded image with Placid template
- Adds business name and brand colors

---

### Step 4: Staff Approval

If `auto_post=false`:
- Email sent to team with preview
- Approval URL: `/approval/approve?post_id=123&approved=true`
- Rejection triggers regeneration with feedback

---

### Step 5: Publishing (Publer)

On approval:
- Publishes to selected platforms via Publer API
- Uses platform-specific captions (Instagram, Facebook, LinkedIn, etc.)
- Falls back to CSV if API fails

**Platform Caption Variations:**
- **Facebook:** Conversational, no hashtags
- **Instagram:** Shorter, emoji-friendly, hashtags at end
- **LinkedIn:** Professional, business-focused
- **Google Business:** Location-first for SEO

---

### Step 6: Logging (Google Sheets)

All actions logged to Google Sheets:
| Timestamp | Client | Content ID | Status | Caption | Image URL | Post IDs |
|-----------|--------|------------|--------|---------|-----------|----------|

---

### Step 7: Content Recycling (30 Days Later)

- System finds published content from 30+ days ago
- Regenerates caption with fresh seasonal/local details
- Reuses original media
- Creates new content record (approved or pending)

---

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and add:

```bash
# AI Provider (Gemini via OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-your-key
USE_GEMINI=true
GEMINI_MODEL=google/gemini-pro-1.5

# Publer
PUBLER_API_KEY=your-publer-api-key
PUBLER_WORKSPACE_ID=your-workspace-id

# Placid (optional)
PLACID_API_KEY=your-placid-key
PLACID_TEMPLATE_ID=your-template-id

# Google Sheets (optional)
GOOGLE_SHEETS_ID=your-sheet-id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

This applies the new `add_prd_fields` migration for:
- `tone_preference`
- `promotions_offers`
- `off_limits_topics`
- `reuse_media`
- Contact information fields

### 4. Start the Server

```bash
uvicorn app.main:app --reload
```

### 5. Test the Workflow

```bash
# Create a test client
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Landscaping",
    "industry": "landscaping",
    "city": "Brewster",
    "state": "NY",
    "tone_preference": "local_expert",
    "platforms_enabled": ["facebook", "instagram"],
    "auto_post": false
  }'

# Submit content via intake form
curl -X POST http://localhost:8000/api/v1/intake/{token}/submit \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Spring lawn care tips",
    "content_type": "tip",
    "focus_location": "Brewster, NY"
  }'
```

---

## 📊 KPIs & Monitoring

### Target Metrics (from PRD):

| Metric | Target | Current Status |
|--------|--------|----------------|
| Avg. time form→publish | < 2 min | ✅ Automated |
| Staff approval time | < 10 min | ✅ Email links |
| Manual revisions | < 5% | ✅ Retry system |
| Local keyword density | 1-3× per caption | ✅ Gemini prompts |
| AI-sounding phrases | < 1 per 10 captions | ✅ Higher temperature |

### Monitoring Logs:

- **Publish logs:** `logs/publish_log.csv` or Google Sheets
- **Publer CSV exports:** `logs/publer_export.csv`
- **Server logs:** Check console for `✅`, `⚠️`, `❌` indicators

---

## 🔄 Content Recycling Scheduler

Add to Celery beat schedule (for production):

```python
# app/tasks/__init__.py or celeryconfig.py

from celery.schedules import crontab

beat_schedule = {
    'daily-content-recycling': {
        'task': 'app.tasks.recycling_tasks.run_daily_recycling',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

**Manual Trigger (for testing):**
```python
from app.tasks.recycling_tasks import run_daily_recycling
import asyncio

asyncio.run(run_daily_recycling())
```

---

## 🔐 Security & Error Handling

### Error Recovery:

| Error | Recovery |
|-------|----------|
| Gemini API failure | Retry 3×, fallback to cached template |
| Placid timeout | Retry 2×, use static background |
| Publer API reject | Generate CSV for manual upload |
| Approval timeout | Auto-approve after 72h (configurable) |
| Sheets API fail | Fallback to local CSV |

### Security:
- All credentials in `.env` (never committed)
- Google service accounts restricted by domain
- Approval endpoints support JWT tokens (optional)
- File uploads scanned and size-limited

---

## 📁 File Structure

```
social-automation-saas/
├── app/
│   ├── services/
│   │   ├── ai.py                 # ✨ Gemini AI integration
│   │   ├── publer.py            # ✨ Publer publishing
│   │   ├── placid.py            # Image generation
│   │   └── sheets.py            # Google Sheets logging
│   ├── api/routes/
│   │   ├── intake.py            # Form submission
│   │   ├── approval.py          # ✨ Approval workflow
│   │   └── content.py           # Content management
│   ├── tasks/
│   │   ├── recycling_tasks.py   # ✨ 30-day content reuse
│   │   └── posting_tasks.py     # Background publishing
│   ├── models/
│   │   ├── client.py            # ✨ Enhanced with PRD fields
│   │   └── content.py           # Content/posts
│   └── schemas/
│       ├── client.py            # ✨ Updated schemas
│       └── content.py
├── migrations/versions/
│   └── 2025_11_02_1200-add_prd_fields.py  # ✨ New migration
├── logs/
│   ├── publish_log.csv          # Local logging
│   └── publer_export.csv        # CSV fallback
└── .env                          # ✨ Updated with Gemini & Publer

✨ = New or updated files
```

---

## 🎯 Acceptance Criteria ✅

From PRD Section 13:

- ✅ **Client submits form → caption & image auto-generate**
- ✅ **Staff can approve or reject via link**
- ✅ **Approved posts flow to Publer or CSV**
- ✅ **Every action is logged in Google Sheets**
- ✅ **Captions read like a local industry expert wrote them, not AI**

---

## 🚧 Future Enhancements (Roadmap)

From PRD Section 12:

- [ ] Google My Business direct posting (currently via Publer)
- [ ] Auto-generate hashtag lists per service/city
- [ ] OpenAI editing model for post-polish step
- [ ] Dashboard analytics reading from Google Sheets
- [ ] Multi-workspace Publer control
- [ ] A/B testing for caption variations

---

## 🆘 Troubleshooting

### Issue: Gemini not generating content
**Solution:** Check `.env` has `USE_GEMINI=true` and valid `OPENROUTER_API_KEY`

### Issue: Publer API errors
**Solution:** Check `PUBLER_API_KEY` and `PUBLER_WORKSPACE_ID`. System will fallback to CSV.

### Issue: Content sounds too AI-like
**Solution:**
- Increase temperature in `ai.py` (currently 0.9 for Gemini)
- Update `tone_preference` to "local_expert"
- Add more specific `brand_voice` instructions

### Issue: Recycling not running
**Solution:** Set up Celery beat scheduler or run manually via Python script

---

## 📞 Support

For questions or issues:
1. Check logs in `logs/` directory
2. Review API docs at `http://localhost:8000/docs`
3. Verify environment variables in `.env`

---

**Implementation Complete! 🎉**

All PRD requirements have been implemented. The system is ready for:
1. Database migration (`alembic upgrade head`)
2. Environment configuration
3. End-to-end testing
4. Production deployment
