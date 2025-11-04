# 🎯 OpenRouter Unified Setup - ONE API Key for Everything!

## ✅ Why OpenRouter?

Instead of managing multiple API keys for different AI services, **OpenRouter gives you access to ALL models with ONE API key:**

- ✅ Google Gemini (for content generation)
- ✅ OpenAI GPT-4 (for post-polishing)
- ✅ Anthropic Claude (for platform variations)
- ✅ 100+ other models

**Result:** Simpler setup, easier billing, one place to manage everything!

---

## 🚀 Quick Setup (3 Steps)

### 1. Get Your OpenRouter API Key

Visit: https://openrouter.ai/keys

Sign up and create an API key. It looks like:
```
sk-or-v1-abc123...
```

### 2. Configure Your `.env`

**That's it! Just ONE key:**

```bash
# OpenRouter - ONE API KEY for everything!
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
USE_OPENROUTER=true

# Content Generation Model
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # For platform variations
USE_GEMINI=true  # Use Gemini for main content
GEMINI_MODEL=google/gemini-pro-1.5

# Content Polisher Model
POLISHER_MODEL=openai/gpt-4-turbo-preview  # GPT-4 for grammar/polish
```

### 3. Start Your Server

```bash
./venv/bin/uvicorn app.main:app --reload
```

**Done!** All AI services now work through OpenRouter.

---

## 🎨 How the System Uses Different Models

The system intelligently uses different models for different tasks:

| Task | Model (via OpenRouter) | Why? |
|------|------------------------|------|
| **Main Caption Generation** | `google/gemini-pro-1.5` | Fast, creative, natural-sounding |
| **Platform Variations** | `anthropic/claude-3.5-sonnet` | Excellent at following format rules |
| **Grammar/Polish** | `openai/gpt-4-turbo-preview` | Best for editing and clarity |

All three models are accessed through your **single OpenRouter API key**.

---

## 💰 Cost Comparison

### Before (Multiple APIs):
- OpenAI API: $20/month minimum
- Anthropic API: $20/month minimum
- Google Gemini API: Separate billing
- **Total:** $40-60+/month + complexity

### After (OpenRouter Only):
- OpenRouter: Pay-as-you-go
- All models included
- Unified billing
- **Total:** ~$10-30/month (usage-based)

---

## 🔧 Advanced Configuration

### Change Models Easily

Want to use different models? Just update `.env`:

```bash
# Use GPT-4 for everything (more expensive but highest quality)
USE_GEMINI=false
OPENROUTER_MODEL=openai/gpt-4-turbo-preview
POLISHER_MODEL=openai/gpt-4-turbo-preview

# Use Claude for everything (balanced cost/quality)
USE_GEMINI=false
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
POLISHER_MODEL=anthropic/claude-3.5-sonnet

# Use Gemini for everything (cheapest, still great quality)
USE_GEMINI=true
GEMINI_MODEL=google/gemini-pro-1.5
POLISHER_MODEL=google/gemini-pro-1.5
```

### Available Models on OpenRouter

Popular models you can use:

**Free/Cheap:**
- `google/gemini-flash-1.5` - Fast and free
- `meta-llama/llama-3.1-8b-instruct:free` - Free

**High Quality:**
- `google/gemini-pro-1.5` - Excellent quality, affordable
- `anthropic/claude-3.5-sonnet` - Top tier reasoning
- `openai/gpt-4-turbo-preview` - Industry standard

**Ultra High Quality:**
- `anthropic/claude-opus` - Best reasoning
- `openai/o1-preview` - Advanced reasoning

See all: https://openrouter.ai/models

---

## 🧪 Testing Your Setup

Run the validation script:

```bash
./venv/bin/python validate_system.py
```

You should see:
```
✅ AI Service initialized with OpenRouter (anthropic/claude-3.5-sonnet)
✅ Content Polisher initialized with OpenRouter (openai/gpt-4-turbo-preview)
```

---

## 🔍 How It Works Internally

### Content Generation Workflow:

```
1. User submits form
   ↓
2. GEMINI (via OpenRouter) generates raw caption
   - Temperature: 0.9 (creative)
   - Local expert tone
   ↓
3. GPT-4 (via OpenRouter) polishes caption
   - Temperature: 0.3 (consistent)
   - Grammar, clarity, tone
   ↓
4. Hashtag Generator adds smart tags
   ↓
5. CLAUDE (via OpenRouter) creates platform variations
   - FB: conversational
   - IG: visual
   - LI: professional
   ↓
6. GPT-4 (via OpenRouter) polishes each variation
   ↓
7. Ready for approval/publishing!
```

**Everything flows through your ONE OpenRouter API key!**

---

## ⚠️ Common Issues

### Issue: "Content Polisher disabled"

**Solution:** Make sure `.env` has:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key
USE_OPENROUTER=true
```

### Issue: "Rate limit exceeded"

**Solution:** OpenRouter has generous limits. If you hit them:
1. Add payment method at https://openrouter.ai/settings/billing
2. Or switch to free models temporarily

### Issue: "Model not found"

**Solution:** Check model names at https://openrouter.ai/models
- Use exact names like `google/gemini-pro-1.5`
- Not `gemini-pro` or `gemini`

---

## 📊 Monitoring Usage

Track your usage and costs:
1. Go to: https://openrouter.ai/activity
2. See all requests, costs, and models used
3. Set budget limits if desired

---

## 🎯 Best Practices

### For Quality:
```bash
USE_GEMINI=true
GEMINI_MODEL=google/gemini-pro-1.5  # Main content
POLISHER_MODEL=openai/gpt-4-turbo-preview  # Polish
```

### For Speed:
```bash
USE_GEMINI=true
GEMINI_MODEL=google/gemini-flash-1.5  # Faster
POLISHER_MODEL=google/gemini-flash-1.5  # Fast polish
```

### For Cost:
```bash
USE_GEMINI=true
GEMINI_MODEL=google/gemini-flash-1.5  # Often free!
POLISHER_MODEL=google/gemini-flash-1.5
```

---

## 🔗 Useful Links

- **OpenRouter Dashboard:** https://openrouter.ai/
- **API Keys:** https://openrouter.ai/keys
- **Model List:** https://openrouter.ai/models
- **Pricing:** https://openrouter.ai/models (shown per model)
- **Usage:** https://openrouter.ai/activity
- **Docs:** https://openrouter.ai/docs

---

## ✅ Summary

**Old Way:**
- Multiple API keys
- Multiple billing accounts
- Complex configuration
- Higher costs

**New Way (OpenRouter):**
- ✅ ONE API key
- ✅ ONE billing account
- ✅ Simple `.env` configuration
- ✅ Lower costs
- ✅ More model options
- ✅ Easier to manage

**Your entire AI stack runs on one API key!** 🎉
