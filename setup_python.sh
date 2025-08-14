#!/bin/bash

echo "🚀 Setting up SmartTrendTracer Python Edition"
echo "============================================"

# Check Python version (macOS compatible)
python_version=$(python3 --version 2>&1 | sed 's/Python //')
echo "✅ Python $python_version detected"

# Backend setup
echo ""
echo "📦 Setting up Python backend..."
cd backend

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Database
DATABASE_URL=sqlite:///../data/tweets.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Frontend URL
FRONTEND_URL=http://localhost:3000
EOL
    echo "⚠️  Please edit backend/.env and add your TWITTER_BEARER_TOKEN"
fi

# Frontend setup
echo ""
echo "📦 Setting up React frontend..."
cd ../frontend

# Install dependencies
echo "Installing Node dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit backend/.env and add your TWITTER_BEARER_TOKEN"
echo "2. Start the backend: cd backend && source venv/bin/activate && python run.py"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "📖 See README_PYTHON.md for detailed documentation"