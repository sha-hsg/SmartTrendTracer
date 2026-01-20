#!/bin/bash

# SmartTrendTracer - Stop All Services
# This script stops all components of the SmartTrendTracer system
# Cross-platform compatible: macOS and Linux
#
# Usage: ./stop_stt.sh [--mongo-yes|-y|--mongo-no|-n]
#   --mongo-yes, -y   Stop MongoDB without asking
#   --mongo-no, -n    Keep MongoDB running without asking
#   (no parameter)    Interactive - ask about MongoDB

# Parse command line arguments
MONGO_ACTION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --mongo-yes|-y)
            MONGO_ACTION="yes"
            shift
            ;;
        --mongo-no|-n)
            MONGO_ACTION="no"
            shift
            ;;
        -h|--help)
            echo "Usage: ./stop_stt.sh [--mongo-yes|-y|--mongo-no|-n]"
            echo "  --mongo-yes, -y   Stop MongoDB without asking"
            echo "  --mongo-no, -n    Keep MongoDB running without asking"
            echo "  (no parameter)    Interactive - ask about MongoDB"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "Stopping SmartTrendTracer Services"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Detect platform
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
    else
        PLATFORM="unknown"
    fi
    echo "Platform detected: $PLATFORM"
}

detect_platform

# Function to stop a service by PID file
stop_service_by_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -n "Stopping $service_name (PID: $pid)..."
            kill $pid 2>/dev/null
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                echo -e " ${YELLOW}Force killing...${NC}"
                kill -9 $pid 2>/dev/null
            fi
            echo -e " ${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}$service_name not running (stale PID file)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}$service_name PID file not found${NC}"
    fi
}

# Function to stop a service by process name
stop_service_by_name() {
    local process_name=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$process_name")
    if [ -n "$pids" ]; then
        echo -n "Stopping $service_name..."
        for pid in $pids; do
            kill $pid 2>/dev/null
        done
        sleep 2
        # Check if any processes are still running
        local remaining=$(pgrep -f "$process_name")
        if [ -n "$remaining" ]; then
            echo -e " ${YELLOW}Force killing...${NC}"
            for pid in $remaining; do
                kill -9 $pid 2>/dev/null
            done
        fi
        echo -e " ${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}$service_name not running${NC}"
    fi
}

# Function to stop a service by port
stop_service_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port)
    if [ -n "$pids" ]; then
        echo -n "Stopping $service_name on port $port..."
        for pid in $pids; do
            kill $pid 2>/dev/null
        done
        sleep 2
        # Check if port is still in use
        local remaining=$(lsof -ti:$port)
        if [ -n "$remaining" ]; then
            echo -e " ${YELLOW}Force killing...${NC}"
            for pid in $remaining; do
                kill -9 $pid 2>/dev/null
            done
        fi
        echo -e " ${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}$service_name not running on port $port${NC}"
    fi
}

# Stop Frontend Development Server
echo "1. Stopping Frontend Development Server..."
if [ -f "pids/frontend.pid" ]; then
    stop_service_by_pid "pids/frontend.pid" "Frontend"
else
    stop_service_by_port 3470 "Frontend"
fi

# Stop Reddit Collector Service
echo ""
echo "2. Stopping Reddit Collector Service..."
if [ -f "pids/reddit_collector.pid" ]; then
    stop_service_by_pid "pids/reddit_collector.pid" "Reddit Collector"
else
    stop_service_by_name "reddit_collector.py" "Reddit Collector"
fi

# Stop Tweet Collector Service
echo ""
echo "3. Stopping Tweet Collector Service..."
if [ -f "pids/tweet_collector.pid" ]; then
    stop_service_by_pid "pids/tweet_collector.pid" "Tweet Collector"
else
    stop_service_by_name "tweet_collector_service.py" "Tweet Collector"
fi

# Stop Marker Service
echo ""
echo "4. Stopping Marker Service..."
if [ -f "pids/marker.pid" ]; then
    stop_service_by_pid "pids/marker.pid" "Marker Service"
else
    stop_service_by_port 8002 "Marker Service"
fi

# Stop MinerU Service
echo ""
echo "5. Stopping MinerU Service..."
if [ -f "pids/mineru.pid" ]; then
    stop_service_by_pid "pids/mineru.pid" "MinerU Service"
else
    stop_service_by_port 8003 "MinerU Service"
fi

# Stop Backend API Server
echo ""
echo "6. Stopping Backend API Server..."
if [ -f "pids/backend.pid" ]; then
    stop_service_by_pid "pids/backend.pid" "Backend API"
else
    stop_service_by_port 8000 "Backend API"
fi

# Handle MongoDB
echo ""
echo -e "${YELLOW}7. MongoDB Management${NC}"

# Determine MongoDB action based on parameter or interactive prompt
STOP_MONGO=false
if [ "$MONGO_ACTION" = "yes" ]; then
    echo "Stopping MongoDB (--mongo-yes specified)..."
    STOP_MONGO=true
elif [ "$MONGO_ACTION" = "no" ]; then
    echo "Keeping MongoDB running (--mongo-no specified)..."
    STOP_MONGO=false
else
    # Interactive mode
    read -p "Do you want to stop MongoDB? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        STOP_MONGO=true
    fi
fi

if [ "$STOP_MONGO" = true ]; then
    echo "Stopping MongoDB..."

    # Platform-specific MongoDB stop
    case "$PLATFORM" in
        macos)
            echo "Using brew services (macOS)..."
            brew services stop mongodb-community 2>/dev/null
            ;;
        linux)
            echo "Using systemctl (Linux)..."
            # Try systemctl first (systemd)
            if command -v systemctl &> /dev/null; then
                sudo systemctl stop mongod 2>/dev/null || \
                systemctl --user stop mongod 2>/dev/null || \
                echo "systemctl failed, trying direct kill..."
            fi
            # Fallback: kill mongod directly
            if pgrep -x "mongod" > /dev/null; then
                echo "Killing mongod process directly..."
                pkill -x mongod 2>/dev/null
            fi
            ;;
        *)
            echo "Unknown platform, trying generic stop..."
            pkill -x mongod 2>/dev/null
            ;;
    esac

    sleep 2
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${RED}✗ MongoDB still running (may need manual stop)${NC}"
        case "$PLATFORM" in
            macos)
                echo "   Try: brew services stop mongodb-community"
                ;;
            linux)
                echo "   Try: sudo systemctl stop mongod"
                ;;
        esac
    else
        echo -e "${GREEN}✓ MongoDB stopped${NC}"
    fi
else
    echo -e "${YELLOW}MongoDB left running (needed for data persistence)${NC}"
fi

# Clean up any orphaned processes
echo ""
echo "8. Cleaning up orphaned processes..."

# Kill Playwright browser processes
playwright_pids=$(pgrep -f "chromium.*playwright" 2>/dev/null)
if [ -n "$playwright_pids" ]; then
    echo -n "Found Playwright browser processes, cleaning up..."
    pkill -f "chromium.*playwright" 2>/dev/null
    pkill -f "Chromium" 2>/dev/null
    sleep 1
    echo -e " ${GREEN}✓${NC}"
fi

# Check for any uvicorn processes
uvicorn_pids=$(pgrep -f "uvicorn")
if [ -n "$uvicorn_pids" ]; then
    echo -n "Found orphaned uvicorn processes, cleaning up..."
    for pid in $uvicorn_pids; do
        kill $pid 2>/dev/null
    done
    sleep 1
    echo -e " ${GREEN}✓${NC}"
fi

# Check for any npm/node processes related to our frontend
node_pids=$(pgrep -f "vite.*3470")
if [ -n "$node_pids" ]; then
    echo -n "Found orphaned frontend processes, cleaning up..."
    for pid in $node_pids; do
        kill $pid 2>/dev/null
    done
    sleep 1
    echo -e " ${GREEN}✓${NC}"
fi

# Clean up PID files
echo ""
echo "9. Cleaning up PID files..."
if [ -d "pids" ]; then
    rm -f pids/*.pid
    echo -e "${GREEN}✓ PID files cleaned${NC}"
fi

# Summary
echo ""
echo "========================================="
echo -e "${GREEN}SmartTrendTracer Services Status:${NC}"
echo "========================================="

# Check services
check_status() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "$service: ${RED}✗ Still running${NC}"
        return 1
    else
        echo -e "$service: ${GREEN}✓ Stopped${NC}"
        return 0
    fi
}

all_stopped=true

check_status 8000 "Backend API      " || all_stopped=false
check_status 8002 "Marker Service   " || all_stopped=false
check_status 8003 "MinerU Service   " || all_stopped=false
check_status 3470 "Frontend         " || all_stopped=false

# Check collectors
if pgrep -f "tweet_collector_service.py" > /dev/null; then
    echo -e "Tweet Collector:  ${RED}✗ Still running${NC}"
    all_stopped=false
else
    echo -e "Tweet Collector:  ${GREEN}✓ Stopped${NC}"
fi

if pgrep -f "reddit_collector.py" > /dev/null; then
    echo -e "Reddit Collector: ${RED}✗ Still running${NC}"
    all_stopped=false
else
    echo -e "Reddit Collector: ${GREEN}✓ Stopped${NC}"
fi

if pgrep -x "mongod" > /dev/null; then
    echo -e "MongoDB:          ${YELLOW}⚠ Running (as requested)${NC}"
else
    echo -e "MongoDB:          ${GREEN}✓ Stopped${NC}"
fi

echo "========================================="

if [ "$all_stopped" = true ]; then
    echo -e "${GREEN}All services stopped successfully!${NC}"
else
    echo -e "${YELLOW}Some services may still be running.${NC}"
    echo "You can force stop them manually if needed."
fi

echo ""
echo "To start all services again, run: ./start_stt.sh"