#!/bin/bash

# Family Psychologist Bot Deployment Script
# This script automates the deployment process on a VPS

set -e  # Exit on any error

echo "🚀 Starting Family Psychologist Bot Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please create it from env.example"
    exit 1
fi

# Check if required environment variables are set
source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    print_error "TELEGRAM_BOT_TOKEN not set in .env file"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    print_error "OPENAI_API_KEY not set in .env file"
    exit 1
fi

print_status "Environment variables validated"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p memory logs

# Set proper permissions
chmod 755 memory logs

# Stop existing containers if running
print_status "Stopping existing containers..."
docker-compose down || true

# Build and start containers
print_status "Building and starting containers..."
docker-compose up -d --build

# Wait for containers to be ready
print_status "Waiting for containers to be ready..."
sleep 10

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_status "Containers are running successfully!"
else
    print_error "Failed to start containers"
    docker-compose logs
    exit 1
fi

# Show container status
print_status "Container status:"
docker-compose ps

# Show logs
print_status "Recent logs:"
docker-compose logs --tail=20

print_status "Deployment completed successfully! 🎉"
print_status "Bot should now be running and responding to messages"
print_status "Monitor logs with: docker-compose logs -f family-psychologist-bot" 