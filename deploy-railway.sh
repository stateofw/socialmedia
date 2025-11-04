#!/bin/bash

# Quick Railway Deployment Script
# Run this to deploy to Railway in minutes!

set -e

echo "🚀 Railway Deployment Script"
echo "=============================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "✅ Railway CLI found"
echo ""

# Login to Railway
echo "🔑 Logging into Railway..."
railway login

echo ""
echo "📦 Initializing Railway project..."
railway init

echo ""
echo "🗄️  Adding PostgreSQL database..."
railway add --database postgres

echo ""
echo "🔴 Adding Redis..."
railway add --database redis

echo ""
echo "⚙️  Environment Variables Setup"
echo "================================"
echo "You need to set the following environment variables in the Railway dashboard:"
echo ""
echo "Required:"
echo "  - SECRET_KEY (generate with: openssl rand -hex 32)"
echo "  - OPENROUTER_API_KEY"
echo "  - PLACID_API_KEY"
echo "  - PUBLER_API_KEY"
echo "  - PUBLER_WORKSPACE_ID"
echo ""
echo "Optional:"
echo "  - AWS_ACCESS_KEY_ID"
echo "  - AWS_SECRET_ACCESS_KEY"
echo "  - GOOGLE_CLIENT_ID"
echo "  - GOOGLE_CLIENT_SECRET"
echo "  - etc."
echo ""
echo "DATABASE_URL and REDIS_URL are automatically set by Railway! ✅"
echo ""

read -p "Press Enter to open Railway dashboard to set environment variables..."
railway open

echo ""
read -p "Have you set all required environment variables? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ Please set environment variables first, then run this script again."
    exit 1
fi

echo ""
echo "🔧 Running database migrations..."
railway run alembic upgrade head

echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app is being deployed to Railway!"
echo ""
echo "Next steps:"
echo "1. Check deployment status: railway status"
echo "2. View logs: railway logs"
echo "3. Get app URL: railway open"
echo "4. Test health endpoint: https://your-app.up.railway.app/health"
echo "5. View API docs: https://your-app.up.railway.app/docs"
echo ""
echo "💰 Monitor your usage: https://railway.app/account/usage"
echo ""
