#!/bin/bash

# Family Psychologist Bot Setup Script
# This script helps with initial setup and configuration

set -e

echo "🔧 Setting up Family Psychologist Bot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Python 3.11+ is installed
print_step "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_status "Python $python_version is installed (✓)"
else
    print_error "Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

# Check if pip is installed
if command -v pip3 &> /dev/null; then
    print_status "pip3 is installed (✓)"
else
    print_error "pip3 is not installed"
    exit 1
fi

# Create virtual environment
print_step "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_step "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_step "Creating necessary directories..."
mkdir -p memory logs

# Set proper permissions
chmod 755 memory logs

# Check if .env file exists
if [ ! -f .env ]; then
    print_step "Creating .env file from template..."
    cp env.example .env
    print_warning "Please edit .env file with your actual tokens and settings"
else
    print_status ".env file already exists"
fi

# Check Docker installation
print_step "Checking Docker installation..."
if command -v docker &> /dev/null; then
    print_status "Docker is installed (✓)"
    
    if command -v docker-compose &> /dev/null; then
        print_status "Docker Compose is installed (✓)"
    else
        print_warning "Docker Compose is not installed. Install it for containerized deployment."
    fi
else
    print_warning "Docker is not installed. Install it for containerized deployment."
fi

# Create git hooks
print_step "Setting up git hooks..."
mkdir -p .git/hooks

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook to run tests and linting

echo "Running pre-commit checks..."

# Run tests
python -m pytest tests/ -v

# Run linting
python -m black . --check
python -m isort . --check-only
python -m mypy .

echo "Pre-commit checks completed"
EOF

chmod +x .git/hooks/pre-commit

# Create development script
print_step "Creating development scripts..."

cat > scripts/dev.sh << 'EOF'
#!/bin/bash
# Development script

source venv/bin/activate
export PYTHONPATH=$PWD

echo "Starting development server..."
python main.py
EOF

chmod +x scripts/dev.sh

# Create test script
cat > scripts/test.sh << 'EOF'
#!/bin/bash
# Test script

source venv/bin/activate
export PYTHONPATH=$PWD

echo "Running tests..."
python -m pytest tests/ -v --cov=. --cov-report=html

echo "Running linting..."
python -m black . --check
python -m isort . --check-only
python -m mypy .
EOF

chmod +x scripts/test.sh

print_status "Setup completed successfully! 🎉"

echo ""
echo "Next steps:"
echo "1. Edit .env file with your tokens:"
echo "   - TELEGRAM_BOT_TOKEN (get from @BotFather)"
echo "   - OPENAI_API_KEY (get from OpenAI)"
echo ""
echo "2. For local development:"
echo "   ./scripts/dev.sh"
echo ""
echo "3. For testing:"
echo "   ./scripts/test.sh"
echo ""
echo "4. For deployment:"
echo "   ./scripts/deploy.sh"
echo ""
echo "5. For production deployment on VPS:"
echo "   docker-compose up -d"
echo ""

print_status "Happy coding! 💕" 