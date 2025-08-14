#!/bin/bash
# Clean start script - kills any existing servers and starts fresh

echo "🧹 SmartTrendTracer Clean Start"
echo "================================"

# 1. Kill any existing Python servers
echo "1. Checking for existing servers..."

# Check port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "   ⚠️  Found process on port 8000"
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "   Killing PID: $PID"
    kill -9 $PID 2>/dev/null
    sleep 1
fi

# Check for any run.py or uvicorn processes
PIDS=$(ps aux | grep -E "python.*(run|uvicorn|main)" | grep -v grep | awk '{print $2}')
if [ ! -z "$PIDS" ]; then
    echo "   ⚠️  Found Python server processes: $PIDS"
    for PID in $PIDS; do
        echo "   Killing PID: $PID"
        kill -9 $PID 2>/dev/null
    done
    sleep 1
fi

echo "   ✅ All old processes cleared"

# 2. Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo ""
    echo "2. ⚠️  Virtual environment not activated!"
    echo "   Please run: source venv/bin/activate"
    echo "   Then run this script again"
    exit 1
else
    echo ""
    echo "2. ✅ Virtual environment active: $VIRTUAL_ENV"
fi

# 3. Start the server
echo ""
echo "3. Starting fresh server..."
echo "================================"
echo ""

# Use the improved run script
if [ -f "run_server.py" ]; then
    python run_server.py
else
    python run.py
fi