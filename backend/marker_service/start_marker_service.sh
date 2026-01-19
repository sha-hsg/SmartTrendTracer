#!/usr/bin/env bash
set -euo pipefail

# --- Configurable values (override via env if needed) ---
PORT="${PORT:-8002}"
HOST="${HOST:-0.0.0.0}"
APP_MODULE="marker_server:app"
VENV_DIR="${VENV_DIR:-marker_env}"
DEV_RELOAD="${DEV_RELOAD:-false}"
WORKERS="${WORKERS:-1}"

# Resolve script directory early (used below)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer CLI path (server reads these and will harvest CLI outputs)
export MARKER_FORCE_CLI="${MARKER_FORCE_CLI:-1}"
export MARKER_ALWAYS_CLI="${MARKER_ALWAYS_CLI:-1}"

# Keep debug ON
export MARKER_DEBUG="${MARKER_DEBUG:-1}"

# Optional caches (speed-ups)
export SURYA_CACHE_DIR="${SURYA_CACHE_DIR:-$HOME/.cache/surya}"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"

# --- SmartTrendTracer-compatible settings ---
# Images live under marker_service/data/paper_images by default.
# (If your main app expects backend/data/paper_images, use a symlink or override IMAGE_BASE_DIR before running.)
export IMAGE_BASE_DIR="${IMAGE_BASE_DIR:-$SCRIPT_DIR/data/paper_images}"

# IMPORTANT: Return API URLs (not filesystem paths) in markdown so the main server can serve them.
export MARKER_REWRITE_TO_FILES="${MARKER_REWRITE_TO_FILES:-0}"

# Canonicalize IMAGE_BASE_DIR to a real absolute path (portable across macOS/Linux)
RESOLVED_IMAGE_BASE_DIR="$(
  python - <<'PY'
import os
p = os.environ.get("IMAGE_BASE_DIR", "")
print(os.path.realpath(p) if p else "")
PY
)"
if [[ -n "$RESOLVED_IMAGE_BASE_DIR" ]]; then
  export IMAGE_BASE_DIR="$RESOLVED_IMAGE_BASE_DIR"
fi

# Ensure image base dir exists and is writable
mkdir -p "$IMAGE_BASE_DIR" || true
if [[ ! -w "$IMAGE_BASE_DIR" ]]; then
  echo "▲ WARNING: IMAGE_BASE_DIR is not writable: $IMAGE_BASE_DIR" >&2
fi

# --- Virtualenv bootstrap ---
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtualenv at $VENV_DIR ..."
  python -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
export PATH="$VENV_DIR/bin:$PATH"

# Ensure runtime deps (uvicorn, python-multipart) are present
if ! python - <<'PY'
import sys
try:
    import uvicorn  # noqa: F401
    import multipart  # noqa: F401
except Exception:
    sys.exit(1)
else:
    sys.exit(0)
PY
then
  echo "Installing runtime deps (uvicorn, python-multipart) ..."
  python -m pip install -q "uvicorn>=0.30.0,<1" "python-multipart>=0.0.9"
fi

# Discover executables in this venv
MARKER_SINGLE_PATH="$(command -v marker_single || true)"
MARKER_PATH="$(command -v marker || true)"
PY_PATH="$(command -v python || true)"

cat <<EOF
---- Startup Configuration ---
MARKER_FORCE_CLI       = ${MARKER_FORCE_CLI}
MARKER_ALWAYS_CLI      = ${MARKER_ALWAYS_CLI}
MARKER_DEBUG           = ${MARKER_DEBUG}
MARKER_REWRITE_TO_FILES= ${MARKER_REWRITE_TO_FILES}
IMAGE_BASE_DIR         = ${IMAGE_BASE_DIR}
marker_single          = ${MARKER_SINGLE_PATH:-"(not found)"}
marker                 = ${MARKER_PATH:-"(not found)"}
python                 = ${PY_PATH}
Working directory      = ${PWD}
------------------------------
EOF

# Hard fail if CLI-first is requested but marker_single is missing
if [[ "${MARKER_FORCE_CLI}" == "1" || "${MARKER_ALWAYS_CLI}" == "1" ]]; then
  if [[ -z "${MARKER_SINGLE_PATH}" ]]; then
    echo "ERROR: marker_single not found in current environment."
    echo "       Install marker-pdf into this venv:"
    echo "         source ${VENV_DIR}/bin/activate && pip install marker-pdf"
    exit 1
  fi
fi

# Build uvicorn args
UVICORN_ARGS=(
  --host "$HOST"
  --port "$PORT"
  --workers "$WORKERS"
  --timeout-keep-alive "120"
  --app-dir "$SCRIPT_DIR"
)

# Enable auto-reload for local dev
if [[ "$DEV_RELOAD" == "true" ]]; then
  UVICORN_ARGS+=("--reload")
fi

echo "Launching Marker service on http://$HOST:$PORT ..."
exec python -m uvicorn "$APP_MODULE" "${UVICORN_ARGS[@]}"