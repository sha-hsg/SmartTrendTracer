#!/bin/bash

# Script to restart the backend server
echo "🔄 Restarting SmartTrendTracer Backend Server..."

# Find and kill the current server process
echo "Stopping current server..."
pkill -f "python run_server.py"
sleep 2

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Start the server again
echo "Starting server..."
python run_server.py &

echo "✅ Server restarted! The statistics endpoint should now work."
echo "Check: http://localhost:8000/api/statistics/overview"