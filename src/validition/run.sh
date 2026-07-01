#!/bin/bash

# ==================================
# Validation - Run Script
# ==================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Validation - AI Backend${NC}"
echo "=================================="

# Check command
case "$1" in
    # Development
    dev)
        echo -e "${YELLOW}Starting development server...${NC}"
        uvicorn main:app --reload --host 0.0.0.0 --port 8004
        ;;

    # Docker Development
    docker-dev)
        echo -e "${YELLOW}Starting with Docker (development)...${NC}"
        docker-compose up --build
        ;;

    # Docker Production
    docker-prod)
        echo -e "${YELLOW}Starting with Docker (production)...${NC}"
        docker-compose -f docker-compose.prod.yml up --build -d
        ;;

    # Celery Worker
    worker)
        echo -e "${YELLOW}Starting Celery worker...${NC}"
        celery -A workers.celery_app worker --loglevel=info -Q validation_queue
        ;;

    # Celery Flower (Monitoring)
    flower)
        echo -e "${YELLOW}Starting Celery Flower...${NC}"
        celery -A workers.celery_app flower --port=5555
        ;;

    # Run Tests
    test)
        echo -e "${YELLOW}Running tests...${NC}"
        pytest tests/ -v
        ;;

    # Run Tests with Coverage
    test-cov)
        echo -e "${YELLOW}Running tests with coverage...${NC}"
        pytest tests/ -v --cov=. --cov-report=html
        ;;

    # Lint
    lint)
        echo -e "${YELLOW}Running linters...${NC}"
        flake8 . --max-line-length=100 --exclude=venv,__pycache__
        black . --check
        isort . --check-only
        ;;

    # Format
    format)
        echo -e "${YELLOW}Formatting code...${NC}"
        black .
        isort .
        ;;

    # Install dependencies
    install)
        echo -e "${YELLOW}Installing dependencies...${NC}"
        pip install -r requirements.txt
        ;;

    # Stop Docker
    stop)
        echo -e "${YELLOW}Stopping Docker containers...${NC}"
        docker-compose down
        ;;

    # Clean
    clean)
        echo -e "${YELLOW}Cleaning up...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        rm -rf htmlcov .coverage 2>/dev/null || true
        echo -e "${GREEN}Done!${NC}"
        ;;

    # Help
    *)
        echo "Usage: ./run.sh {command}"
        echo ""
        echo "Commands:"
        echo "  dev          - Start development server"
        echo "  docker-dev   - Start with Docker (development)"
        echo "  docker-prod  - Start with Docker (production)"
        echo "  worker       - Start Celery worker"
        echo "  flower       - Start Celery Flower monitoring"
        echo "  test         - Run tests"
        echo "  test-cov     - Run tests with coverage"
        echo "  lint         - Run linters"
        echo "  format       - Format code"
        echo "  install      - Install dependencies"
        echo "  stop         - Stop Docker containers"
        echo "  clean        - Clean cache files"
        ;;
esac
