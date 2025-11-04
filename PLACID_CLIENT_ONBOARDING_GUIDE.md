# Placid Client Onboarding Guide

## Overview

Each client can have their own **custom Placid template** with their unique branding (logo, colors, fonts). When auto-generating content, the system uses the client's specific template to create branded images.

---

## How It Works

### Template Priority System

When generating images, the system uses this priority:

1. **Client-specific template** (`client.placid_template_id`) - Used if configured
2. **Global fallback template** (`.env` PLACID_TEMPLATE_ID) - Used if client has no template
3. **Skip image generation** - If neither is configured

This allows:
- Quick testing with a default template
- Per-client branding for production clients
- Mix of custom and default templates

---

## Client Onboarding Process

### Option 1: Quick Start (Use Default Template)

**Best for:** Testing, simple clients, or quick onboarding

1. Create ONE master Placid template in your Placid account
2. Add template ID to `.env`:
   ```bash
   PLACID_TEMPLATE_ID=abc123-your-template-uuid
   ```
3. All clients without a custom template will use this default
4. ✅ **Done!** Client can start auto-generating posts immediately

**Pros:**
- Fast onboarding (no template setup needed)
- One template to maintain

**Cons:**
- All clients share same design/layout
- Limited branding customization

---

### Option 2: Custom Branded Template (Recommended)

**Best for:** Premium clients, enterprise accounts, or clients who need full branding

#### Step 1: Create Client Template in Placid

1. Log into your [Placid account](https://placid.app/)
2. Create a new template with the following layers:

**Required Layers:**
- `title` (text) - Main headline
- `business_name` (text) - Business name
- `background_color` (color/hex) - Dynamic color based on industry
- `subtitle` (text, optional) - Description/subtitle

**Optional Layers for Custom Branding:**
- `logo` (image) - Client logo
- `brand_accent` (color) - Client's brand color
- Any custom design elements

**Recommended Template Size:**
- 1200x630px (optimal for Facebook/LinkedIn)
- 1080x1080px (optimal for Instagram)

3. Copy the template UUID from Placid (looks like `abc123-def456-...`)

#### Step 2: Add Template to Client Record

**Via Admin Dashboard (Recommended):**
```python
# When creating/editing a client:
client.placid_template_id = "abc123-def456-ghi789"
```

**Via Database Direct:**
```sql
UPDATE clients
SET placid_template_id = 'abc123-def456-ghi789'
WHERE id = 1;
```

**Via API:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/clients/1" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"placid_template_id": "abc123-def456-ghi789"}'
```

#### Step 3: Test Image Generation

```bash
# Client submits empty content (triggers auto-generation)
curl -X POST "http://localhost:8000/api/v1/client/content/submit" \
  -H "Authorization: Bearer {CLIENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{}'
```

✅ **Result:** Image generated with client's custom template!

---

## Template Design Best Practices

### Industry-Specific Colors

The system automatically applies industry-specific colors to the `background_color` layer:

| Industry | Color | Hex Code |
|----------|-------|----------|
| Landscaping | Green | `#4CAF50` |
| Construction | Orange | `#FF9800` |
| Restaurant | Pink | `#E91E63` |
| Healthcare | Light Blue | `#2196F3` |
| Fitness | Red | `#F44336` |
| Real Estate | Blue | `#3F51B5` |
| Retail | Purple | `#9C27B0` |
| Automotive | Gray | `#607D8B` |
| Beauty | Pink | `#E91E63` |
| Home Services | Deep Orange | `#FF5722` |

**Pro Tip:** Design your template to work with multiple background colors so it adapts to any industry.

### Dynamic Content Handling

The system automatically truncates content to prevent overflow:
- `title`: Maximum 60 characters
- `subtitle`: Maximum 100 characters
- `business_name`: No limit (but keep short for best results)

**Design your template with these limits in mind!**

### Logo Integration

If your template has a `logo` layer:
1. Store client logo URL in `client.logo_url`
2. Update Placid service to pass logo:
   ```python
   # In placid.py generate_social_post_image():
   if client.logo_url:
       image_url = client.logo_url
   ```

---

## Multi-Client Workflow

### Scenario 1: Onboard 10 Clients Fast
1. Create ONE default template
2. Set `PLACID_TEMPLATE_ID` in `.env`
3. Onboard all clients without custom templates
4. ✅ All clients auto-generate with default design

### Scenario 2: Enterprise Client Needs Custom Branding
1. Create custom template with their logo/colors
2. Set `client.placid_template_id = "custom-template-uuid"`
3. ✅ This client gets custom branding, others use default

### Scenario 3: Upgrade Client from Default to Custom
1. Client starts with default template
2. Later, create custom template for them
3. Update `client.placid_template_id`
4. ✅ Future posts use custom branding (past posts unchanged)

---

## Troubleshooting

### Image Not Generating

**Check 1: Is Placid configured?**
```bash
# Check .env
grep PLACID_API_KEY .env
```

**Check 2: Does client have template?**
```sql
SELECT business_name, placid_template_id FROM clients WHERE id = 1;
```

**Check 3: Is fallback template set?**
```bash
grep PLACID_TEMPLATE_ID .env
```

### Wrong Template Being Used

**Priority system:**
1. Client template → 2. Global template → 3. No image

Check which template is being used:
```python
# In auto_content_generator.py, the system logs:
print(f"🎨 Generating Placid image for: {topic}")
# Check server logs to see if image was generated
```

### Template Missing Layers

**Error:** Placid returns error about missing layer

**Fix:** Ensure your template has ALL required layers:
- `title`
- `business_name`
- `background_color`

**Optional layers can be skipped** but required layers must exist.

---

## Advanced: Dynamic Template Selection

For advanced users, you can create multiple templates per client:

```python
# Example: Different templates for different content types
if content_type == "before_after":
    template_id = client.placid_template_before_after
elif content_type == "testimonial":
    template_id = client.placid_template_testimonial
else:
    template_id = client.placid_template_id  # Default
```

Add these fields to Client model as needed.

---

## Cost Considerations

**Placid Pricing:**
- Charged per image generated
- Check [Placid pricing](https://placid.app/pricing) for current rates

**Optimization Tips:**
1. Use default template for most clients
2. Only create custom templates for paying/premium clients
3. Set `max_uses=3` in auto_content_generator to prefer real images over generated ones
4. Images are only generated when:
   - Client has no photos
   - All photos used 3+ times
   - Client submits empty form

---

## Summary

### Quick Onboarding (5 minutes):
1. Create one Placid template
2. Add to `.env` as `PLACID_TEMPLATE_ID`
3. ✅ All clients ready to auto-generate

### Custom Branding (15 minutes per client):
1. Create client-specific template in Placid
2. Set `client.placid_template_id`
3. ✅ Client gets custom branded images

### Hybrid Approach (Recommended):
- Default template for standard clients
- Custom templates for premium clients
- Best balance of speed and customization

---

**Questions?** Check the Placid API docs: https://placid.app/docs

**Last Updated:** November 4, 2025
