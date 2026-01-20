#!/bin/bash

# SmartTrendTracer - Cross-Platform Python Environment Setup
# Works on both macOS and Linux
#
# Usage:
#   ./setup_python.sh           # Full setup (backend + frontend)
#   ./setup_python.sh backend   # Backend only
#   ./setup_python.sh frontend  # Frontend only
#   ./setup_python.sh check     # Check environment status
#   ./setup_python.sh activate  # Print activation command

set -e  # Exit on error

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
}

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if a venv is valid (python binary exists and works)
check_venv_valid() {
    local venv_path=$1
    if [ -d "$venv_path" ] && [ -x "$venv_path/bin/python" ]; then
        # Test if python actually runs (catches broken symlinks)
        if "$venv_path/bin/python" --version &>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Setup mise for Python version management
setup_mise() {
    log_info "Checking for mise (Python version manager)..."

    if command -v mise &> /dev/null; then
        log_success "mise found: $(mise --version)"

        # Activate mise in current shell
        eval "$(mise activate bash 2>/dev/null)" || true

        # Check if mise.toml exists and install Python
        if [ -f "$SCRIPT_DIR/mise.toml" ]; then
            log_info "Installing Python via mise (from mise.toml)..."
            mise install 2>/dev/null || true
            log_success "mise Python setup complete"
        fi
    else
        log_warn "mise not found - using system Python"
        log_info "Install mise for better Python version management:"
        case "$PLATFORM" in
            macos)
                echo "    brew install mise"
                ;;
            linux)
                echo "    curl https://mise.run | sh"
                ;;
        esac
    fi
}

# Create or recreate virtual environment
setup_venv() {
    local venv_path=$1
    local requirements_file=$2
    local venv_name=$(basename "$venv_path")

    log_info "Setting up virtual environment: $venv_name"

    if check_venv_valid "$venv_path"; then
        log_success "Valid venv found at $venv_path"
        local py_version=$("$venv_path/bin/python" --version 2>&1)
        log_info "Python version: $py_version"
    else
        if [ -d "$venv_path" ]; then
            log_warn "Invalid/broken venv detected (likely from different platform)"
            log_info "Removing broken venv..."
            rm -rf "$venv_path"
        fi

        log_info "Creating new virtual environment..."
        python3 -m venv "$venv_path"

        if ! check_venv_valid "$venv_path"; then
            log_error "Failed to create virtual environment"
            return 1
        fi

        log_success "Virtual environment created"
    fi

    # Upgrade pip
    log_info "Upgrading pip..."
    "$venv_path/bin/python" -m pip install --upgrade pip -q

    # Install requirements if provided
    if [ -n "$requirements_file" ] && [ -f "$requirements_file" ]; then
        log_info "Installing requirements from $requirements_file..."
        "$venv_path/bin/python" -m pip install -r "$requirements_file" -q
        log_success "Requirements installed"
    fi

    return 0
}

# Check ~/.env for API keys
check_env_keys() {
    log_info "Checking API keys in ~/.env..."

    if [ ! -f "$HOME/.env" ]; then
        log_warn "~/.env not found"
        log_info "Create ~/.env with your API keys:"
        echo "    export OPENAI_API_KEY=sk-..."
        echo "    export ANTHROPIC_API_KEY=sk-ant-..."
        echo "    export GOOGLE_API_KEY=..."
        return 1
    fi

    # Load and check keys
    set -a
    source "$HOME/.env"
    set +a

    local missing_keys=()

    [ -z "$OPENAI_API_KEY" ] && missing_keys+=("OPENAI_API_KEY")
    [ -z "$ANTHROPIC_API_KEY" ] && missing_keys+=("ANTHROPIC_API_KEY")
    [ -z "$GOOGLE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ] && missing_keys+=("GOOGLE_API_KEY or GEMINI_API_KEY")

    if [ ${#missing_keys[@]} -gt 0 ]; then
        log_warn "Missing API keys in ~/.env:"
        for key in "${missing_keys[@]}"; do
            echo "    - $key"
        done
    else
        log_success "All primary API keys found"
    fi

    return 0
}

# Setup backend
setup_backend() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}Setting up Backend Python Environment${NC}"
    echo -e "${BLUE}=========================================${NC}"

    local backend_dir="$SCRIPT_DIR/backend"
    cd "$backend_dir"

    # Main backend venv
    setup_venv "venv" "requirements.txt"

    echo ""
    log_info "Backend venv ready. To activate:"
    echo -e "    ${GREEN}source $backend_dir/venv/bin/activate${NC}"

    cd "$SCRIPT_DIR"
}

# Setup Marker service environment
setup_marker() {
    echo ""
    log_info "Setting up Marker Service environment..."

    local marker_dir="$SCRIPT_DIR/backend/marker_service"

    if [ ! -d "$marker_dir" ]; then
        log_warn "Marker service directory not found, skipping"
        return 0
    fi

    cd "$marker_dir"

    if check_venv_valid "marker_env"; then
        log_success "Marker venv already valid"
    else
        log_info "Creating Marker virtual environment..."
        [ -d "marker_env" ] && rm -rf "marker_env"
        python3 -m venv marker_env

        log_info "Installing Marker dependencies..."
        marker_env/bin/pip install --upgrade pip -q
        marker_env/bin/pip install marker-pdf fastapi uvicorn python-multipart -q
        log_success "Marker environment ready"
    fi

    cd "$SCRIPT_DIR"
}

# Setup MinerU service environment
setup_mineru() {
    echo ""
    log_info "Setting up MinerU Service environment..."

    local mineru_dir="$SCRIPT_DIR/backend/mineru_service"

    if [ ! -d "$mineru_dir" ]; then
        log_warn "MinerU service directory not found, skipping"
        return 0
    fi

    cd "$mineru_dir"

    if check_venv_valid "mineru_env"; then
        log_success "MinerU venv already valid"
    else
        log_info "Creating MinerU virtual environment..."
        [ -d "mineru_env" ] && rm -rf "mineru_env"
        python3 -m venv mineru_env

        log_info "Installing MinerU dependencies..."
        mineru_env/bin/pip install --upgrade pip -q
        mineru_env/bin/pip install mineru fastapi uvicorn python-multipart aiofiles -q
        log_success "MinerU environment ready"
    fi

    cd "$SCRIPT_DIR"
}

# Check if node_modules has correct native modules for current platform
check_node_modules_valid() {
    local frontend_dir=$1

    # Check for rollup native module (platform-specific)
    if [[ "$PLATFORM" == "linux" ]]; then
        if [ ! -d "$frontend_dir/node_modules/@rollup/rollup-linux-x64-gnu" ]; then
            return 1  # Missing Linux native module
        fi
    elif [[ "$PLATFORM" == "macos" ]]; then
        # Check for either Intel or ARM mac
        if [ ! -d "$frontend_dir/node_modules/@rollup/rollup-darwin-x64" ] && \
           [ ! -d "$frontend_dir/node_modules/@rollup/rollup-darwin-arm64" ]; then
            return 1  # Missing macOS native module
        fi
    fi
    return 0
}

# Setup frontend
setup_frontend() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}Setting up Frontend (Node.js)${NC}"
    echo -e "${BLUE}=========================================${NC}"

    local frontend_dir="$SCRIPT_DIR/frontend"
    cd "$frontend_dir"

    # Check for Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found"
        log_info "Install Node.js:"
        case "$PLATFORM" in
            macos)
                echo "    brew install node"
                ;;
            linux)
                echo "    sudo apt install nodejs npm  # Debian/Ubuntu"
                echo "    sudo pacman -S nodejs npm    # Arch Linux"
                ;;
        esac
        return 1
    fi

    log_success "Node.js found: $(node --version)"

    # Check/install node_modules
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
        log_success "Frontend dependencies installed"
    elif ! check_node_modules_valid "$frontend_dir"; then
        # node_modules exists but has wrong platform's native modules
        log_warn "node_modules has native modules from different platform"
        log_info "Reinstalling for $PLATFORM..."
        rm -rf node_modules package-lock.json
        npm install
        log_success "Frontend dependencies reinstalled for $PLATFORM"
    else
        log_success "node_modules valid for $PLATFORM"
    fi

    cd "$SCRIPT_DIR"
}

# Check all environments
check_status() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}SmartTrendTracer Environment Status${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""

    detect_platform
    echo "Platform: $PLATFORM"
    echo ""

    # Python version
    echo -n "System Python: "
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}$(python3 --version)${NC}"
    else
        echo -e "${RED}Not found${NC}"
    fi

    # mise
    echo -n "mise: "
    if command -v mise &> /dev/null; then
        echo -e "${GREEN}$(mise --version)${NC}"
    else
        echo -e "${YELLOW}Not installed${NC}"
    fi

    echo ""
    echo "Virtual Environments:"

    # Backend venv
    echo -n "  Backend (backend/venv): "
    if check_venv_valid "$SCRIPT_DIR/backend/venv"; then
        echo -e "${GREEN}Valid${NC} - $($SCRIPT_DIR/backend/venv/bin/python --version)"
    else
        echo -e "${RED}Invalid/Missing${NC}"
    fi

    # Marker venv
    echo -n "  Marker (marker_service/marker_env): "
    if check_venv_valid "$SCRIPT_DIR/backend/marker_service/marker_env"; then
        echo -e "${GREEN}Valid${NC}"
    else
        echo -e "${YELLOW}Invalid/Missing${NC}"
    fi

    # MinerU venv
    echo -n "  MinerU (mineru_service/mineru_env): "
    if check_venv_valid "$SCRIPT_DIR/backend/mineru_service/mineru_env"; then
        echo -e "${GREEN}Valid${NC}"
    else
        echo -e "${YELLOW}Invalid/Missing${NC}"
    fi

    # Frontend
    echo ""
    echo -n "Frontend (node_modules): "
    if [ -d "$SCRIPT_DIR/frontend/node_modules" ]; then
        echo -e "${GREEN}Present${NC}"
    else
        echo -e "${RED}Missing${NC}"
    fi

    # API Keys
    echo ""
    echo "API Keys (~/.env):"
    if [ -f "$HOME/.env" ]; then
        source "$HOME/.env" 2>/dev/null
        echo -n "  OPENAI_API_KEY: "
        [ -n "$OPENAI_API_KEY" ] && echo -e "${GREEN}Set${NC}" || echo -e "${RED}Missing${NC}"
        echo -n "  ANTHROPIC_API_KEY: "
        [ -n "$ANTHROPIC_API_KEY" ] && echo -e "${GREEN}Set${NC}" || echo -e "${RED}Missing${NC}"
        echo -n "  GOOGLE_API_KEY: "
        [ -n "$GOOGLE_API_KEY" ] || [ -n "$GEMINI_API_KEY" ] && echo -e "${GREEN}Set${NC}" || echo -e "${YELLOW}Missing${NC}"
    else
        echo -e "  ${RED}~/.env not found${NC}"
    fi

    # MongoDB
    echo ""
    echo -n "MongoDB: "
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${GREEN}Running${NC}"
    else
        echo -e "${YELLOW}Not running${NC}"
    fi

    echo ""
}

# Print activation command
print_activate() {
    echo ""
    echo "To activate the backend Python environment:"
    echo ""
    echo -e "  ${GREEN}source $SCRIPT_DIR/backend/venv/bin/activate${NC}"
    echo ""
    echo "Or use this one-liner (copy & paste):"
    echo ""
    echo "  cd $SCRIPT_DIR/backend && source venv/bin/activate"
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${BLUE}SmartTrendTracer - Python Environment Setup${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""

    detect_platform
    log_info "Platform: $PLATFORM"

    case "${1:-all}" in
        backend)
            setup_mise
            setup_backend
            setup_marker
            setup_mineru
            check_env_keys
            ;;
        frontend)
            setup_frontend
            ;;
        check)
            check_status
            ;;
        activate)
            print_activate
            ;;
        all|"")
            setup_mise
            setup_backend
            setup_marker
            setup_mineru
            setup_frontend
            check_env_keys
            echo ""
            echo -e "${GREEN}=========================================${NC}"
            echo -e "${GREEN}Setup Complete!${NC}"
            echo -e "${GREEN}=========================================${NC}"
            print_activate
            ;;
        *)
            echo "Usage: $0 [backend|frontend|check|activate|all]"
            echo ""
            echo "  backend   - Setup backend Python environments only"
            echo "  frontend  - Setup frontend Node.js environment only"
            echo "  check     - Check environment status"
            echo "  activate  - Print venv activation command"
            echo "  all       - Full setup (default)"
            exit 1
            ;;
    esac
}

main "$@"
