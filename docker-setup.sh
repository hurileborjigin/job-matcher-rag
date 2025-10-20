
#!/bin/bash
# docker-setup.sh

set -e

echo "🚀 Setting up Job Fair Navigator with Docker + UV"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your Azure OpenAI credentials!"
    echo ""
    read -p "Press enter to continue after editing .env file..."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs data/chroma_db

# Build Docker image
echo ""
echo "🐳 Building Docker image with UV..."
docker-compose build

# Check if jobs.db exists
if [ ! -f data/jobs.db ]; then
    echo ""
    echo "⚠️  No job database found!"
    echo "You need to scrape jobs first."
    echo ""
    read -p "Do you want to scrape jobs now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🕷️  Scraping jobs..."
        docker-compose run --rm app python scripts/scrape_jobs.py
        echo ""
        echo "📊 Building vector store..."
        docker-compose run --rm app python scripts/build_vectorstore.py
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📦 Using UV for package management (faster installs!)"
echo ""
echo "To start the application:"
echo "  docker-compose up"
echo ""
echo "To start in background:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"