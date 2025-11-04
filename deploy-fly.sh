#!/bin/bash

# Quick Fly.io Deployment Script
# Deploy for FREE with this script!

set -e

echo "🚀 Fly.io Deployment Script (FREE TIER)"
echo "========================================="
echo ""

# Check if Fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Installing..."
    curl -L https://fly.io/install.sh | sh

    # Add to PATH
    export FLYCTL_INSTALL="$HOME/.fly"
    export PATH="$FLYCTL_INSTALL/bin:$PATH"
fi

echo "✅ Fly CLI found"
echo ""

# Login to Fly
echo "🔑 Logging into Fly.io..."
fly auth login

echo ""
echo "📦 Creating Fly.io app..."
fly launch --no-deploy

echo ""
echo "🗄️  Creating PostgreSQL database (FREE tier)..."
fly postgres create --name social-automation-db --region iad --vm-size shared-cpu-1x --volume-size 1

echo ""
echo "🔗 Attaching database to app..."
fly postgres attach social-automation-db

echo ""
echo "📁 Creating persistent volume for media files..."
fly volumes create media_data --size 1 --region iad

echo ""
echo "⚙️  Setting environment variables..."
echo ""
echo "Enter your secrets (they'll be encrypted):"
echo ""

# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
echo "✅ Generated SECRET_KEY automatically"
fly secrets set SECRET_KEY="$SECRET_KEY"

# Ask for required API keys
read -p "Enter your OPENROUTER_API_KEY: " OPENROUTER_KEY
fly secrets set OPENROUTER_API_KEY="$OPENROUTER_KEY"

read -p "Enter your PLACID_API_KEY: " PLACID_KEY
fly secrets set PLACID_API_KEY="$PLACID_KEY"

read -p "Enter your PUBLER_API_KEY: " PUBLER_KEY
fly secrets set PUBLER_API_KEY="$PUBLER_KEY"

read -p "Enter your PUBLER_WORKSPACE_ID: " PUBLER_WORKSPACE
fly secrets set PUBLER_WORKSPACE_ID="$PUBLER_WORKSPACE"

# Set other config
fly secrets set ENV=production
fly secrets set DEBUG=False
fly secrets set USE_OPENROUTER=True

echo ""
read -p "Do you want to add Redis from Upstash (free tier)? (y/n): " add_redis

if [ "$add_redis" = "y" ]; then
    echo ""
    echo "📝 Go to https://upstash.com and create a free Redis database"
    echo "Then copy the connection URL (redis://...)"
    echo ""
    read -p "Enter your Upstash REDIS_URL: " REDIS_URL
    fly secrets set REDIS_URL="$REDIS_URL"
fi

echo ""
echo "🔧 Running database migrations..."
fly ssh console -C "alembic upgrade head"

echo ""
echo "🚀 Deploying to Fly.io..."
fly deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app is live on Fly.io!"
echo ""
echo "Next steps:"
echo "1. Check status: fly status"
echo "2. View logs: fly logs"
echo "3. Get app URL: fly apps list"
echo "4. Test health endpoint: https://your-app.fly.dev/health"
echo "5. View API docs: https://your-app.fly.dev/docs"
echo ""
echo "💰 100% FREE on Fly.io's free tier! (3 VMs, 256MB each)"
echo ""
echo "To scale up: fly scale memory 512"
echo "To add more VMs: fly scale count 2"
echo ""
