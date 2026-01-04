#!/bin/bash

# Start FastAPI server for Vector Recall System API

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Starting Vector Recall System API..."
echo "Project root: $PROJECT_ROOT"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start FastAPI server
echo "Starting FastAPI server..."
echo "Server will be available at: http://0.0.0.0:8001"
echo "API documentation: http://0.0.0.0:8001/docs"
echo "Redoc documentation: http://0.0.0.0:8001/redoc"
echo "-" * 50

uvicorn interface.api.main:app --host 0.0.0.0 --port 8001 --reload
