#!/bin/bash

echo "🚀 Social Automation SaaS - Setup Script"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your API keys!"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Ask user if they want to start with Docker
read -p "🐳 Do you want to start the application with Docker? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🐳 Starting application with Docker..."
    docker-compose up -d
    echo ""
    echo "✅ Application is starting!"
    echo ""
    echo "📍 Services:"
    echo "   - API: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - PostgreSQL: localhost:5432"
    echo "   - Redis: localhost:6379"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Stop application:"
    echo "   docker-compose down"
    echo ""
else
    echo "💻 To run locally without Docker:"
    echo ""
    echo "1. Install dependencies:"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "2. Start PostgreSQL and Redis"
    echo ""
    echo "3. Run FastAPI:"
    echo "   uvicorn app.main:app --reload"
    echo ""
    echo "4. Run Celery worker (in another terminal):"
    echo "   celery -A app.tasks worker --loglevel=info"
    echo ""
    echo "5. Run Celery beat (in another terminal):"
    echo "   celery -A app.tasks beat --loglevel=info"
    echo ""
fi

echo "📚 For more information, see README.md"
echo ""
echo "🎉 Setup complete!"
