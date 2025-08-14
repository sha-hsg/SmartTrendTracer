#!/bin/bash
# Script to run the media fixer in the background

echo "Starting automatic media fixer..."
echo "This will run continuously until all media is collected"
echo "Check progress with: tail -f media_fix.log"
echo ""

cd /Users/siehan/Sync/05-Development/02-SG/SG2025/SmartTrendTracer/backend
source venv/bin/activate

# Run in background and log output
nohup python fix_media_auto.py > media_fix.log 2>&1 &

echo "✅ Media fixer started in background with PID: $!"
echo ""
echo "Commands:"
echo "  View progress:  tail -f media_fix.log"
echo "  Stop fixer:     kill $!"
echo ""
echo "The script will automatically:"
echo "  - Process tweets in batches of 8"
echo "  - Wait 15 minutes when rate limited"
echo "  - Continue until all media is collected"
echo "  - Save progress between runs"