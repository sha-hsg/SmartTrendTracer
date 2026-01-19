#!/bin/bash

echo "=========================================="
echo "Starting MinerU PDF Processing Service"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "mineru_env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup_mineru.sh first"
    exit 1
fi

# Activate environment
source mineru_env/bin/activate

# Check if MinerU is installed
if ! command -v mineru &> /dev/null; then
    echo "❌ MinerU not found in environment!"
    echo "Please run ./setup_mineru.sh to install dependencies"
    exit 1
fi

echo "✅ Environment activated"
echo "🚀 Starting MinerU service on port 8003..."
echo ""

# Start the server
python mineru_server.py