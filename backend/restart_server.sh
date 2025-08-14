#!/bin/bash

echo "🔄 Restarting SmartTrendTracer Backend Server..."

# Find and kill the current server process
echo "Stopping current server (if running)..."
pkill -f "python run_server.py" 2>/dev/null || echo "No server process found"

# Wait a moment for process to fully terminate
sleep 2

# Navigate to backend directory
cd "$(dirname "$0")"

# Start the server
echo "Starting server..."
python run_server.py &

echo "✅ Backend server restarted!"
echo ""
echo "The following fixes have been applied:"
echo "  • Statistics API: Fixed ArticleTag.tag_name → ArticleTag.tag"
echo "  • Rate Limiter: Added missing get_wait_time() method"
echo ""
echo "Check the statistics dashboard at: http://localhost:3000"
echo "API endpoint: http://localhost:8000/api/statistics/overview"
echo ""
echo "Press Ctrl+C in the server terminal to stop it later."