#!/bin/bash
# DEPRECATED: This script has moved to scripts/sync-out.sh
# This wrapper forwards to the new location for backwards compatibility

echo ""
echo -e "\033[1;33m================================================\033[0m"
echo -e "\033[1;33m  HINWEIS: Dieses Skript ist deprecated!\033[0m"
echo -e "\033[1;33m  Bitte nutze:  ./scripts/sync-out.sh\033[0m"
echo -e "\033[1;33m================================================\033[0m"
echo ""
sleep 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

exec "$PROJECT_ROOT/scripts/sync-out.sh" "$@"
