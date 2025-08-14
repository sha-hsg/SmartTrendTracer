#!/bin/bash
# Run both the API server and tweet collector service

echo "🚀 Starting SmartTrendTracer Services"
echo "======================================"

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_PID $COLLECTOR_PID 2>/dev/null
    wait $API_PID $COLLECTOR_PID 2>/dev/null
    echo "✅ Services stopped"
    exit
}

# Set up trap for cleanup
trap cleanup INT TERM

# Start the tweet collector in background
echo "📊 Starting Tweet Collector Service..."
python tweet_collector_service.py &
COLLECTOR_PID=$!
echo "   PID: $COLLECTOR_PID"

# Give collector a moment to start
sleep 2

# Start the API server
echo "🌐 Starting API Server..."
uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "   PID: $API_PID"

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📌 API Server: http://localhost:8000"
echo "📌 API Docs: http://localhost:8000/docs"
echo "📌 Tweet Collector: Running every 15 minutes"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================"

# Wait for processes
wait $API_PID $COLLECTOR_PID