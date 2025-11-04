# Client Portal API - New Features Guide

## ✅ New Features Implemented

Your client portal now has powerful new features allowing clients to manage their content independently:

### 📤 Upload Media Anytime
### ✍️ Submit New Content Anytime  
### 📅 View Scheduled Posts
### ⏰ Reschedule Posts

---

## 📤 Upload Media Anytime

**Endpoint:** `POST /api/v1/client/media/upload`

Clients can upload images and videos anytime for future posts.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/client/media/upload" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "files=@video.mp4"
```

**Response:**
```json
{
  "message": "Successfully uploaded 3 file(s)",
  "media_urls": [
    "/media/clients/1/20251104_143022_a1b2c3d4.jpg",
    "/media/clients/1/20251104_143023_e5f6g7h8.jpg",
    "/media/clients/1/20251104_143024_i9j0k1l2.mp4"
  ],
  "count": 3
}
```

**Features:**
- ✅ Supports: JPG, PNG, GIF, WEBP, MP4, MOV, AVI
- ✅ Max 10MB per file
- ✅ Multiple files at once
- ✅ Client-specific storage
- ✅ Returns URLs for content submission

---

## ✍️ Submit New Content

**Endpoint:** `POST /api/v1/client/content/submit`

Clients can submit new content anytime from their portal.

**Request (with images only):**
```bash
curl -X POST "http://localhost:8000/api/v1/client/content/submit" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "media_urls": ["/media/clients/1/photo.jpg"]
  }'
```

**Request (with topic):**
```bash
curl -X POST "http://localhost:8000/api/v1/client/content/submit" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "New landscaping project showcase",
    "content_type": "project_showcase",
    "notes": "Downtown renovation project",
    "media_urls": ["/media/clients/1/before.jpg", "/media/clients/1/after.jpg"]
  }'
```

**Response:**
```json
{
  "message": "Content submitted successfully! We'll generate your post shortly.",
  "content_id": 456,
  "status": "processing"
}
```

**How It Works:**
1. Client uploads media (optional but recommended)
2. Client submits content with media URLs
3. **If no topic:** AI analyzes images and generates topic automatically
4. AI generates captions, hashtags, platform variations
5. Content set to **PENDING_APPROVAL**
6. You review and approve
7. Post gets scheduled and published

---

## 📅 View Scheduled Posts

**Endpoint:** `GET /api/v1/client/scheduled-posts`

Clients can see all their upcoming scheduled posts.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/client/scheduled-posts" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

**Response:**
```json
{
  "total_scheduled": 4,
  "posts": [
    {
      "id": 123,
      "topic": "Before & After: Lawn Transformation",
      "caption": "Check out this amazing lawn transformation...",
      "status": "SCHEDULED",
      "scheduled_at": "2025-11-15T10:00:00",
      "platforms": ["facebook", "instagram", "google_business"],
      "media_urls": ["/media/clients/1/before.jpg", "/media/clients/1/after.jpg"],
      "can_reschedule": true
    },
    {
      "id": 124,
      "topic": "Customer Testimonial",
      "caption": "We're thrilled to share feedback...",
      "status": "APPROVED",
      "scheduled_at": "2025-11-16T14:00:00",
      "platforms": ["facebook", "instagram"],
      "media_urls": ["/media/clients/1/testimonial.jpg"],
      "can_reschedule": false
    }
  ],
  "monthly_posts_used": 5,
  "monthly_limit": 8
}
```

**Post Statuses:**
- **APPROVED**: Approved by you, not yet in publishing queue
- **SCHEDULED**: In Publer queue, will publish at `scheduled_at`
- **can_reschedule**: `true` only for SCHEDULED posts

---

## ⏰ Reschedule Posts

**Endpoint:** `PATCH /api/v1/client/content/{content_id}/reschedule`

Clients can change the schedule of SCHEDULED posts.

**Request:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/client/content/123/reschedule" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "new_scheduled_time": "2025-11-20T15:00:00"
  }'
```

**Response:**
```json
{
  "message": "Post rescheduled successfully",
  "content_id": 123,
  "old_time": "2025-11-15T10:00:00",
  "new_time": "2025-11-20T15:00:00"
}
```

**Requirements:**
- ✅ Post must be SCHEDULED (in Publer queue)
- ✅ New time must be in the future
- ✅ Client can only reschedule their own posts

**Note:** Posts in APPROVED status cannot be rescheduled by clients (you must schedule them first).

---

## 📊 Get Statistics

**Endpoint:** `GET /api/v1/client/stats`

Clients can see their usage stats.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/client/stats" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

**Response:**
```json
{
  "total_posts": 15,
  "posts_this_month": 5,
  "posts_remaining": 3,
  "monthly_limit": 8,
  "by_status": {
    "DRAFT": 2,
    "PENDING_APPROVAL": 1,
    "SCHEDULED": 4,
    "PUBLISHED": 8
  },
  "platforms": ["facebook", "instagram", "google_business"],
  "publer_accounts_connected": 3
}
```

---

## 🎯 Complete Client Workflow Example

### Workflow: Upload & Submit Content

```bash
# 1. Login
curl -X POST "http://localhost:8000/api/v1/client/login" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Joes Landscaping",
    "password": "SecurePassword123"
  }'

# Response: { "access_token": "eyJ...", "token_type": "bearer" }
# Save the access_token for subsequent requests

# 2. Upload media
curl -X POST "http://localhost:8000/api/v1/client/media/upload" \
  -H "Authorization: Bearer eyJ..." \
  -F "files=@lawn_before.jpg" \
  -F "files=@lawn_after.jpg"

# Response: { "media_urls": ["/media/clients/1/...jpg", "/media/clients/1/...jpg"] }

# 3. Submit content (AI will generate captions)
curl -X POST "http://localhost:8000/api/v1/client/content/submit" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "media_urls": ["/media/clients/1/lawn_before.jpg", "/media/clients/1/lawn_after.jpg"],
    "notes": "This was a 2-week project in downtown Brewster"
  }'

# Response: { "content_id": 789, "status": "processing" }

# 4. Check scheduled posts
curl -X GET "http://localhost:8000/api/v1/client/scheduled-posts" \
  -H "Authorization: Bearer eyJ..."

# Response: List of scheduled posts with dates

# 5. Reschedule if needed
curl -X PATCH "http://localhost:8000/api/v1/client/content/789/reschedule" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "new_scheduled_time": "2025-11-25T12:00:00"
  }'

# Response: { "message": "Post rescheduled successfully" }
```

---

## 🔒 Security Features

✅ **Authentication Required**
- All endpoints require valid JWT token
- Token obtained via `/client/login`

✅ **Authorization Checks**
- Clients can only access their own data
- Cannot view/modify other clients' content

✅ **File Upload Security**
- Validates file types: images and videos only
- Max 10MB per file
- Client-specific storage directories
- Automatic cleanup on failure

✅ **Post Management Security**
- Can only reschedule own posts
- Can only reschedule SCHEDULED posts
- Cannot modify PUBLISHED posts

---

## 📋 API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/client/login` | Authenticate client | No |
| GET | `/client/me` | Get client info | Yes |
| GET | `/client/stats` | Get statistics | Yes |
| POST | `/client/media/upload` | Upload media files | Yes |
| POST | `/client/content/submit` | Submit new content | Yes |
| GET | `/client/scheduled-posts` | View scheduled posts | Yes |
| PATCH | `/client/content/{id}/reschedule` | Reschedule post | Yes |

---

## ✅ What's Enabled

**Clients Can Now:**
- ✅ Upload media anytime (not just via intake form)
- ✅ Submit new content whenever they want
- ✅ See how many posts are scheduled
- ✅ View all their scheduled posts with dates
- ✅ Reschedule posts to different times
- ✅ Check remaining monthly posts
- ✅ Upload just images (AI generates everything else)

**You Still Control:**
- ✅ All content requires your approval (PENDING_APPROVAL)
- ✅ You decide when to schedule posts
- ✅ Posts only go to correct client accounts (per-client workspaces)
- ✅ Monthly post limits enforced
- ✅ Client can only reschedule AFTER you've scheduled it

---

**Implementation Date:** November 4, 2025  
**Status:** ✅ Production Ready  
**All endpoints tested and working**
