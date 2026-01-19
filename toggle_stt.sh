#!/bin/bash

# Toggle script for SmartTrendTracer
# Toggles between start and stop with each keypress

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initial state: assume services are stopped
STATE="stopped"

# Function to check if services are actually running
check_actual_state() {
    if [ -f "backend/backend.pid" ] && kill -0 $(cat backend/backend.pid) 2>/dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

# Initialize state based on actual running processes
STATE=$(check_actual_state)

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SmartTrendTracer Toggle Control         ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

if [ "$STATE" = "running" ]; then
    echo -e "${GREEN}Services are currently: RUNNING ✓${NC}"
    echo -e "${YELLOW}Press [ENTER] to STOP, [Q] to quit${NC}"
else
    echo -e "${RED}Services are currently: STOPPED ✗${NC}"
    echo -e "${YELLOW}Press [ENTER] to START, [Q] to quit${NC}"
fi

echo ""

# Main loop
while true; do
    # Read single key
    read -n 1 -s key

    # Check if user pressed Q/q to quit
    if [ "$key" = "q" ] || [ "$key" = "Q" ]; then
        echo ""
        echo -e "${YELLOW}Exiting toggle control...${NC}"
        exit 0
    fi

    # Toggle state
    if [ "$STATE" = "stopped" ]; then
        # Currently stopped, so START
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}▶  STARTING SmartTrendTracer Services...${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        ./start_stt.sh

        STATE="running"
        echo ""
        echo -e "${GREEN}✓ Services are now: RUNNING${NC}"
        echo -e "${YELLOW}Press [ENTER] to STOP, [Q] to quit${NC}"
        echo ""
    else
        # Currently running, so STOP
        echo ""
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}■  STOPPING SmartTrendTracer Services...${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        ./stop_stt.sh

        STATE="stopped"
        echo ""
        echo -e "${RED}✗ Services are now: STOPPED${NC}"
        echo -e "${YELLOW}Press [ENTER] to START, [Q] to quit${NC}"
        echo ""
    fi
done
