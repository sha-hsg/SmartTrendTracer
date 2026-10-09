#!/bin/bash
# ============================================================================
# SmartTrendTracer Setup Script
# ============================================================================
# Automatically detects platform (macOS/Linux) and sets up the environment
#
# Usage:
#   ./scripts/setup.sh           # Full setup
#   ./scripts/setup.sh --check   # Only check dependencies
#   ./scripts/setup.sh --venv    # Only setup virtual environments
#   ./scripts/setup.sh --mongodb # Only setup MongoDB
#   ./scripts/setup.sh --frontend # Only setup frontend
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ============================================================================
# Platform Detection
# ============================================================================
detect_platform() {
    case "$(uname -s)" in
        Darwin*)  echo "macos" ;;
        Linux*)   echo "linux" ;;
        *)        echo "unknown" ;;
    esac
}

detect_linux_distro() {
    if [ -f /etc/arch-release ]; then
        echo "arch"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/fedora-release ]; then
        echo "fedora"
    else
        echo "unknown"
    fi
}

PLATFORM=$(detect_platform)
if [ "$PLATFORM" = "linux" ]; then
    LINUX_DISTRO=$(detect_linux_distro)
fi

# ============================================================================
# Helper Functions
# ============================================================================
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}  ✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}  ℹ $1${NC}"
}

check_command() {
    command -v "$1" &> /dev/null
}

is_running() {
    pgrep -x "$1" > /dev/null 2>&1
}

# ============================================================================
# Dependency Checks
# ============================================================================
check_dependencies() {
    print_header "🔍 Checking Dependencies"

    local all_ok=true

    # Python
    print_step "Python 3.10+"
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            print_success "Python $PYTHON_VERSION installed"
        else
            print_error "Python $PYTHON_VERSION (3.10+ required)"
            all_ok=false
        fi
    else
        print_error "Python 3 not found"
        all_ok=false
    fi

    # mise (optional)
    print_step "mise (optional)"
    if check_command mise; then
        print_success "mise $(mise --version) installed"
    else
        print_info "mise not installed (optional for Python version management)"
    fi

    # Node.js
    print_step "Node.js 18+"
    if check_command node; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'.' -f1)
        if [ "$NODE_MAJOR" -ge 18 ]; then
            print_success "Node.js $NODE_VERSION installed"
        else
            print_warning "Node.js $NODE_VERSION (18+ recommended)"
        fi
    else
        print_error "Node.js not found"
        all_ok=false
    fi

    # MongoDB
    print_step "MongoDB"
    if check_command mongod; then
        MONGO_VERSION=$(mongod --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        print_success "MongoDB $MONGO_VERSION installed"
    else
        print_error "MongoDB not found"
        all_ok=false
    fi

    # MongoDB Tools
    print_step "MongoDB Tools (mongodump/mongorestore)"
    if check_command mongodump && check_command mongorestore; then
        print_success "MongoDB tools installed"
    else
        print_error "MongoDB tools not found"
        all_ok=false
    fi

    # Git
    print_step "Git"
    if check_command git; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_success "Git $GIT_VERSION installed"
    else
        print_warning "Git not found (optional)"
    fi

    # Syncthing (optional)
    print_step "Syncthing (optional)"
    if check_command syncthing; then
        print_success "Syncthing installed"
        if is_running syncthing; then
            print_info "Syncthing is running"
        else
            print_info "Syncthing not running"
        fi
    else
        print_info "Syncthing not installed (optional for cross-machine sync)"
    fi

    echo ""
    if [ "$all_ok" = true ]; then
        print_success "All required dependencies are installed"
        return 0
    else
        print_error "Some dependencies are missing"
        return 1
    fi
}

# ============================================================================
# Virtual Environment Setup
# ============================================================================
check_venv_valid() {
    local venv_path=$1
    if [ -d "$venv_path" ] && [ -x "$venv_path/bin/python" ]; then
        # Try to run python to verify it's not a broken symlink
        "$venv_path/bin/python" --version &>/dev/null
        return $?
    fi
    return 1
}

setup_venv() {
    print_header "🐍 Setting Up Python Virtual Environments"

    cd "$PROJECT_ROOT"

    # Backend venv
    print_step "Backend venv"
    if check_venv_valid "backend/venv"; then
        print_success "Backend venv is valid"
    else
        print_warning "Backend venv invalid or missing, creating..."
        rm -rf backend/venv
        python3 -m venv backend/venv
        backend/venv/bin/pip install --upgrade pip -q
        print_info "Installing requirements..."
        backend/venv/bin/pip install -r backend/requirements.txt -q
        print_success "Backend venv created"
    fi

    # Marker service venv
    print_step "Marker service venv"
    local marker_venv="backend/marker_service/marker_env"
    if check_venv_valid "$marker_venv"; then
        print_success "Marker venv is valid"
        # Ensure psutil is installed (required for marker_server.py)
        if ! "$marker_venv/bin/pip" show psutil &>/dev/null; then
            print_info "Installing psutil in marker_env..."
            "$marker_venv/bin/pip" install psutil -q
            print_success "psutil installed"
        fi
    else
        print_warning "Marker venv invalid or missing"
        print_info "Run: cd backend/marker_service && python3 -m venv marker_env"
    fi

    # MinerU service venv
    print_step "MinerU service venv"
    local mineru_venv="backend/mineru_service/mineru_env"
    if check_venv_valid "$mineru_venv"; then
        print_success "MinerU venv is valid"
    else
        print_warning "MinerU venv invalid or missing"
        print_info "Run: cd backend/mineru_service && python3 -m venv mineru_env"
    fi

    cd "$PROJECT_ROOT"
}

# ============================================================================
# Frontend Setup
# ============================================================================
setup_frontend() {
    print_header "🌐 Setting Up Frontend"

    cd "$PROJECT_ROOT/frontend"

    # Check if node_modules needs reinstall (wrong platform)
    local needs_install=false

    if [ ! -d "node_modules" ]; then
        needs_install=true
        print_warning "node_modules not found"
    else
        # Check for platform-specific modules
        if [[ "$PLATFORM" == "linux" ]]; then
            if [ ! -d "node_modules/@rollup/rollup-linux-x64-gnu" ]; then
                needs_install=true
                print_warning "node_modules has macOS binaries, needs reinstall"
            fi
        elif [[ "$PLATFORM" == "macos" ]]; then
            if [ ! -d "node_modules/@rollup/rollup-darwin-x64" ] && \
               [ ! -d "node_modules/@rollup/rollup-darwin-arm64" ]; then
                needs_install=true
                print_warning "node_modules has Linux binaries, needs reinstall"
            fi
        fi
    fi

    if [ "$needs_install" = true ]; then
        print_step "Installing frontend dependencies..."
        rm -rf node_modules package-lock.json 2>/dev/null || true
        npm install
        print_success "Frontend dependencies installed"
    else
        print_success "Frontend dependencies OK"
    fi

    cd "$PROJECT_ROOT"
}

# ============================================================================
# MongoDB Setup
# ============================================================================
setup_mongodb() {
    print_header "🗄️ Setting Up MongoDB"

    print_step "Checking MongoDB service..."

    if [[ "$PLATFORM" == "macos" ]]; then
        # macOS with Homebrew
        if brew services list 2>/dev/null | grep -q "mongodb-community.*started"; then
            print_success "MongoDB is already running"
        else
            print_step "Starting MongoDB..."
            brew services start mongodb-community
            sleep 2
            print_success "MongoDB started"
        fi
    else
        # Linux with systemd
        if systemctl is-active --quiet mongod 2>/dev/null; then
            print_success "MongoDB is already running"
        elif systemctl is-active --quiet mongodb 2>/dev/null; then
            print_success "MongoDB is already running"
        else
            print_step "Starting MongoDB..."
            sudo systemctl start mongod 2>/dev/null || sudo systemctl start mongodb 2>/dev/null
            sleep 2
            print_success "MongoDB started"
        fi
    fi

    # Test connection
    print_step "Testing MongoDB connection..."
    if mongosh --eval "db.adminCommand('ping')" --quiet &>/dev/null; then
        print_success "MongoDB connection successful"
    else
        print_error "Could not connect to MongoDB"
        return 1
    fi
}

# ============================================================================
# API Keys Check
# ============================================================================
check_api_keys() {
    print_header "🔑 Checking API Keys (~/.env)"

    if [ ! -f "$HOME/.env" ]; then
        print_warning "~/.env not found"
        print_info "Create ~/.env with your API keys:"
        echo "    export OPENAI_API_KEY=sk-..."
        echo "    export ANTHROPIC_API_KEY=sk-ant-..."
        echo "    export GOOGLE_API_KEY=..."
        return 1
    fi

    # Source the file
    set -a
    source "$HOME/.env"
    set +a

    local all_good=true

    if [ -n "$OPENAI_API_KEY" ]; then
        print_success "OPENAI_API_KEY: Set"
    else
        print_warning "OPENAI_API_KEY: Missing"
        all_good=false
    fi

    if [ -n "$ANTHROPIC_API_KEY" ]; then
        print_success "ANTHROPIC_API_KEY: Set"
    else
        print_warning "ANTHROPIC_API_KEY: Missing"
        all_good=false
    fi

    if [ -n "$GOOGLE_API_KEY" ] || [ -n "$GEMINI_API_KEY" ]; then
        print_success "GOOGLE_API_KEY: Set"
    else
        print_warning "GOOGLE_API_KEY: Missing"
        all_good=false
    fi

    if [ "$all_good" = false ]; then
        return 1
    fi
    return 0
}

# ============================================================================
# Summary
# ============================================================================
print_summary() {
    print_header "✅ Setup Complete!"

    local platform_icon="🐧"
    if [ "$PLATFORM" = "macos" ]; then
        platform_icon="🍎"
    fi

    echo -e "  ${GREEN}Platform:${NC} $platform_icon $PLATFORM"
    if [ "$PLATFORM" = "linux" ]; then
        echo -e "  ${GREEN}Distribution:${NC} $LINUX_DISTRO"
    fi
    echo -e "  ${GREEN}Project:${NC} $PROJECT_ROOT"
    echo ""
    echo -e "  ${CYAN}To start SmartTrendTracer:${NC}"
    echo "    ./start_stt.sh"
    echo ""
    echo -e "  ${CYAN}To stop SmartTrendTracer:${NC}"
    echo "    ./stop_stt.sh"
    echo ""
    echo -e "  ${CYAN}Access:${NC}"
    echo "    Frontend: http://localhost:5173"
    echo "    API Docs: http://localhost:8000/docs"
    echo ""
}

# ============================================================================
# Main
# ============================================================================
main() {
    local platform_icon="🐧"
    if [ "$PLATFORM" = "macos" ]; then
        platform_icon="🍎"
    fi

    print_header "🚀 SmartTrendTracer Setup Script"
    echo -e "  Platform: ${GREEN}$platform_icon $PLATFORM${NC}"
    if [ "$PLATFORM" = "linux" ]; then
        echo -e "  Distribution: ${GREEN}$LINUX_DISTRO${NC}"
    fi
    echo -e "  Project: ${GREEN}$PROJECT_ROOT${NC}"

    # Parse arguments
    case "${1:-}" in
        --check|check|status)
            check_dependencies
            check_api_keys || true
            exit $?
            ;;
        --venv|venv|python)
            setup_venv
            exit $?
            ;;
        --mongodb|mongodb|mongo|db)
            setup_mongodb
            exit $?
            ;;
        --frontend|frontend|node|npm)
            setup_frontend
            exit $?
            ;;
        --help|-h|help)
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --check     Only check dependencies"
            echo "  --venv      Only setup virtual environments"
            echo "  --mongodb   Only setup MongoDB"
            echo "  --frontend  Only setup frontend"
            echo "  --help      Show this help"
            echo ""
            echo "Without options, runs full setup."
            exit 0
            ;;
        ""|full|all)
            # Full setup - continue below
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac

    # Full setup
    echo ""
    echo -e "This script will:"
    echo "  1. Check system dependencies"
    echo "  2. Setup Python virtual environments"
    echo "  3. Setup frontend (Node.js)"
    echo "  4. Setup MongoDB"
    echo "  5. Check API keys"
    echo ""
    read -p "Continue? [Y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi

    # Run setup steps
    check_dependencies || print_warning "Some dependencies missing - continuing anyway"
    setup_venv
    setup_frontend
    setup_mongodb || print_warning "MongoDB setup incomplete"
    check_api_keys || print_warning "Some API keys missing"
    print_summary
}

# Run main
main "$@"
