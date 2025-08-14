#!/bin/bash
# Start only the tweet collector service

echo "📊 Starting Tweet Collector Service"
echo "===================================="
echo ""
echo "This will collect tweets every 15 minutes"
echo "from the configured Twitter accounts."
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the tweet collector
python tweet_collector_service.py