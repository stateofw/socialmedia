#!/bin/bash

# Railway Environment Variables Setup Script
# This script helps you set all required environment variables

set -e

echo "🔧 Setting up Railway Environment Variables"
echo "==========================================="
echo ""

# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
echo "✅ Generated SECRET_KEY"

# Set SECRET_KEY
railway variables --set "SECRET_KEY=$SECRET_KEY"
echo "✅ Set SECRET_KEY"

# Set application config
railway variables --set "ENV=production"
railway variables --set "DEBUG=False"
railway variables --set "API_V1_PREFIX=/api/v1"
echo "✅ Set application config"

# Set OpenRouter config
railway variables --set "USE_OPENROUTER=true"
railway variables --set "OPENROUTER_MODEL=anthropic/claude-3.5-sonnet"
railway variables --set "POLISHER_MODEL=openai/gpt-4-turbo-preview"
echo "✅ Set OpenRouter config"

# Set Gemini config
railway variables --set "GEMINI_MODEL=google/gemini-pro-1.5"
railway variables --set "USE_GEMINI=false"
echo "✅ Set Gemini config"

# Set retry config
railway variables --set "RETRY_DELAY_SECONDS=15"
railway variables --set "MAX_RETRY_ATTEMPTS=3"
echo "✅ Set retry config"

echo ""
echo "⚠️  You still need to set these API keys manually:"
echo ""
echo "railway variables --set 'OPENROUTER_API_KEY=your-key-here'"
echo "railway variables --set 'PLACID_API_KEY=your-key-here'"
echo "railway variables --set 'PLACID_TEMPLATE_ID=your-template-id-here'"
echo "railway variables --set 'PUBLER_API_KEY=your-key-here'"
echo "railway variables --set 'PUBLER_WORKSPACE_ID=your-workspace-id-here'"
echo ""
echo "Optional (if using these services):"
echo "railway variables --set 'AWS_ACCESS_KEY_ID=your-key-here'"
echo "railway variables --set 'AWS_SECRET_ACCESS_KEY=your-key-here'"
echo "railway variables --set 'AWS_REGION=us-east-1'"
echo "railway variables --set 'S3_BUCKET_NAME=your-bucket-name'"
echo "railway variables --set 'GOOGLE_CLIENT_ID=your-id-here'"
echo "railway variables --set 'GOOGLE_CLIENT_SECRET=your-secret-here'"
echo "railway variables --set 'META_APP_ID=your-id-here'"
echo "railway variables --set 'META_APP_SECRET=your-secret-here'"
echo ""
echo "✅ Basic environment variables configured!"
