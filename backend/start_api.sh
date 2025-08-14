#!/bin/bash
# Start only the API server (without tweet collection)

echo "🌐 Starting SmartTrendTracer API Server"
echo "========================================"
echo ""
echo "Note: This starts ONLY the API server."
echo "Tweet collection must be run separately with:"
echo "  ./start_collector.sh"
echo ""
echo "Starting server..."
echo ""

# Start the API server
uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload