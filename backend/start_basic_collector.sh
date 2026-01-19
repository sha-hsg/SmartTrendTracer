#!/bin/bash

# Start Tweet Collector with optimizations for Twitter Basic Account
# This script sets the appropriate environment variables and launches the collector

echo "=========================================="
echo "Twitter Collector - Configuration"
echo "=========================================="

# Check if bearer token is set
if [ -z "$TWITTER_BEARER_TOKEN" ]; then
    echo "❌ Error: TWITTER_BEARER_TOKEN not set"
    echo "Please run: export TWITTER_BEARER_TOKEN='your_token_here'"
    exit 1
fi

echo "✅ Bearer token found"
echo ""

# Offer choice of mode
echo "Which mode would you like to run?"
echo "1) Basic Account Mode (DEFAULT - $100/month plan)"
echo "2) Pro/Enterprise Mode (Higher limits)"
echo "3) Usage Monitor"
echo ""
read -p "Enter choice (1-3) [Default: 1]: " choice

# Default to option 1 if no input
if [ -z "$choice" ]; then
    choice=1
fi

case $choice in
    1)
        echo "Starting collector in Basic Account Mode (DEFAULT)..."
        echo ""
        echo "Configuration:"
        echo "  • Max pages per account: 1"
        echo "  • Collection interval: 15 minutes"
        echo "  • Request limit: 12 per window"
        echo "  • Monthly limit: 10,000 tweets"
        echo "  • Daily budget: 333 tweets"
        echo "  • Tiered priority: Enabled"
        echo ""
        
        # Basic Account Mode is now default, but we'll ensure it's set
        export BASIC_ACCOUNT_MODE=true
        
        python tweet_collector_service.py
        ;;
    2)
        echo "Starting collector in Pro/Enterprise Mode..."
        echo ""
        echo "Configuration:"
        echo "  • Max pages per account: 5"
        echo "  • Collection interval: 30 minutes"
        echo "  • No usage limits"
        echo "  • Higher rate limits (300 req/15min)"
        echo ""
        
        # Explicitly disable Basic Account Mode
        export BASIC_ACCOUNT_MODE=false
        
        python tweet_collector_service.py
        ;;
    3)
        echo "Starting Usage Monitor..."
        python monitor_usage.py
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac