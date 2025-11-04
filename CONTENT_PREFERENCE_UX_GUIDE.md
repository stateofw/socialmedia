# Content Generation Preference - UX Guide

## Overview

Clients can now choose how they want to provide content for their social media posts. This creates a clean, explicit UX where clients understand their options upfront.

---

## Three Content Preferences

### 1. **Own Media** (Default)
**Description:** "I'll upload my own photos and videos for posts"

**Best for:**
- Clients with lots of project photos
- Businesses that regularly take photos/videos
- Clients who want full control over imagery

**How it works:**
- Client uploads media through portal
- AI generates captions from their images
- All posts use client-provided content

**Example:** Landscaping company that takes before/after photos of every project

---

### 2. **Auto-Generate**
**Description:** "Automatically create posts with AI-generated text and branded images"

**Best for:**
- Clients without regular photo access
- Busy clients who want hands-off approach
- Service businesses without visual projects

**How it works:**
- System picks industry-specific topics
- AI generates complete captions
- Placid creates branded images
- Posts ready for admin approval

**Example:** HVAC company that doesn't take many photos but needs consistent social presence

---

### 3. **Mixed** (Flexible)
**Description:** "I can upload media or let you auto-generate content as needed"

**Best for:**
- Clients who sometimes have photos, sometimes don't
- Seasonal businesses
- Clients who want flexibility

**How it works:**
- Client can submit with media OR empty
- System intelligently handles both cases
- Ensures consistent posting schedule

**Example:** Restaurant that posts food photos when available, but also wants promotional posts for events

---

## Implementation Flow

### During Client Onboarding

**Admin asks client:**
> "How would you like to provide content for your social media posts?"

**Options presented:**
1. ⬜ **I'll upload my own photos/videos** - I have regular access to project photos
2. ⬜ **Auto-generate content for me** - I don't have regular photos, create posts automatically
3. ⬜ **Flexible approach** - Sometimes I'll upload, sometimes auto-generate

**Set in database:**
```bash
# When creating client
curl -X POST "/api/v1/clients/" \
  -d '{
    "business_name": "Example Business",
    "content_generation_preference": "own_media"  # or auto_generate or mixed
  }'
```

---

### In Client Dashboard

**Dashboard displays current preference:**

```
┌─────────────────────────────────────────────────┐
│  Content Settings                               │
├─────────────────────────────────────────────────┤
│  How we create your posts:                     │
│  • I'll upload my own photos/videos            │
│                                                 │
│  [Change Preference]                            │
└─────────────────────────────────────────────────┘
```

**Change preference modal:**
```
┌─────────────────────────────────────────────────┐
│  Change Content Preference                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ⬜ I'll upload my own photos/videos            │
│     You'll provide images for every post        │
│                                                 │
│  ⬜ Auto-generate content for me                │
│     We'll create posts with AI + branded images │
│                                                 │
│  ⬜ Flexible approach                            │
│     Upload media when you have it, otherwise    │
│     we'll auto-generate                         │
│                                                 │
│  [Cancel]  [Save Changes]                       │
└─────────────────────────────────────────────────┘
```

---

## API Endpoints

### Get Current Preference

```bash
GET /api/v1/client/me
Authorization: Bearer {CLIENT_TOKEN}
```

**Response:**
```json
{
  "id": 1,
  "business_name": "Example Business",
  "content_generation_preference": "own_media",
  "monthly_post_limit": 8,
  "posts_this_month": 3,
  "posts_remaining": 5
}
```

### Update Preference

```bash
PATCH /api/v1/client/content-preference
Authorization: Bearer {CLIENT_TOKEN}
Content-Type: application/json

{
  "content_generation_preference": "auto_generate"
}
```

**Response:**
```json
{
  "message": "Content generation preference updated successfully",
  "preference": "auto_generate",
  "description": "We'll automatically create posts with AI-generated text and branded images"
}
```

**Valid values:**
- `own_media`
- `auto_generate`
- `mixed`

---

## Content Submission Logic

The system respects client preference but is also intelligent about edge cases:

### Preference: "own_media"

**Client submits WITH media:**
✅ Uses client's media + AI captions

**Client submits WITHOUT media:**
⚠️ System checks: Any unused media available?
- **Yes:** Suggests using existing media
- **No:** Falls back to auto-generation (one-time)

### Preference: "auto_generate"

**Client submits anything:**
✅ Always auto-generates regardless of provided media

**Result:**
- AI-generated topic, caption, hashtags
- Placid-generated branded image
- Consistent posting schedule

### Preference: "mixed"

**Client submits WITH media:**
✅ Uses client's media + AI captions

**Client submits WITHOUT media:**
✅ Auto-generates complete post

**Result:**
- Maximum flexibility
- Never blocks posting schedule
- Client controls on per-post basis

---

## UI/UX Examples

### Example 1: Onboarding Flow

```
Step 1: Client Information
┌─────────────────────────────────────────────────┐
│  Business Name: [Joe's Landscaping          ]  │
│  Industry:      [Landscaping         ▼]       │
│  Location:      [Brewster, NY           ]      │
└─────────────────────────────────────────────────┘

Step 2: Content Preferences
┌─────────────────────────────────────────────────┐
│  How would you like to create social posts?    │
│                                                 │
│  ⬜ I'll upload project photos                  │
│     Best if you take regular photos of your    │
│     work and want to showcase projects         │
│                                                 │
│  ⬜ Auto-generate posts for me                  │
│     Best if you don't have regular access to   │
│     photos or prefer a hands-off approach      │
│                                                 │
│  ⬜ Flexible - I'll decide per post             │
│     Upload photos when you have them,          │
│     otherwise we'll create posts for you       │
│                                                 │
│  [← Back]  [Continue →]                        │
└─────────────────────────────────────────────────┘
```

### Example 2: Content Submission Screen

**For "own_media" preference:**
```
┌─────────────────────────────────────────────────┐
│  Create New Post                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  Upload Photos/Videos:                         │
│  ┌─────────┐ ┌─────────┐                      │
│  │  [+]    │ │  [+]    │                      │
│  │ Add     │ │ Add     │                      │
│  └─────────┘ └─────────┘                      │
│                                                 │
│  Optional: Describe your project               │
│  [                                      ]      │
│                                                 │
│  [Submit for AI Caption Generation]            │
└─────────────────────────────────────────────────┘
```

**For "auto_generate" preference:**
```
┌─────────────────────────────────────────────────┐
│  Create New Post                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  ✅ Auto-generation enabled                     │
│                                                 │
│  Our AI will automatically create a post for   │
│  you with:                                      │
│  • Industry-specific topic                     │
│  • Engaging caption with hashtags              │
│  • Branded image with your business name       │
│                                                 │
│  Optional: Suggest a topic                     │
│  [                                      ]      │
│                                                 │
│  [Generate Post]                               │
│                                                 │
│  [Change to manual upload] ────────────────────│
└─────────────────────────────────────────────────┘
```

**For "mixed" preference:**
```
┌─────────────────────────────────────────────────┐
│  Create New Post                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  Choose your approach:                         │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │  Upload Media    │  │  Auto-Generate   │   │
│  │                  │  │                  │   │
│  │  I have photos   │  │  Create for me   │   │
│  │  to share        │  │  automatically   │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Admin Dashboard

### Client List View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Clients                                                            │
├─────────────────────────────────────────────────────────────────────┤
│  Business Name         Industry      Content Preference   Posts    │
│  ─────────────────────────────────────────────────────────────────  │
│  Joe's Landscaping     Landscaping   📸 Own Media        5/8       │
│  ABC HVAC              HVAC          🤖 Auto-Generate    3/8       │
│  Best Burgers          Restaurant    🔀 Mixed            7/8       │
└─────────────────────────────────────────────────────────────────────┘
```

### Client Detail View

```
┌─────────────────────────────────────────────────┐
│  Joe's Landscaping - Settings                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  Content Generation Preference:                │
│  • Own Media (Client provides photos)          │
│                                                 │
│  Placid Template:                              │
│  [abc123-template-uuid]                        │
│                                                 │
│  [Edit Settings]                               │
└─────────────────────────────────────────────────┘
```

---

## Benefits

### For Clients

✅ **Clear expectations** - Know exactly how content will be created
✅ **Flexibility** - Can change preference anytime
✅ **No surprises** - System behaves as expected based on preference
✅ **Less friction** - Auto-generate option removes content creation burden

### For You (Admin)

✅ **Set expectations upfront** - No confusion about content workflow
✅ **Reduce support requests** - Clients understand the system
✅ **Better onboarding** - Clear choice during setup
✅ **Flexible pricing** - Charge more for auto-generation if desired

---

## Migration Strategy

### Existing Clients

All existing clients default to `own_media` preference. To migrate them:

**Option 1: Keep as-is**
- Existing clients continue uploading media
- No changes needed

**Option 2: Update based on behavior**
```sql
-- Clients who rarely upload media → auto_generate
UPDATE clients
SET content_generation_preference = 'auto_generate'
WHERE id IN (
    SELECT client_id
    FROM contents
    GROUP BY client_id
    HAVING COUNT(CASE WHEN media_urls IS NULL THEN 1 END) > 5
);

-- Clients who always upload → keep own_media
-- (already set as default)
```

**Option 3: Ask each client**
- Send email: "Choose your content preference"
- Link to dashboard preference page
- They update it themselves

---

## Testing Checklist

- [ ] Create new client with `own_media` preference
- [ ] Create new client with `auto_generate` preference
- [ ] Create new client with `mixed` preference
- [ ] Update preference via dashboard
- [ ] Submit content with `own_media` + media (should use media)
- [ ] Submit content with `own_media` + no media (should suggest/fallback)
- [ ] Submit content with `auto_generate` + media (should ignore media)
- [ ] Submit content with `auto_generate` + no media (should auto-generate)
- [ ] Submit content with `mixed` + media (should use media)
- [ ] Submit content with `mixed` + no media (should auto-generate)
- [ ] Verify preference shows in dashboard
- [ ] Verify preference editable from dashboard

---

## Future Enhancements

### Per-Post Override
Allow clients to override preference on individual posts:
```
"This month use my photos, but next month auto-generate"
```

### Smart Suggestions
If client with "own_media" hasn't uploaded in 30 days:
```
"💡 Haven't uploaded recently?
   Switch to auto-generate to keep posting?"
```

### Preference Analytics
Track which preference leads to:
- Higher client satisfaction
- More consistent posting
- Better engagement

---

**Implementation Date:** November 4, 2025
**Status:** ✅ Complete and Ready for Use

**API Endpoints:**
- `GET /api/v1/client/me` - View preference
- `PATCH /api/v1/client/content-preference` - Update preference
- `POST /api/v1/clients/` - Set during creation
- `PATCH /api/v1/clients/{id}` - Update via admin

**Database Field:** `clients.content_generation_preference`
**Valid Values:** `own_media`, `auto_generate`, `mixed`
