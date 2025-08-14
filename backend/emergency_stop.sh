#!/bin/bash
# Emergency stop script - force kills the server

echo "🛑 EMERGENCY STOP - Force killing SmartTrendTracer"
echo "=================================================="

# Kill anything on port 8000
echo "Checking port 8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    PIDS=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "Killing processes on port 8000: $PIDS"
    for PID in $PIDS; do
        kill -9 $PID 2>/dev/null
    done
fi

# Kill any Python server processes
echo "Checking for Python server processes..."
PIDS=$(ps aux | grep -E "python.*(run_server|run\.py|uvicorn|main:app)" | grep -v grep | awk '{print $2}')
if [ ! -z "$PIDS" ]; then
    echo "Killing Python processes: $PIDS"
    for PID in $PIDS; do
        kill -9 $PID 2>/dev/null
    done
fi

# Kill any suspended Python processes
echo "Checking for suspended processes..."
SUSPENDED=$(jobs -l 2>/dev/null | grep python | awk '{print $2}')
if [ ! -z "$SUSPENDED" ]; then
    echo "Killing suspended processes: $SUSPENDED"
    for PID in $SUSPENDED; do
        kill -9 $PID 2>/dev/null
    done
fi

echo ""
echo "✅ All server processes killed"
echo ""
echo "You can now start fresh with:"
echo "  python run_server.py"
echo ""
echo "Or better, use the simple collector:"
echo "  python collect_tweets.py"