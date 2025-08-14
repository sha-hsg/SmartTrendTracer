#!/bin/bash
# Stop the SmartTrendTracer backend server

echo "🛑 Stopping SmartTrendTracer Backend..."

# Find and kill the process
PID=$(ps aux | grep "python run" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "✅ Server is not running"
else
    echo "Found server process: PID $PID"
    echo "Sending shutdown signal..."
    kill -TERM $PID
    
    # Wait a moment
    sleep 2
    
    # Check if still running
    if ps -p $PID > /dev/null; then
        echo "⚠️  Process still running, forcing shutdown..."
        kill -9 $PID
    fi
    
    echo "✅ Server stopped"
fi

# Also check for uvicorn processes
UVICORN_PID=$(ps aux | grep "uvicorn" | grep "app.main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$UVICORN_PID" ]; then
    echo "Found uvicorn process: PID $UVICORN_PID"
    kill -9 $UVICORN_PID
    echo "✅ Uvicorn stopped"
fi