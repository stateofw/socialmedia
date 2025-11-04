# 🎯 Client Portal - Complete Guide

## Overview

The **Client Portal** allows your clients to log in, view their content, upload media, approve posts, and manage their preferences through a beautiful, easy-to-use web interface.

---

## ✅ Features Implemented

### 🔐 **Authentication**
- Secure password-based login system
- Session management with HTTP-only cookies
- Separate client authentication (not admin users)

### 📊 **Dashboard**
- Overview statistics (total posts, pending approval, published, remaining)
- Recent content feed
- Upcoming scheduled posts
- Quick action buttons for common tasks

### 📝 **Content Management**
- View all content with filtering by status
- Detailed content view with caption, hashtags, media
- Platform-specific variations display
- **Approve** or **Request Changes** on pending content
- Rejection feedback system

### 📸 **Media Library**
- Upload multiple images/videos at once
- Grid view of all uploaded media
- Support for images (PNG, JPG, GIF, WEBP) and videos (MP4, MOV)
- Copy media URLs for easy sharing
- Organized by client ID for isolation

### 📅 **Calendar**
- View upcoming scheduled posts for next 30 days
- See posting schedule by date
- Platform badges showing where content will publish

### ⚙️ **Settings**
- Update brand voice/tone instructions
- Manage current promotions and offers
- View account information
- See platform integrations

---

## 🚀 Setup Instructions

### 1. Admin Creates Client

First, create a client through the admin interface or API:

```bash
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "business_name": "Test Landscaping Co",
    "industry": "landscaping",
    "city": "Brewster",
    "state": "NY",
    "primary_contact_email": "client@testlandscaping.com",
    "primary_contact_name": "John Doe",
    "platforms_enabled": ["instagram", "facebook"],
    "monthly_post_limit": 8
  }'
```

**Response includes:**
- `id`: Client ID
- `intake_token`: For public content submission
- Other client details

### 2. Set Client Password

After creating the client, set their portal password:

```bash
curl -X POST http://localhost:8000/api/v1/clients/1/set-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "password": "SecurePassword123!"
  }'
```

**Response includes:**
```json
{
  "message": "Password set successfully",
  "client_id": 1,
  "login_url": "http://localhost:8000/api/v1/client/login",
  "email": "client@testlandscaping.com"
}
```

### 3. Client Logs In

Share the login credentials with your client:
- **Login URL:** `http://localhost:8000/api/v1/client/login`
- **Email:** Their `primary_contact_email`
- **Password:** The password you set in step 2

---

## 🌐 Client Portal URLs

All client portal routes are under `/api/v1/client/`:

| Route | Purpose |
|-------|---------|
| `/api/v1/client/login` | Login page (GET) and login handler (POST) |
| `/api/v1/client/logout` | Logout and clear session |
| `/api/v1/client/dashboard` | Main dashboard with stats and overview |
| `/api/v1/client/content` | List all content (with optional `?status=` filter) |
| `/api/v1/client/content/{id}` | View content details |
| `/api/v1/client/content/{id}/approve` | Approve content (POST) |
| `/api/v1/client/content/{id}/reject` | Reject with feedback (POST) |
| `/api/v1/client/media` | Media library and upload page |
| `/api/v1/client/media/upload` | Upload media files (POST) |
| `/api/v1/client/calendar` | Content calendar (next 30 days) |
| `/api/v1/client/settings` | Account settings |
| `/api/v1/client/settings/update` | Update settings (POST) |

---

## 🎨 User Interface

The client portal uses:
- **Tailwind CSS** for beautiful, responsive design
- **Alpine.js** for interactive components
- **HTMX** for smooth page interactions
- **Purple theme** to differentiate from admin (which uses indigo)

### Screenshots (What Clients See):

**Login Page:**
- Clean, centered form
- Purple branding
- Email + password fields

**Dashboard:**
- 4 stat cards: Total Posts, Pending Approval, Published, Posts Remaining
- Upcoming scheduled posts section
- Recent content feed
- Quick action buttons (Upload Media, Review Posts, Settings)

**Content Management:**
- Filterable list by status (All, Pending, Approved, Published)
- Click any post to see full details
- Approve or request changes on pending posts
- Modal for rejection feedback

**Media Library:**
- Drag-and-drop upload area
- Grid display of all uploaded media
- Video thumbnails with play icons
- Copy URL button on hover

---

## 📁 File Structure

### Backend Files Created:

```
app/
├── api/
│   └── routes/
│       └── client_portal.py          # All client portal routes (450+ lines)
├── models/
│   └── client.py                     # Added password_hash, last_login fields
└── templates/
    └── client/
        ├── base.html                  # Base template with client nav
        ├── login.html                 # Login page
        ├── dashboard.html             # Main dashboard
        ├── content.html               # Content list
        ├── content_detail.html        # Single content view
        ├── media.html                 # Media library
        ├── calendar.html              # Calendar view
        └── settings.html              # Settings page

migrations/
└── versions/
    └── 2025_11_02_2000-764054baedb3_add_client_portal_auth.py

media/
└── clients/
    └── {client_id}/                   # Each client gets their own folder
```

### API Additions:

**`app/api/routes/clients.py`:**
- Added `set_client_password` endpoint

**`app/api/__init__.py`:**
- Registered `client_portal` router under `/client` prefix

**`app/main.py`:**
- Mounted `/media` static files directory

---

## 🔒 Security Features

### Session Management:
- HTTP-only cookies prevent XSS attacks
- 7-day session expiration
- Sessions stored in-memory (can be upgraded to Redis)

### Password Security:
- Passwords hashed with bcrypt
- Separate from admin user passwords
- No plain-text storage

### Access Control:
- Clients can only see their own content
- Media folders isolated by client ID
- Admin endpoints require admin authentication

---

## 💡 Usage Workflow

### Complete Client Onboarding:

1. **Admin creates client** → Client record created with intake token
2. **Admin sets password** → Client can now log in to portal
3. **Admin shares credentials** → Email client their login info
4. **Client logs in** → Sees dashboard, content, media
5. **Client uploads media** → Photos/videos for upcoming posts
6. **System generates content** → Using AI + client's media
7. **Client reviews & approves** → Content goes to "approved" status
8. **System publishes** → Content posted to social platforms
9. **Client tracks performance** → Via dashboard stats

---

## 🎯 Content Approval Flow

When content is ready for review, it has status **"polished"**:

1. Client sees **"Pending Approval"** count on dashboard
2. Client clicks **"Review Posts"** quick action
3. Content list shows all polished posts
4. Client clicks a post to view full details:
   - Caption
   - Hashtags
   - Platform-specific versions
   - Media attachments
   - Scheduled time
5. Client has two options:
   - **Approve** → Status becomes "approved", ready to publish
   - **Request Changes** → Opens modal for feedback
6. If rejected:
   - Client types specific feedback
   - Status becomes "rejected"
   - Admin/system can revise and resubmit

---

## 📤 Media Upload

### Supported Formats:
- **Images:** PNG, JPG, JPEG, GIF, WEBP
- **Videos:** MP4, MOV
- **Size:** Up to 50MB per file (configurable)

### Upload Process:
1. Client goes to **Media** page
2. Clicks upload area or drags files
3. Selects multiple files at once
4. Clicks **"Upload Selected Files"**
5. Files saved to `media/clients/{client_id}/`
6. Files accessible at `/media/clients/{client_id}/{filename}`

### Usage:
- Admin can use uploaded media in content generation
- Media URLs can be copied and shared
- All media is organized per-client

---

## 🔧 Customization Options

### Branding:
All client portal pages use **purple theme**. To customize:
- Edit `app/templates/client/base.html`
- Change Tailwind color classes (e.g., `bg-purple-600` → `bg-blue-600`)

### Email Notifications:
To notify clients of pending approvals, add email sending in:
- `app/api/routes/intake.py` after content is polished
- Use `settings.SMTP_*` configuration

### Session Storage:
Current: In-memory dictionary (resets on server restart)
Upgrade to Redis:
```python
# In client_portal.py
# Replace client_sessions dict with Redis
import redis
session_store = redis.Redis(host='localhost', port=6379, db=1)
```

---

## 🧪 Testing the Portal

### Test Login:

1. Create a test client (see Setup step 1)
2. Set password (see Setup step 2)
3. Visit http://localhost:8000/api/v1/client/login
4. Enter email and password
5. Should redirect to dashboard

### Test Media Upload:

1. Log in as client
2. Navigate to **Media** tab
3. Upload a test image
4. Should appear in grid view
5. Check `media/clients/{client_id}/` folder

### Test Content Approval:

1. Create content via admin or API
2. Set status to "polished"
3. Log in as client
4. See "Pending Approval" count
5. Click content, approve or reject
6. Verify status changes in database

---

## 📊 Database Schema Changes

### `clients` table:

**New fields:**
- `password_hash` (String, nullable) - Bcrypt hashed password
- `last_login` (DateTime, nullable) - Tracks portal access

**Migration:** `2025_11_02_2000-764054baedb3_add_client_portal_auth.py`

Run with:
```bash
./venv/bin/alembic upgrade head
```

---

## 🎉 Success Indicators

Your client portal is working when:

✅ Clients can log in with email/password
✅ Dashboard shows accurate stats
✅ Content list displays all client posts
✅ Clients can approve/reject content
✅ Media uploads save to correct folder
✅ Calendar shows scheduled posts
✅ Settings can be updated
✅ Session persists across page loads
✅ Logout clears session and redirects

---

## 🚀 Next Steps / Enhancements

### Potential Additions:

1. **Email Notifications:**
   - Notify client when content is ready for review
   - Send weekly summary of posts

2. **Analytics Integration:**
   - Show post performance (likes, comments, shares)
   - Graph engagement over time

3. **Content Requests:**
   - Allow clients to submit content ideas
   - Direct submission form in portal

4. **Multi-User Support:**
   - Multiple team members per client account
   - Role-based permissions (viewer, approver, admin)

5. **Payment Integration:**
   - Show billing info
   - Upgrade/downgrade plans
   - Payment history

6. **Mobile App:**
   - Native iOS/Android app
   - Push notifications for approvals

---

## 🐛 Troubleshooting

### "Not authenticated" error:
- Check session cookie is set
- Verify `client_session` cookie exists
- Try logging in again

### Media not uploading:
- Check `media/clients/` folder exists and is writable
- Verify file size under limit
- Check file extension is allowed

### Can't log in:
- Verify password was set via `/clients/{id}/set-password`
- Check `primary_contact_email` matches login email
- Ensure client `is_active = true`

### Session expires immediately:
- Check cookie settings in browser
- Verify server time matches client time
- Consider upgrading to Redis for persistent sessions

---

## 📚 Related Documentation

- **Main System:** `SYSTEM_READY.md`
- **Setup Guide:** `SIMPLIFIED_SETUP.md`
- **OpenRouter Config:** `OPENROUTER_UNIFIED_SETUP.md`
- **Features:** `ENHANCEMENTS_COMPLETE.md`
- **Original PRD:** `PRD_IMPLEMENTATION_GUIDE.md`

---

## ✨ Summary

The **Client Portal** gives your clients a professional, self-service interface to:

🎯 Monitor their content pipeline
📸 Upload media for upcoming posts
✅ Approve or request changes to generated content
📅 See their posting schedule
⚙️ Manage preferences and settings

All with a beautiful, mobile-responsive design that matches your brand!

**Status:** ✅ **FULLY IMPLEMENTED AND READY TO USE!**
