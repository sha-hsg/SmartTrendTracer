#!/bin/bash
#
# MongoDB Sync Verification Script
# ==================================
#
# This script checks the synchronization status and helps you understand
# which machine's data is current and what actions you should take.
#
# Usage:
#   ./verify-sync.sh
#
# Use this to:
#   - Check if you're on the right machine
#   - Verify sync status before starting work
#   - See when data was last synced

set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SYNC_DIR="./mongodb_sync"
MONGODB_DB="smarttrendtracer"
MACHINE=$(hostname)

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         MongoDB Sync Status Verification           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Display current machine
echo -e "${BLUE}📍 Current Machine:${NC} $MACHINE"
echo -e "${BLUE}📁 Sync Directory:${NC} $SYNC_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if sync metadata exists
if [ ! -f "$SYNC_DIR/last_export.json" ]; then
    echo -e "${RED}❌ No sync metadata found${NC}"
    echo ""
    echo "This means:"
    echo "  • No sync has been performed yet, OR"
    echo "  • The sync directory hasn't been created"
    echo ""
    echo -e "${YELLOW}What to do:${NC}"
    echo "  1. If this is your first machine: run ./sync-out.sh"
    echo "  2. If syncing from another machine: wait for Syncthing to sync"
    echo ""
    exit 0
fi

# Read metadata
if command -v jq &> /dev/null; then
    SOURCE_MACHINE=$(jq -r '.machine' "$SYNC_DIR/last_export.json")
    SOURCE_TIMESTAMP=$(jq -r '.timestamp' "$SYNC_DIR/last_export.json")
    EXPORTED_AT=$(jq -r '.exported_at' "$SYNC_DIR/last_export.json")
    DOC_COUNT=$(jq -r '.document_count' "$SYNC_DIR/last_export.json")
    DB_SIZE=$(jq -r '.size_mb' "$SYNC_DIR/last_export.json")
    PLATFORM=$(jq -r '.platform' "$SYNC_DIR/last_export.json")
else
    # Fallback if jq is not installed
    SOURCE_MACHINE=$(grep '"machine"' "$SYNC_DIR/last_export.json" | cut -d'"' -f4)
    SOURCE_TIMESTAMP=$(grep '"timestamp"' "$SYNC_DIR/last_export.json" | cut -d'"' -f4)
    EXPORTED_AT=$(grep '"exported_at"' "$SYNC_DIR/last_export.json" | cut -d'"' -f4)
    DOC_COUNT=$(grep '"document_count"' "$SYNC_DIR/last_export.json" | grep -o '[0-9]*')
    DB_SIZE="N/A"
    PLATFORM="Unknown"
fi

# Display sync information
echo -e "${BLUE}📤 Last Export Information:${NC}"
echo "  Machine: $SOURCE_MACHINE ($PLATFORM)"
echo "  Timestamp: $SOURCE_TIMESTAMP"
echo "  Exported at: $EXPORTED_AT"
echo "  Documents: $DOC_COUNT"
if [ "$DB_SIZE" != "N/A" ]; then
    echo "  Size: ${DB_SIZE} MB"
fi
echo ""

# Calculate how long ago the export was made
if command -v date &> /dev/null && [ "$EXPORTED_AT" != "null" ]; then
    # Get export epoch time (cross-platform)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        EXPORT_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$EXPORTED_AT" +%s 2>/dev/null || echo "0")
    else
        # Linux
        EXPORT_EPOCH=$(date -d "$EXPORTED_AT" +%s 2>/dev/null || echo "0")
    fi

    if [ "$EXPORT_EPOCH" != "0" ]; then
        CURRENT_EPOCH=$(date +%s)
        AGE_SECONDS=$((CURRENT_EPOCH - EXPORT_EPOCH))
        AGE_HOURS=$((AGE_SECONDS / 3600))
        AGE_DAYS=$((AGE_SECONDS / 86400))

        echo -e "${BLUE}⏰ Export Age:${NC}"
        if [ $AGE_DAYS -gt 0 ]; then
            echo "  ${AGE_DAYS} day(s) and ${AGE_HOURS} hour(s) ago"
        else
            echo "  ${AGE_HOURS} hour(s) ago"
        fi

        # Warn if very old
        if [ $AGE_DAYS -gt 7 ]; then
            echo -e "  ${RED}⚠️  Very old! Consider re-syncing${NC}"
        elif [ $AGE_DAYS -gt 2 ]; then
            echo -e "  ${YELLOW}⚠️  Slightly old${NC}"
        else
            echo -e "  ${GREEN}✓ Recent${NC}"
        fi
        echo ""
    fi
fi

# Check if sync directory exists
if [ ! -d "$SYNC_DIR/latest" ]; then
    echo -e "${RED}❌ Sync data directory not found${NC}"
    echo ""
    echo "Expected: $SYNC_DIR/latest"
    echo ""
    echo "This means Syncthing hasn't synced the data yet."
    echo ""
    exit 1
fi

# Get local MongoDB status
if mongosh --eval "db.version()" > /dev/null 2>&1; then
    LOCAL_DOCS=$(mongosh $MONGODB_DB --quiet --eval "db.stats().objects" 2>/dev/null || echo "0")
    echo -e "${BLUE}💾 Local MongoDB Status:${NC}"
    echo "  Database: $MONGODB_DB"
    echo "  Documents: $LOCAL_DOCS"
    echo "  Status: Running ✓"
else
    echo -e "${BLUE}💾 Local MongoDB Status:${NC}"
    echo -e "  ${RED}MongoDB is not running${NC}"
    LOCAL_DOCS="unknown"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Determine what action to take
if [ "$SOURCE_MACHINE" = "$MACHINE" ]; then
    # Same machine - data was exported from here
    echo -e "${GREEN}✅ You are on the SOURCE machine ($MACHINE)${NC}"
    echo ""
    echo -e "${YELLOW}📝 What this means:${NC}"
    echo "  • The current sync data was exported from THIS machine"
    echo "  • Your local MongoDB likely has the same data"
    echo "  • You should work here OR sync to the other machine"
    echo ""
    echo -e "${BLUE}💡 Recommended Actions:${NC}"
    echo "  • To continue working here: Just start working"
    echo "  • To switch to other machine:"
    echo "    1. Ensure Syncthing has synced (check Syncthing UI)"
    echo "    2. On other machine, run: ./sync-in.sh"
    echo ""

else
    # Different machine - need to import
    echo -e "${YELLOW}⚠️  You are on a DIFFERENT machine${NC}"
    echo ""
    echo -e "${YELLOW}📝 What this means:${NC}"
    echo "  • Export source: $SOURCE_MACHINE"
    echo "  • Current machine: $MACHINE"
    echo "  • Your local MongoDB may have old/different data"
    echo ""
    echo -e "${BLUE}💡 Recommended Actions:${NC}"
    echo "  ${GREEN}1. Import the synced data:${NC}"
    echo "     ./sync-in.sh"
    echo ""
    echo "  ${YELLOW}2. Or export from this machine if you worked here:${NC}"
    echo "     ./sync-out.sh"
    echo "     (This will overwrite the synced data with your local data)"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT:${NC}"
    echo "  If you worked on $SOURCE_MACHINE last, you should import!"
    echo "  If you worked on $MACHINE last, you should export!"
    echo ""
fi

# Check Syncthing status if available
if command -v curl &> /dev/null; then
    if curl -s http://localhost:8384 > /dev/null 2>&1; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo -e "${GREEN}✓ Syncthing is running${NC}"
        echo "  Web UI: http://localhost:8384"
        echo ""
    fi
fi

# Show quick reference
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${CYAN}📚 Quick Reference:${NC}"
echo "  ./sync-out.sh     Export MongoDB for syncing"
echo "  ./sync-in.sh      Import synced MongoDB"
echo "  ./verify-sync.sh  Check sync status (this script)"
echo ""
