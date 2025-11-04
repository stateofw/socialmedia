# 🔌 How Users Connect Their WordPress

**Updated:** October 31, 2025
**Status:** ✅ FULLY FUNCTIONAL - User-Friendly UI Added

---

## 🎯 Quick Answer

Users connect WordPress through a **simple web form** in the client dashboard. No technical knowledge required!

**Process:**
1. Admin logs into dashboard
2. Clicks on a client
3. Fills out WordPress connection form
4. Tests connection with one click
5. Saves - Done!

---

## 📋 Step-by-Step Instructions for Users

### Step 1: Access Client Dashboard

1. **Login to admin dashboard:** http://localhost:8000/admin/login
2. **Navigate to Clients page:** Click "Clients" in the menu
3. **Click on the client** you want to connect WordPress for

### Step 2: Get WordPress Application Password

On the **client's WordPress site** (not your automation platform):

1. Log in to **WordPress admin** (https://clientwebsite.com/wp-admin)
2. Go to **Users → Profile**
3. Scroll down to **"Application Passwords"** section
4. Enter application name: `Social Automation`
5. Click **"Add New Application Password"**
6. **Copy the generated password** (format: `xxxx xxxx xxxx xxxx xxxx xxxx`)

> **Important:** This is NOT the regular WordPress login password. It's a special app password that's more secure.

### Step 3: Fill Out Connection Form

Back on your automation platform client detail page:

1. **WordPress Site URL:** Enter the full URL
   - Example: `https://clientwebsite.com`
   - Include `https://` or `http://`

2. **WordPress Username:** Enter the WordPress admin username
   - Example: `admin` or `john@example.com`

3. **Application Password:** Paste the password you copied
   - Example: `abcd efgh ijkl mnop qrst uvwx`

4. **Test connection before saving:** Leave this checked (recommended)

### Step 4: Test & Save

1. Click **"Test Connection"** button (optional but recommended)
   - ✅ Success: Shows "Connection successful!"
   - ❌ Fail: Shows error message with troubleshooting info

2. Click **"Save WordPress Settings"**
   - Settings are encrypted and stored securely
   - Green "Connected" badge appears

**Done!** WordPress is now connected for this client.

---

## 🖼️ What the UI Looks Like

### Client Detail Page Structure

```
┌─────────────────────────────────────────────────┐
│  Client Name                      [Active]       │
│  Industry • Location                             │
├─────────────────────────────────────────────────┤
│                                                  │
│  LEFT COLUMN:                  RIGHT COLUMN:     │
│  ├─ Client Information         ├─ WordPress      │
│  │  • Business Name              Integration     │
│  │  • Industry                   [Connected]     │
│  │  • Location                                   │
│  │  • Website                  ┌──────────────┐ │
│  │  • Post Limit               │ Instructions │ │
│  │  • Auto-posting             └──────────────┘ │
│  │                                               │
│  ├─ Social Platforms           Site URL: [____] │
│  │  [FB] [IG] [LI]            Username: [____]  │
│  │                            Password: [____]  │
│  ├─ Brand Voice                [x] Test first   │
│     "Friendly, professional"                    │
│                                [Test] [Save]    │
│                                                  │
│                               Recent Content:    │
│                               • Post 1 →        │
│                               • Post 2 →        │
└─────────────────────────────────────────────────┘
```

### Built-in Help Instructions

The form includes step-by-step instructions on how to get WordPress credentials:

```
┌────────────────────────────────────────────────┐
│ ℹ️ How to get WordPress credentials:          │
├────────────────────────────────────────────────┤
│ 1. Log in to the client's WordPress admin      │
│ 2. Go to Users → Profile                       │
│ 3. Scroll to Application Passwords section     │
│ 4. Enter name: "Social Automation"             │
│ 5. Click Add New Application Password          │
│ 6. Copy the generated password                 │
│ 7. Paste it below                              │
└────────────────────────────────────────────────┘
```

---

## 🔧 What Happens Behind the Scenes

### When User Clicks "Save"

1. **Validation:** Checks all fields are filled
2. **Connection Test** (if enabled):
   - Sends test request to WordPress REST API
   - Verifies credentials are correct
   - Confirms site is accessible
3. **Encryption:** Stores credentials securely in database
4. **Confirmation:** Shows success message

### Database Storage

```sql
platform_configs table:
├─ client_id: 1
├─ platform: "wordpress"
├─ is_active: true
├─ config: {"site_url": "https://...", "username": "admin"}
└─ access_token: "xxxx xxxx xxxx xxxx" (encrypted)
```

### Security Features

- ✅ **App Passwords Only** - Not regular WordPress passwords
- ✅ **Encrypted Storage** - Credentials stored securely
- ✅ **Per-User Access** - Users only see their own clients
- ✅ **HTTPS Required** - Secure connection to WordPress
- ✅ **Test Before Save** - Validates credentials work
- ✅ **Easy Disconnect** - One-click to remove connection

---

## 🎬 Using WordPress After Connection

### Publishing a Blog Post

Once WordPress is connected:

1. **Create social content** (via dashboard or API)
2. **AI generates caption** → Status: `pending_approval`
3. **Review in dashboard** → Click "Generate Blog"
4. **AI creates blog article** (30-60 seconds)
5. **Click "Publish to WordPress"**
6. **Blog appears on client's WordPress site** ✅

### Where to Find These Buttons

**Client Content Detail Page:**
```
┌──────────────────────────────────────┐
│ Content: "5 Marketing Tips"          │
├──────────────────────────────────────┤
│ Caption: "In today's market..."      │
│                                       │
│ [Generate Blog Post]  ← Step 1       │
│                                       │
│ Blog Title: "5 Essential Marketing..." │
│ Blog Content: (800 words)            │
│                                       │
│ [Publish to WordPress]  ← Step 2     │
│                                       │
│ WordPress URL: https://client.com/... │
└──────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### "Connection Failed" Error

**Possible Causes:**
1. Wrong site URL (check https vs http)
2. Invalid username or password
3. WordPress REST API disabled
4. Security plugin blocking API

**Solutions:**
```bash
# Test WordPress API manually:
curl https://clientsite.com/wp-json/wp/v2/posts

# Should return JSON, not error
```

### "Invalid Credentials" Error

**Fixes:**
1. Double-check username (it's case-sensitive)
2. Regenerate application password in WordPress
3. Make sure you copied the full password (with spaces)
4. Try a different WordPress user with admin rights

### "Site Not Found" Error

**Fixes:**
1. Verify site URL is correct
2. Include `https://` or `http://`
3. Remove trailing slash
4. Check site is actually online

### WordPress App Password Not Showing

**Requirement:** WordPress 5.6 or higher

**If missing:**
1. Update WordPress to latest version
2. Check if disabled in config (ALLOW_APPLICATION_PASSWORDS)
3. Use plugin: "Application Passwords" for older versions

---

## 🔐 Security Best Practices

### For Users (Your Customers)

1. **Use App Passwords, not regular passwords**
   - More secure
   - Can be revoked independently
   - Doesn't expose main password

2. **Create dedicated user for automation**
   ```
   WordPress → Users → Add New
   Username: social-automation
   Role: Editor or Author
   Generate app password for this user
   ```

3. **Revoke old passwords**
   - Go to Users → Profile → Application Passwords
   - Click "Revoke" on unused passwords

4. **Monitor WordPress activity**
   - Use WordPress Activity Log plugin
   - Check who's posting what

### For Platform Admins (You)

1. **Never log credentials**
   - Passwords are masked in all logs
   - Only connection success/failure logged

2. **Use HTTPS for WordPress sites**
   - Reject HTTP-only sites
   - Credentials sent over encrypted connection

3. **Regular security audits**
   ```sql
   -- Check all connected WordPress sites
   SELECT client_id, config->>'site_url' as site
   FROM platform_configs
   WHERE platform = 'wordpress' AND is_active = true;
   ```

---

## 📊 Connection Status Indicators

### Visual Badges

**Not Connected:**
```
[Not Connected] (gray badge)
```

**Connected:**
```
[✓ Connected] (green badge)
```

**Connection Error:**
```
[⚠ Error] (red badge)
```

### How to Check Connection Status

```sql
-- Via database:
SELECT
    c.business_name,
    pc.is_active,
    pc.config->>'site_url' as wordpress_url
FROM clients c
LEFT JOIN platform_configs pc ON c.id = pc.client_id AND pc.platform = 'wordpress'
WHERE c.id = 1;
```

---

## 🔄 Updating Connection

### To Update WordPress Credentials

1. Go to client detail page
2. **Site URL/Username:** Just change and save
3. **Password:**
   - Leave blank to keep existing password
   - Enter new password to update it
4. Click "Save WordPress Settings"

### To Disconnect WordPress

1. Go to client detail page
2. Click **"Disconnect WordPress"** (red button)
3. Confirm action
4. Credentials removed from database

**Note:** This doesn't delete anything on WordPress - just removes the connection.

---

## 📱 Mobile-Friendly

The WordPress connection form is **fully responsive**:
- ✅ Works on phone browsers
- ✅ Works on tablets
- ✅ Touch-friendly buttons
- ✅ Clear error messages

---

## 🎓 Training Your Users

### Quick Training Checklist

Share this with users who need to connect WordPress:

- [ ] How to access client detail page
- [ ] Where to find WordPress app passwords
- [ ] How to fill out the form
- [ ] What "Test Connection" does
- [ ] How to publish blog posts after connecting
- [ ] What to do if connection fails

### User Documentation Template

```markdown
# Connecting Your WordPress Site

1. Login to your dashboard
2. Go to Clients → Click your client
3. In WordPress section, fill out:
   - Site URL: https://yoursite.com
   - Username: Your WP username
   - Password: Get from WP → Users → Profile → App Passwords
4. Click "Test Connection"
5. Click "Save"
6. Done! You can now publish blogs to WordPress automatically
```

---

## 🚀 API Alternative (Advanced)

For users comfortable with APIs:

```bash
# Connect WordPress via API
curl -X POST http://localhost:8000/admin/clients/1/wordpress \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=YOUR_TOKEN" \
  -d '{
    "site_url": "https://clientsite.com",
    "username": "admin",
    "app_password": "xxxx xxxx xxxx xxxx",
    "test_connection": true
  }'

# Response:
{
  "success": true,
  "message": "WordPress settings saved successfully!"
}
```

---

## 📊 Quick Reference

### Access Points
- **UI:** http://localhost:8000/admin/clients/{id}
- **API:** POST /admin/clients/{id}/wordpress

### Required Information
1. WordPress Site URL
2. WordPress Username
3. WordPress Application Password

### Features
- ✅ One-click connection test
- ✅ Auto-save with validation
- ✅ Visual status indicators
- ✅ Built-in help instructions
- ✅ Secure credential storage
- ✅ Easy disconnect option

---

## ✅ Summary

**For End Users:**
Connecting WordPress is as simple as filling out a 3-field form with built-in instructions. No technical knowledge required.

**For Developers:**
Full REST API available for programmatic connections with validation and testing.

**Security:**
Industry-standard security with app passwords, encrypted storage, and HTTPS-only connections.

**Your users can now connect their WordPress sites in under 2 minutes!** 🎉

---

**Documentation Created:** October 31, 2025
**Feature Status:** Production Ready ✅
**User Difficulty:** Easy (2/10)
