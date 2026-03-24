#!/bin/bash

# CareerLens Quick Start - Local Development
# This script sets up the entire development environment

set -e

echo "🚀 CareerLens - Local Development Setup"
echo "========================================"

# Check prerequisites
echo "✓ Checking prerequisites..."
command -v docker &> /dev/null || { echo "❌ Docker not found. Please install Docker."; exit 1; }
command -v docker-compose &> /dev/null || { echo "❌ Docker Compose not found. Please install Docker Compose."; exit 1; }

# Setup environment
echo "✓ Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
else
    echo "  .env already exists"
fi

# Clean previous containers
echo "✓ Cleaning up previous containers..."
docker-compose down -v 2>/dev/null || true

# Build and start services
echo "✓ Building Docker images (this may take a few minutes)..."
docker-compose build --no-cache

echo "✓ Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
max_attempts=30
attempts=0

while [ $attempts -lt $max_attempts ]; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "✓ Backend API is ready"
        break
    fi
    attempts=$((attempts + 1))
    echo "  Attempt $attempts/$max_attempts..."
    sleep 2
done

if [ $attempts -eq $max_attempts ]; then
    echo "❌ Backend API failed to start. Check logs with: docker-compose logs backend"
    exit 1
fi

# Show access information
echo ""
echo "✅ Setup Complete!"
echo ""
echo "🌐 Access your application:"
echo "  Backend API:          http://localhost:8000"
echo "  API Documentation:    http://localhost:8000/docs"
echo "  Frontend:             http://localhost:3000"
echo "  MySQL:                localhost:3306"
echo ""
echo "📚 Next Steps:"
echo "  1. Visit http://localhost:3000 in your browser"
echo "  2. Upload a resume to test the analysis"
echo "  3. Check API docs at http://localhost:8000/docs"
echo ""
echo "🛑 To stop all services:"
echo "  docker-compose down"
echo ""
echo "📋 View logs:"
echo "  docker-compose logs -f backend   # Backend API logs"
echo "  docker-compose logs -f frontend  # Frontend logs"
echo "  docker-compose logs -f mysql     # Database logs"
echo ""
echo "🧹 To clean up everything (dev only):"
echo "  docker-compose down -v"
echo ""
