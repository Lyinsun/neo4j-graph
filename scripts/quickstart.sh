#!/bin/bash

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Neo4j Graph Vector Recall System - Quick Start            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in project root"
    exit 1
fi

# Step 1: Install dependencies
echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Step 2: Verify configuration

echo "[2/3] Verifying configuration..."
python -m infrastructure.config.config

if [ $? -ne 0 ]; then
    echo "Error: Configuration validation failed"
    echo "Please check your .env file"
    exit 1
fi

echo "✓ Configuration validated"
echo ""

# Step 3: Run demo

echo "[3/3] Starting interactive demo..."
echo ""
echo "Running test insert to verify Neo4j functionality..."
python -m interface.cli.main test-insert

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Quick Start Complete!                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Start API server: ./scripts/start_api.sh"
echo "  2. Import data: python -m interface.cli.main import-flight --data-dir data/Flight"
echo "  3. View API docs: http://localhost:8000/docs"
echo ""
