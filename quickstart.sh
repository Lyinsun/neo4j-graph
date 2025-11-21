#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   PRD Review Vector Recall System - Quick Start             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the neo4j directory"
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
cd src
python config.py

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
python demo.py

cd ..
