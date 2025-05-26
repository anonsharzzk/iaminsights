#!/bin/bash

# Cloud Access Visualizer Deployment Script
# Usage: ./scripts/deploy.sh [development|production]

set -e

ENVIRONMENT=${1:-development}
PROJECT_NAME="cloud-access-visualizer"

echo "🚀 Deploying Cloud Access Visualizer in ${ENVIRONMENT} mode..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running again."
    echo "   Especially change the JWT_SECRET_KEY and admin credentials!"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/mongodb
mkdir -p logs
mkdir -p nginx/ssl

# Generate SSL certificates for development
if [ "$ENVIRONMENT" = "development" ] && [ ! -f nginx/ssl/cert.pem ]; then
    echo "🔐 Generating self-signed SSL certificates for development..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Deploy based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting production deployment..."
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml up -d --build
    
    echo "✅ Production deployment completed!"
    echo "📊 Services status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "🌐 Production URLs:"
    echo "   Frontend: https://localhost (or your domain)"
    echo "   Backend API: https://localhost/api"
    echo "   API Documentation: https://localhost/api/docs"
    
else
    echo "🛠️  Starting development deployment..."
    
    # Build and start services
    docker-compose up -d --build
    
    echo "✅ Development deployment completed!"
    echo "📊 Services status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Development URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8001"
    echo "   API Documentation: http://localhost:8001/docs"
    echo "   MongoDB: mongodb://localhost:27017"
fi

echo ""
echo "📋 Default Admin Credentials:"
echo "   Email: adminn@iamsharan.com"
echo "   Password: Testing@123"
echo ""
echo "⚠️  Remember to change these credentials after first login!"

echo ""
echo "📖 View logs with:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "   docker-compose -f docker-compose.prod.yml logs -f"
else
    echo "   docker-compose logs -f"
fi

echo ""
echo "🛑 Stop services with:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "   docker-compose -f docker-compose.prod.yml down"
else
    echo "   docker-compose down"
fi

echo ""
echo "🎉 Deployment completed successfully!"