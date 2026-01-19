#!/bin/bash
#
# MongoDB Export Script for Cross-Machine Synchronization
# ========================================================
#
# This script exports the MongoDB database to a format suitable for Syncthing
# synchronization between Linux and macOS machines.
#
# Usage:
#   ./sync-out.sh
#
# What it does:
#   1. Exports MongoDB database using mongodump
#   2. Creates timestamped metadata for sync verification
#   3. Prepares data for Syncthing to sync to other machine
#
# Run this at the END of your work session before switching machines.

set -e  # Exit on any error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SYNC_DIR="./mongodb_sync"
MONGODB_DB="smarttrendtracer"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MACHINE=$(hostname)

# Get ISO 8601 timestamp
ISO_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MongoDB Export for Cross-Machine Sync            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if MongoDB is running
if ! mongosh --eval "db.version()" > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: MongoDB is not running${NC}"
    echo ""
    echo "Please start MongoDB first:"
    echo "  macOS:   brew services start mongodb-community"
    echo "  Linux:   sudo systemctl start mongod"
    exit 1
fi

# Get database statistics before export
DOC_COUNT=$(mongosh $MONGODB_DB --quiet --eval "print(Number(db.stats().objects))" 2>/dev/null || echo "0")
DB_SIZE=$(mongosh $MONGODB_DB --quiet --eval "print(Math.round(db.stats().dataSize / 1024 / 1024))" 2>/dev/null || echo "0")

echo -e "${BLUE}📊 Current Database Status:${NC}"
echo "  Database: $MONGODB_DB"
echo "  Documents: $DOC_COUNT"
echo "  Size: ${DB_SIZE} MB"
echo "  Machine: $MACHINE"
echo ""

# Create sync directory if needed
mkdir -p "$SYNC_DIR/backups"

# Export MongoDB
echo -e "${YELLOW}🔄 Exporting MongoDB database...${NC}"

TEMP_DUMP="$SYNC_DIR/dump_$TIMESTAMP"
if mongodump --db="$MONGODB_DB" --out="$TEMP_DUMP" --quiet; then
    echo -e "${GREEN}✓ MongoDB export successful${NC}"
else
    echo -e "${RED}❌ MongoDB export failed${NC}"
    rm -rf "$TEMP_DUMP"
    exit 1
fi

# Remove old 'latest' dump if exists
if [ -d "$SYNC_DIR/latest" ]; then
    echo -e "${YELLOW}🗑️  Removing previous export...${NC}"
    rm -rf "$SYNC_DIR/latest"
fi

# Move new dump to 'latest'
mv "$TEMP_DUMP/$MONGODB_DB" "$SYNC_DIR/latest"
rm -rf "$TEMP_DUMP"

echo -e "${GREEN}✓ Export moved to sync directory${NC}"

# Create metadata file
echo -e "${YELLOW}📝 Writing sync metadata...${NC}"

cat > "$SYNC_DIR/last_export.json" <<EOF
{
  "machine": "$MACHINE",
  "timestamp": "$TIMESTAMP",
  "exported_at": "$ISO_TIMESTAMP",
  "database": "$MONGODB_DB",
  "document_count": $DOC_COUNT,
  "size_mb": $DB_SIZE,
  "platform": "$(uname -s)",
  "hostname": "$MACHINE"
}
EOF

echo -e "${GREEN}✓ Metadata created${NC}"

# Calculate export size
EXPORT_SIZE=$(du -sh "$SYNC_DIR/latest" | cut -f1)

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║             Export Completed Successfully          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📦 Export Details:${NC}"
echo "  Location: $SYNC_DIR/latest/"
echo "  Size: $EXPORT_SIZE"
echo "  Documents: $DOC_COUNT"
echo ""
echo -e "${BLUE}📡 Next Steps:${NC}"
echo "  1. Wait for Syncthing to sync (check Syncthing UI)"
echo "  2. On the other machine, run: ./sync-in.sh"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  - Ensure Syncthing is running and syncing"
echo "  - Don't work on this machine until you've synced back"
echo "  - Commit and push any code changes: git add . && git commit && git push"
echo ""

# Show Syncthing status if cli is available
if command -v syncthing &> /dev/null; then
    echo -e "${BLUE}💡 Syncthing Status:${NC}"
    echo "  Open Syncthing UI: http://localhost:8384"
    echo ""
fi

echo -e "${GREEN}✅ Ready to switch machines!${NC}"
echo ""
