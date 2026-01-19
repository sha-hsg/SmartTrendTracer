#!/bin/bash

echo "=========================================="
echo "MinerU Service Setup"
echo "=========================================="

# Create isolated virtual environment
if [ ! -d "mineru_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv mineru_env
else
    echo "Virtual environment already exists"
fi

# Activate environment
source mineru_env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install MinerU with specific dependencies
echo "Installing MinerU..."
pip install magic-pdf[full] mineru

# Install web server dependencies
echo "Installing server dependencies..."
pip install fastapi uvicorn python-multipart aiofiles

# Download MinerU models if needed
echo "Setting up MinerU models..."
python -c "from magic_pdf.pipe.UNIPipe import UNIPipe; print('Models setup complete')" 2>/dev/null || echo "Models will be downloaded on first use"

echo ""
echo "=========================================="
echo "MinerU setup complete!"
echo "To start the service, run: ./start_mineru_service.sh"
echo "=========================================="