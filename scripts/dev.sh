#!/bin/bash
# Development helper script for Receipt AI

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# Commands

cmd_setup() {
    info "Setting up development environment..."
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
        error "Python 3.11+ required (found $PYTHON_VERSION)"
    fi
    info "Python $PYTHON_VERSION detected"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        info "Creating virtual environment..."
        python3 -m venv venv
    else
        info "Virtual environment already exists"
    fi
    
    # Activate venv
    source venv/bin/activate
    
    # Upgrade pip
    info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel -q
    
    # Install dependencies
    info "Installing dependencies..."
    pip install -r requirements.txt -q
    
    # Create .env if not exists
    if [ ! -f ".env" ]; then
        info "Creating .env from template..."
        cp .env.example .env
        warn "Remember to edit .env with your API keys!"
    fi
    
    # Create upload directory
    mkdir -p uploads
    
    info "Setup complete! Run './scripts/dev.sh start' to begin."
}

cmd_start() {
    info "Starting development server..."
    
    # Check if venv exists
    if [ ! -d "venv" ]; then
        error "Virtual environment not found. Run './scripts/dev.sh setup' first."
    fi
    
    source venv/bin/activate
    
    # Check for required services
    if ! command -v redis-server &> /dev/null; then
        warn "Redis not found. Some features may not work."
        warn "Install with: brew install redis (macOS) or apt install redis (Linux)"
    fi
    
    # Start uvicorn with reload
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

cmd_worker() {
    info "Starting Celery worker..."
    
    source venv/bin/activate
    celery -A app.tasks worker --loglevel=info
}

cmd_test() {
    info "Running tests..."
    
    source venv/bin/activate
    pytest -v "$@"
}

cmd_coverage() {
    info "Running tests with coverage..."
    
    source venv/bin/activate
    pytest --cov=app --cov-report=html --cov-report=term-missing
    
    info "Coverage report generated in htmlcov/index.html"
}

cmd_lint() {
    info "Running linters..."
    
    source venv/bin/activate
    
    # Ruff
    info "Running ruff..."
    ruff check app/ || true
    
    # Black check
    info "Checking code formatting..."
    black app/ --check || true
    
    # Type checking
    info "Running type checker..."
    mypy app/ || true
}

cmd_format() {
    info "Formatting code..."
    
    source venv/bin/activate
    
    # Black
    black app/ tests/
    
    # isort
    isort app/ tests/
    
    # Ruff auto-fix
    ruff check --fix app/ tests/ || true
    
    info "Code formatted!"
}

cmd_db_migrate() {
    info "Creating database migration..."
    
    source venv/bin/activate
    
    MESSAGE="$1"
    if [ -z "$MESSAGE" ]; then
        error "Usage: ./scripts/dev.sh db:migrate 'migration message'"
    fi
    
    alembic revision --autogenerate -m "$MESSAGE"
    
    info "Migration created! Review it in migrations/versions/"
}

cmd_db_upgrade() {
    info "Applying database migrations..."
    
    source venv/bin/activate
    alembic upgrade head
    
    info "Database up to date!"
}

cmd_db_downgrade() {
    info "Rolling back last migration..."
    
    source venv/bin/activate
    alembic downgrade -1
    
    info "Rolled back one version"
}

cmd_clean() {
    info "Cleaning up development files..."
    
    # Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Test/coverage
    rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
    
    # Build artifacts
    rm -rf dist build 2>/dev/null || true
    
    info "Cleaned!"
}

cmd_reset() {
    warn "This will delete the database and uploads. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        info "Resetting development environment..."
        
        # Stop docker if running
        docker-compose down -v 2>/dev/null || true
        
        # Remove uploads
        rm -rf uploads/*
        
        # Remove SQLite db if exists
        rm -f receipt_ai.db
        
        info "Reset complete! Run './scripts/dev.sh setup' to start fresh."
    else
        info "Cancelled"
    fi
}

cmd_docker() {
    info "Starting Docker environment..."
    docker-compose up
}

cmd_docker_build() {
    info "Building Docker image..."
    docker-compose build
}

cmd_shell() {
    info "Starting Python shell..."
    
    source venv/bin/activate
    python3 -c "
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.database import *

print('Receipt AI Development Shell')
print('Available:')
print('  settings - App configuration')
print('  SessionLocal - Database session factory')
print('  Document, ExtractionResult - Models')
print()
"
    python3 -i
}

# Main command router

case "$1" in
    setup)
        cmd_setup
        ;;
    start)
        cmd_start
        ;;
    worker)
        cmd_worker
        ;;
    test)
        shift
        cmd_test "$@"
        ;;
    coverage)
        cmd_coverage
        ;;
    lint)
        cmd_lint
        ;;
    format)
        cmd_format
        ;;
    db:migrate)
        cmd_db_migrate "$2"
        ;;
    db:upgrade)
        cmd_db_upgrade
        ;;
    db:downgrade)
        cmd_db_downgrade
        ;;
    clean)
        cmd_clean
        ;;
    reset)
        cmd_reset
        ;;
    docker)
        cmd_docker
        ;;
    docker:build)
        cmd_docker_build
        ;;
    shell)
        cmd_shell
        ;;
    *)
        echo "Receipt AI Development Helper"
        echo ""
        echo "Usage: ./scripts/dev.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup           - Setup development environment"
        echo "  start           - Start development server"
        echo "  worker          - Start Celery worker"
        echo "  test [args]     - Run tests"
        echo "  coverage        - Run tests with coverage report"
        echo "  lint            - Run linters (ruff, black, mypy)"
        echo "  format          - Auto-format code"
        echo "  db:migrate <msg>- Create database migration"
        echo "  db:upgrade      - Apply migrations"
        echo "  db:downgrade    - Rollback last migration"
        echo "  clean           - Remove cache files"
        echo "  reset           - Reset database and uploads"
        echo "  docker          - Start Docker environment"
        echo "  docker:build    - Build Docker image"
        echo "  shell           - Python shell with app context"
        echo ""
        ;;
esac
