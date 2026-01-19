#!/bin/bash
#
# MongoDB Import Script for Cross-Machine Synchronization
# ========================================================
#
# This script imports the MongoDB database that was synced from another machine
# via Syncthing.
#
# Usage:
#   ./sync-in.sh
#
# What it does:
#   1. Creates a backup of the current local MongoDB database
#   2. Imports the synced database from the other machine (OVERWRITES local data)
#   3. Verifies the import was successful
#
# Run this at the START of your work session on a new machine.
#
# IMPORTANT: This will OVERWRITE your local MongoDB database with the synced data!

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
MACHINE=$(hostname)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MongoDB Import from Cross-Machine Sync           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if sync data exists
if [ ! -d "$SYNC_DIR/latest" ]; then
    echo -e "${RED}❌ Error: No sync data found${NC}"
    echo ""
    echo "Expected directory: $SYNC_DIR/latest"
    echo ""
    echo "This means:"
    echo "  1. You haven't run sync-out.sh on the other machine, OR"
    echo "  2. Syncthing hasn't finished syncing yet"
    echo ""
    echo "What to do:"
    echo "  1. On the other machine, run: ./sync-out.sh"
    echo "  2. Wait for Syncthing to finish syncing"
    echo "  3. Try again"
    exit 1
fi

# Check if MongoDB is running
if ! mongosh --eval "db.version()" > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: MongoDB is not running${NC}"
    echo ""
    echo "Please start MongoDB first:"
    echo "  macOS:   brew services start mongodb-community"
    echo "  Linux:   sudo systemctl start mongod"
    exit 1
fi

# Read sync metadata
if [ -f "$SYNC_DIR/last_export.json" ]; then
    SOURCE_MACHINE=$(jq -r '.machine' "$SYNC_DIR/last_export.json" 2>/dev/null || echo "unknown")
    SOURCE_TIMESTAMP=$(jq -r '.timestamp' "$SYNC_DIR/last_export.json" 2>/dev/null || echo "unknown")
    EXPORTED_AT=$(jq -r '.exported_at' "$SYNC_DIR/last_export.json" 2>/dev/null || echo "unknown")
    DOC_COUNT=$(jq -r '.document_count' "$SYNC_DIR/last_export.json" 2>/dev/null || echo "unknown")

    echo -e "${BLUE}📥 Sync Source Information:${NC}"
    echo "  Source machine: $SOURCE_MACHINE"
    echo "  Exported at: $EXPORTED_AT"
    echo "  Documents: $DOC_COUNT"
    echo ""

    # Warn if source and destination are the same machine
    if [ "$SOURCE_MACHINE" = "$MACHINE" ]; then
        echo -e "${YELLOW}⚠️  WARNING: Source and destination machines are the same!${NC}"
        echo ""
        echo "You're about to import data that was exported from THIS machine."
        echo "This is unusual - you should typically import from the OTHER machine."
        echo ""
        read -p "Do you want to continue anyway? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Import cancelled."
            exit 0
        fi
        echo ""
    fi

    # Check if export is recent (warn if > 7 days old)
    if command -v date &> /dev/null && [ "$EXPORTED_AT" != "unknown" ]; then
        # Calculate age in seconds (cross-platform compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            EXPORT_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$EXPORTED_AT" +%s 2>/dev/null || echo "0")
        else
            # Linux
            EXPORT_EPOCH=$(date -d "$EXPORTED_AT" +%s 2>/dev/null || echo "0")
        fi

        CURRENT_EPOCH=$(date +%s)
        AGE_SECONDS=$((CURRENT_EPOCH - EXPORT_EPOCH))
        AGE_DAYS=$((AGE_SECONDS / 86400))

        if [ $AGE_DAYS -gt 7 ]; then
            echo -e "${YELLOW}⚠️  WARNING: Export is $AGE_DAYS days old!${NC}"
            echo ""
            echo "This data might be stale. Consider:"
            echo "  1. Check if you ran sync-out.sh on the other machine recently"
            echo "  2. Verify Syncthing has finished syncing"
            echo ""
            read -p "Continue with import? (yes/no): " CONFIRM
            if [ "$CONFIRM" != "yes" ]; then
                echo "Import cancelled."
                exit 0
            fi
            echo ""
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Warning: No metadata file found${NC}"
    echo "Proceeding with import anyway..."
    echo ""
fi

# Get current local database statistics
CURRENT_DOCS=$(mongosh $MONGODB_DB --quiet --eval "print(db.stats().objects)" 2>/dev/null || echo "0")

echo -e "${BLUE}📊 Current Local Database:${NC}"
echo "  Machine: $MACHINE"
echo "  Database: $MONGODB_DB"
echo "  Documents: $CURRENT_DOCS"
echo ""

# Confirm before proceeding
echo -e "${YELLOW}⚠️  IMPORTANT WARNING:${NC}"
echo ""
echo "This will:"
echo "  1. Create a backup of your current database"
echo "  2. DELETE your current database"
echo "  3. REPLACE it with the synced database from $SOURCE_MACHINE"
echo ""
echo "Your current $CURRENT_DOCS documents will be replaced."
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo "Import cancelled. No changes made."
    exit 0
fi

echo ""

# Create backup of current database
BACKUP_DIR="$SYNC_DIR/backups/backup_${MACHINE}_${TIMESTAMP}"
echo -e "${YELLOW}💾 Creating backup of current database...${NC}"

if mongodump --db="$MONGODB_DB" --out="$BACKUP_DIR" --quiet; then
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"
    echo "  Size: $BACKUP_SIZE"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    echo "Import cancelled for safety."
    exit 1
fi

echo ""

# Import the synced database (drops existing data)
echo -e "${YELLOW}📥 Importing synced database...${NC}"
echo "  This will overwrite your local database..."

if mongorestore --db="$MONGODB_DB" --drop "$SYNC_DIR/latest" --quiet; then
    echo -e "${GREEN}✓ Database import successful${NC}"
else
    echo -e "${RED}❌ Import failed!${NC}"
    echo ""
    echo "Your data is safe in the backup at:"
    echo "  $BACKUP_DIR"
    echo ""
    echo "To restore the backup:"
    echo "  mongorestore --db=$MONGODB_DB --drop $BACKUP_DIR/$MONGODB_DB"
    exit 1
fi

# Verify import
NEW_DOCS=$(mongosh $MONGODB_DB --quiet --eval "print(db.stats().objects)" 2>/dev/null || echo "0")

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║             Import Completed Successfully          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 New Database Status:${NC}"
echo "  Database: $MONGODB_DB"
echo "  Documents: $NEW_DOCS (was: $CURRENT_DOCS)"
echo "  Machine: $MACHINE"
echo ""
echo -e "${BLUE}💾 Backup Available:${NC}"
echo "  Location: $BACKUP_DIR"
echo "  To restore: mongorestore --db=$MONGODB_DB --drop $BACKUP_DIR/$MONGODB_DB"
echo ""
echo -e "${GREEN}✅ Ready to work on $MACHINE!${NC}"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "  1. Verify your data looks correct"
echo "  2. Start working (backend + frontend)"
echo "  3. When done, run: ./sync-out.sh"
echo ""
