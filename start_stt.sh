#!/bin/bash

# SmartTrendTracer - Start All Services
# This script starts all components of the SmartTrendTracer system

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate mise if available (for managing Python versions)
if command -v mise &> /dev/null; then
    eval "$(mise activate bash 2>/dev/null)"
fi

# Load API keys from ~/.env (contains OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
if [ -f "$HOME/.env" ]; then
    set -a  # automatically export all variables
    source "$HOME/.env"
    set +a
fi

# Create necessary directories if they don't exist
mkdir -p logs pids

# Create timestamped log file for this startup (absolute path)
STARTUP_LOG="$SCRIPT_DIR/logs/startup_$(date +%Y%m%d_%H%M%S).log"
echo "Startup log: $STARTUP_LOG"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$STARTUP_LOG"
}

# Function to log without timestamp (for formatted output)
log_plain() {
    echo "$*" | tee -a "$STARTUP_LOG"
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect platform
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
    else
        PLATFORM="unknown"
    fi
    log "   Platform detected: $PLATFORM ($OSTYPE)"
}

# Function to check if a venv is valid (has python binary)
check_venv_valid() {
    local venv_path=$1
    if [ -d "$venv_path" ] && [ -x "$venv_path/bin/python" ]; then
        return 0
    fi
    return 1
}

# Function to create and setup venv
create_venv() {
    local venv_path=$1
    local requirements_file=$2
    local log_file=$3

    log "   Creating virtual environment at $venv_path..."

    # Remove existing broken venv if present
    if [ -d "$venv_path" ]; then
        log "   Removing incomplete venv directory..."
        rm -rf "$venv_path"
    fi

    # Create new venv
    python3 -m venv "$venv_path" >> "$log_file" 2>&1

    if [ ! -x "$venv_path/bin/python" ]; then
        log "   ✗ Failed to create virtual environment"
        return 1
    fi

    # Upgrade pip
    "$venv_path/bin/python" -m pip install --upgrade pip >> "$log_file" 2>&1

    # Install requirements if provided
    if [ -n "$requirements_file" ] && [ -f "$requirements_file" ]; then
        log "   Installing requirements from $requirements_file..."
        "$venv_path/bin/python" -m pip install -r "$requirements_file" >> "$log_file" 2>&1
    fi

    log "   ✓ Virtual environment created successfully"
    return 0
}

# Function to start MongoDB based on platform
start_mongodb() {
    if pgrep -x "mongod" > /dev/null; then
        return 0  # Already running
    fi

    log "   MongoDB is not running, attempting to start..."

    case "$PLATFORM" in
        macos)
            log "   Using brew services (macOS)..."
            brew services start mongodb-community >> "$STARTUP_LOG" 2>&1
            ;;
        linux)
            log "   Using systemctl (Linux)..."
            # Try systemctl first (systemd)
            if command -v systemctl &> /dev/null; then
                sudo systemctl start mongod >> "$STARTUP_LOG" 2>&1 || \
                systemctl --user start mongod >> "$STARTUP_LOG" 2>&1 || \
                log "   ⚠️  systemctl failed, trying direct start..."
            fi
            # Fallback: try starting mongod directly
            if ! pgrep -x "mongod" > /dev/null; then
                log "   Trying direct mongod start..."
                mongod --dbpath /var/lib/mongodb --fork --logpath /var/log/mongodb/mongod.log >> "$STARTUP_LOG" 2>&1 || \
                mongod --dbpath ~/.mongodb/data --fork --logpath ~/.mongodb/mongod.log >> "$STARTUP_LOG" 2>&1
            fi
            ;;
        *)
            log "   ⚠️  Unknown platform, trying generic mongod start..."
            mongod --fork --logpath /tmp/mongod.log >> "$STARTUP_LOG" 2>&1
            ;;
    esac

    sleep 2

    if pgrep -x "mongod" > /dev/null; then
        MONGO_PID=$(pgrep -x "mongod")
        log_plain "   ✓ MongoDB started (PID: $MONGO_PID)"
        return 0
    else
        log_plain "   ✗ Failed to start MongoDB"
        case "$PLATFORM" in
            macos)
                log "   Please start MongoDB manually: brew services start mongodb-community"
                ;;
            linux)
                log "   Please start MongoDB manually: sudo systemctl start mongod"
                ;;
        esac
        return 1
    fi
}

log_plain "========================================="
log "Starting SmartTrendTracer Services"
log_plain "========================================="
log "Script directory: $SCRIPT_DIR"

# Detect platform first
detect_platform
log_plain ""

# Function to check if a service is running
check_service() {
    local port=$1
    local service_name=$2
    log "   Checking if port $port is available..."
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        log_plain "   ⚠️  $service_name is already running on port $port (PID: $pid)"
        echo -e "${YELLOW}⚠️  $service_name is already running on port $port${NC}"
        return 1
    fi
    log "   ✓ Port $port is available"
    return 0
}

# Function to wait for service to start
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=${3:-30}  # Default 30s, can be overridden
    local attempt=0
    local start_time=$(date +%s)

    echo -n "Waiting for $service_name to start" | tee -a "$STARTUP_LOG"
    while [ $attempt -lt $max_attempts ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            echo -e " ${GREEN}✓${NC} (${duration}s)" | tee -a "$STARTUP_LOG"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}✗ (timeout after ${max_attempts}s)${NC}" | tee -a "$STARTUP_LOG"
    return 1
}

# Check MongoDB
log "1. Checking MongoDB..."
log "   Searching for mongod process..."
if pgrep -x "mongod" > /dev/null; then
    MONGO_PID=$(pgrep -x "mongod")
    log_plain "   ✓ MongoDB is running (PID: $MONGO_PID)"

    # Try to get MongoDB version and status
    if command -v mongosh &> /dev/null; then
        MONGO_VERSION=$(mongosh --quiet --eval "db.version()" 2>/dev/null || echo "unknown")
        log "   MongoDB version: $MONGO_VERSION"

        # Get database stats
        DOC_COUNT=$(mongosh smarttrendtracer --quiet --eval "print(Number(db.stats().objects))" 2>/dev/null || echo "0")
        DB_SIZE=$(mongosh smarttrendtracer --quiet --eval "print(Math.round(db.stats().dataSize / 1024 / 1024))" 2>/dev/null || echo "0")
        log "   Database: smarttrendtracer ($DOC_COUNT documents, ${DB_SIZE}MB)"
    fi
else
    # Use platform-specific MongoDB start
    if ! start_mongodb; then
        exit 1
    fi
fi

# Start Backend API Server
log_plain ""
log "2. Starting Backend API Server (port 8000)..."
if check_service 8000 "Backend API"; then
    log "   Port 8000 available, starting backend..."
    BACKEND_DIR="$SCRIPT_DIR/backend"
    cd "$BACKEND_DIR"

    # Check for virtual environment (validate python binary exists, not just directory)
    log "   Checking for Python virtual environment..."
    if check_venv_valid "venv"; then
        PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
        log "   Using existing venv..."
        PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
        log "   Python: $PYTHON_VERSION"
    elif check_venv_valid "$SCRIPT_DIR/venv"; then
        PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
        log "   Using parent venv..."
        PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
        log "   Python: $PYTHON_VERSION"
    else
        # Create new venv with requirements
        if create_venv "venv" "requirements.txt" "$STARTUP_LOG"; then
            PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
            PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
            log "   Python: $PYTHON_VERSION"
        else
            log "   ✗ Failed to create virtual environment. Please check Python installation."
            exit 1
        fi
    fi

    # Start the backend server in the background with explicit venv path
    log "   Starting uvicorn server (reload mode)..."
    nohup $PYTHON_BIN -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$SCRIPT_DIR/pids/backend.pid"
    log "   Backend process started with PID: $BACKEND_PID"
    log "   Using Python: $PYTHON_BIN"

    # Backend needs longer timeout due to MongoDB index creation (44s typical)
    wait_for_service 8000 "Backend API" 60
    cd "$SCRIPT_DIR"
else
    log "   Skipping backend start (already running)"
    if [ -f "pids/backend.pid" ]; then
        SAVED_PID=$(cat pids/backend.pid)
        log "   Saved PID file: $SAVED_PID"
    fi
fi

# Start Marker Service (different environment)
log_plain ""
log "3. Starting Marker Service (port 8002)..."
if check_service 8002 "Marker Service"; then
    log "   Port 8002 available, starting Marker service..."
    MARKER_DIR="$SCRIPT_DIR/backend/marker_service"
    cd "$MARKER_DIR"

    # Check if marker_env is valid (has python binary)
    log "   Checking for Marker virtual environment..."
    if check_venv_valid "marker_env"; then
        MARKER_PYTHON="$MARKER_DIR/marker_env/bin/python"
        log "   Using existing marker_env..."
    else
        log "   Creating virtual environment for Marker service..."
        # Remove broken venv if exists
        [ -d "marker_env" ] && rm -rf "marker_env"
        python3 -m venv marker_env >> "$STARTUP_LOG" 2>&1
        MARKER_PYTHON="$MARKER_DIR/marker_env/bin/python"
        if [ ! -x "$MARKER_PYTHON" ]; then
            log "   ✗ Failed to create Marker virtual environment"
            # Continue without Marker - it's optional
        else
            log "   Installing Marker dependencies (marker-pdf, fastapi, uvicorn)..."
            $MARKER_PYTHON -m pip install --upgrade pip >> "$STARTUP_LOG" 2>&1
            $MARKER_PYTHON -m pip install marker-pdf fastapi uvicorn python-multipart >> "$STARTUP_LOG" 2>&1
        fi
    fi

    # Start the marker server in the background with explicit venv path
    log "   Starting Marker uvicorn server (1 worker, 120s keepalive)..."
    nohup $MARKER_PYTHON -m uvicorn marker_server:app --host 0.0.0.0 --port 8002 --workers 1 --timeout-keep-alive 120 > "$SCRIPT_DIR/logs/marker.log" 2>&1 &
    MARKER_PID=$!
    echo $MARKER_PID > "$SCRIPT_DIR/pids/marker.pid"
    log "   Marker process started with PID: $MARKER_PID"
    log "   Using Python: $MARKER_PYTHON"

    wait_for_service 8002 "Marker Service"
    cd "$SCRIPT_DIR"
else
    log "   Skipping Marker service start (already running)"
    if [ -f "pids/marker.pid" ]; then
        SAVED_PID=$(cat pids/marker.pid)
        log "   Saved PID file: $SAVED_PID"
    fi
fi

# Start MinerU Service (different environment)
log_plain ""
log "4. Starting MinerU Service (port 8003)..."
if check_service 8003 "MinerU Service"; then
    log "   Port 8003 available, starting MinerU service..."
    MINERU_DIR="$SCRIPT_DIR/backend/mineru_service"
    cd "$MINERU_DIR"

    # Check if mineru_env is valid (has python binary)
    log "   Checking for MinerU virtual environment..."
    if check_venv_valid "mineru_env"; then
        MINERU_PYTHON="$MINERU_DIR/mineru_env/bin/python"
        log "   Using existing mineru_env..."
    else
        log "   Creating virtual environment for MinerU service..."
        # Remove broken venv if exists
        [ -d "mineru_env" ] && rm -rf "mineru_env"
        python3 -m venv mineru_env >> "$STARTUP_LOG" 2>&1
        MINERU_PYTHON="$MINERU_DIR/mineru_env/bin/python"
        if [ ! -x "$MINERU_PYTHON" ]; then
            log "   ✗ Failed to create MinerU virtual environment"
            # Continue without MinerU - it's optional
        else
            log "   Installing MinerU dependencies (mineru, fastapi, uvicorn)..."
            $MINERU_PYTHON -m pip install --upgrade pip >> "$STARTUP_LOG" 2>&1
            $MINERU_PYTHON -m pip install mineru fastapi uvicorn python-multipart aiofiles >> "$STARTUP_LOG" 2>&1
        fi
    fi

    # Start the MinerU server in the background with explicit venv path
    log "   Starting MinerU server..."
    nohup $MINERU_PYTHON mineru_server.py > "$SCRIPT_DIR/logs/mineru.log" 2>&1 &
    MINERU_PID=$!
    echo $MINERU_PID > "$SCRIPT_DIR/pids/mineru.pid"
    log "   MinerU process started with PID: $MINERU_PID"
    log "   Using Python: $MINERU_PYTHON"

    wait_for_service 8003 "MinerU Service"
    cd "$SCRIPT_DIR"
else
    log "   Skipping MinerU service start (already running)"
    if [ -f "pids/mineru.pid" ]; then
        SAVED_PID=$(cat pids/mineru.pid)
        log "   Saved PID file: $SAVED_PID"
    fi
fi

# Start Tweet Collector Service
log_plain ""
log "5. Starting Tweet Collector Service..."
cd "$BACKEND_DIR"

# Check if tweet collector is already running
log "   Checking for tweet_collector_service.py process..."
if pgrep -f "tweet_collector_service.py" > /dev/null; then
    COLLECTOR_PID=$(pgrep -f "tweet_collector_service.py")
    log_plain "   ⚠️  Tweet Collector is already running (PID: $COLLECTOR_PID)"
else
    log "   Tweet Collector not running, starting..."
    # Use backend environment with explicit path (validate python binary exists)
    log "   Checking for Python virtual environment..."
    if check_venv_valid "venv"; then
        COLLECTOR_PYTHON="$BACKEND_DIR/venv/bin/python"
        log "   Using backend venv..."
    elif check_venv_valid "$SCRIPT_DIR/venv"; then
        COLLECTOR_PYTHON="$SCRIPT_DIR/venv/bin/python"
        log "   Using parent venv..."
    else
        COLLECTOR_PYTHON="python3"
        log "   No valid venv found, using system Python"
    fi

    # Start the tweet collector in the background with explicit venv path
    log "   Starting tweet collector service (background process)..."
    nohup $COLLECTOR_PYTHON tweet_collector_service.py > "$SCRIPT_DIR/logs/tweet_collector.log" 2>&1 &
    COLLECTOR_PID=$!
    echo $COLLECTOR_PID > "$SCRIPT_DIR/pids/tweet_collector.pid"
    log "   Tweet Collector process started with PID: $COLLECTOR_PID"
    log "   Using Python: $COLLECTOR_PYTHON"

    sleep 2
    if pgrep -f "tweet_collector_service.py" > /dev/null; then
        log_plain "   ✓ Tweet Collector started successfully"
    else
        log_plain "   ✗ Failed to start Tweet Collector (check logs/tweet_collector.log)"
    fi
fi
cd "$SCRIPT_DIR"

# Start Reddit Collector Service (optional)
log_plain ""
log "6. Starting Reddit Collector Service (optional)..."
log "   Checking for Reddit API credentials..."
if [ -n "$REDDIT_CLIENT_ID" ] && [ -n "$REDDIT_CLIENT_SECRET" ]; then
    log "   ✓ Reddit credentials found in environment"
    cd "$BACKEND_DIR"
    log "   Checking for reddit_collector.py process..."
    if pgrep -f "reddit_collector.py" > /dev/null; then
        REDDIT_PID=$(pgrep -f "reddit_collector.py")
        log_plain "   ⚠️  Reddit Collector is already running (PID: $REDDIT_PID)"
    else
        log "   Reddit Collector not running, starting..."
        # Use backend environment with explicit path (validate python binary exists)
        log "   Checking for Python virtual environment..."
        if check_venv_valid "venv"; then
            REDDIT_PYTHON="$BACKEND_DIR/venv/bin/python"
            log "   Using backend venv..."
        elif check_venv_valid "$SCRIPT_DIR/venv"; then
            REDDIT_PYTHON="$SCRIPT_DIR/venv/bin/python"
            log "   Using parent venv..."
        else
            REDDIT_PYTHON="python3"
            log "   No valid venv found, using system Python"
        fi

        # Start the reddit collector in the background with explicit venv path
        log "   Starting reddit collector service (background process)..."
        nohup $REDDIT_PYTHON -m app.collectors.reddit_collector > "$SCRIPT_DIR/logs/reddit_collector.log" 2>&1 &
        REDDIT_PID=$!
        echo $REDDIT_PID > "$SCRIPT_DIR/pids/reddit_collector.pid"
        log "   Reddit Collector process started with PID: $REDDIT_PID"
        log "   Using Python: $REDDIT_PYTHON"

        sleep 2
        if pgrep -f "reddit_collector.py" > /dev/null; then
            log_plain "   ✓ Reddit Collector started successfully"
        else
            log_plain "   ⚠️  Reddit Collector not started (check logs/reddit_collector.log)"
        fi
    fi
    cd "$SCRIPT_DIR"
else
    log_plain "   ✗ Skipping Reddit Collector (no credentials found)"
    log "   Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in environment to enable"
fi

# Start Frontend Development Server
log_plain ""
log "7. Starting Frontend Development Server (port 3470)..."
if check_service 3470 "Frontend"; then
    log "   Port 3470 available, starting frontend..."
    FRONTEND_DIR="$SCRIPT_DIR/frontend"
    cd "$FRONTEND_DIR"

    # Check if node_modules exists
    log "   Checking for node_modules directory..."
    if [ ! -d "node_modules" ]; then
        log "   node_modules not found, installing frontend dependencies..."
        log "   This may take a few minutes..."
        npm install >> "$STARTUP_LOG" 2>&1
        log "   ✓ Frontend dependencies installed"
    else
        log "   ✓ node_modules found"
        # Check package.json modification time
        if command -v stat &> /dev/null; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                PKG_TIME=$(stat -f %m package.json 2>/dev/null || echo "0")
                NODE_TIME=$(stat -f %m node_modules 2>/dev/null || echo "0")
            else
                PKG_TIME=$(stat -c %Y package.json 2>/dev/null || echo "0")
                NODE_TIME=$(stat -c %Y node_modules 2>/dev/null || echo "0")
            fi
            if [ "$PKG_TIME" -gt "$NODE_TIME" ]; then
                log "   ⚠️  package.json is newer than node_modules, consider running npm install"
            fi
        fi
    fi

    # Start the frontend server in the background
    log "   Starting Vite dev server..."
    nohup npm run dev > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$SCRIPT_DIR/pids/frontend.pid"
    log "   Frontend process started with PID: $FRONTEND_PID"

    wait_for_service 3470 "Frontend"
    cd "$SCRIPT_DIR"
else
    log "   Skipping frontend start (already running)"
    if [ -f "pids/frontend.pid" ]; then
        SAVED_PID=$(cat pids/frontend.pid)
        log "   Saved PID file: $SAVED_PID"
    fi
fi

# Calculate total startup time
SCRIPT_END=$(date +%s)
# Platform-specific file modification time
if [[ "$PLATFORM" == "macos" ]]; then
    SCRIPT_START=$(date -r "$STARTUP_LOG" +%s 2>/dev/null || echo $SCRIPT_END)
else
    SCRIPT_START=$(stat -c %Y "$STARTUP_LOG" 2>/dev/null || echo $SCRIPT_END)
fi
TOTAL_TIME=$((SCRIPT_END - SCRIPT_START))

# Collect all PIDs for summary
log_plain ""
log_plain "========================================="
log "SmartTrendTracer Services Status"
log_plain "========================================="

# MongoDB
if pgrep -x "mongod" > /dev/null; then
    MONGO_PID=$(pgrep -x "mongod")
    log_plain "MongoDB:          ✓ Running (PID: $MONGO_PID)"
else
    log_plain "MongoDB:          ✗ Not running"
fi

# Backend API
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    BACKEND_PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    log_plain "Backend API:      ✓ http://localhost:8000 (PID: $BACKEND_PID)"
else
    log_plain "Backend API:      ✗ Not running"
fi

# Marker Service
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
    MARKER_PID=$(lsof -Pi :8002 -sTCP:LISTEN -t)
    log_plain "Marker Service:   ✓ http://localhost:8002 (PID: $MARKER_PID)"
else
    log_plain "Marker Service:   ✗ Not running"
fi

# MinerU Service
if lsof -Pi :8003 -sTCP:LISTEN -t >/dev/null 2>&1; then
    MINERU_PID=$(lsof -Pi :8003 -sTCP:LISTEN -t)
    log_plain "MinerU Service:   ✓ http://localhost:8003 (PID: $MINERU_PID)"
else
    log_plain "MinerU Service:   ✗ Not running"
fi

# Tweet Collector
if pgrep -f "tweet_collector_service.py" > /dev/null; then
    TWEET_PID=$(pgrep -f "tweet_collector_service.py")
    log_plain "Tweet Collector:  ✓ Running in background (PID: $TWEET_PID)"
else
    log_plain "Tweet Collector:  ✗ Not running"
fi

# Reddit Collector
if pgrep -f "reddit_collector.py" > /dev/null; then
    REDDIT_PID=$(pgrep -f "reddit_collector.py")
    log_plain "Reddit Collector: ✓ Running in background (PID: $REDDIT_PID)"
elif [ -n "$REDDIT_CLIENT_ID" ]; then
    log_plain "Reddit Collector: ✗ Not running (credentials found but not started)"
else
    log_plain "Reddit Collector: - Skipped (no credentials)"
fi

# Frontend
if lsof -Pi :3470 -sTCP:LISTEN -t >/dev/null 2>&1; then
    FRONTEND_PID=$(lsof -Pi :3470 -sTCP:LISTEN -t)
    log_plain "Frontend:         ✓ http://localhost:3470 (PID: $FRONTEND_PID)"
else
    log_plain "Frontend:         ✗ Not running"
fi

log_plain "========================================="
log "Total startup time: ${TOTAL_TIME}s"
log_plain ""
log "Service Logs:"
log "  Backend:         logs/backend.log"
log "  Marker:          logs/marker.log"
log "  MinerU:          logs/mineru.log"
log "  Tweet Collector: logs/tweet_collector.log"
log "  Reddit Collector: logs/reddit_collector.log"
log "  Frontend:        logs/frontend.log"
log_plain ""
log "To stop all services, run: ./stop_stt.sh"
log "To view logs, check the logs/ directory"
log "Startup log saved to: $STARTUP_LOG"
log_plain ""
log "All services started successfully!"