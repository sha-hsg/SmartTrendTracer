# SmartTrendTracer - Cross-Platform Sync Workflow

This guide explains how to synchronize SmartTrendTracer between your Linux and macOS notebooks using Syncthing and MongoDB dump/restore.

## Overview

**Architecture:**
- **Code**: Git repository (standard version control)
- **File Data**: Syncthing (PDFs, images, FAISS indexes)
- **MongoDB Data**: mongodump/mongorestore via Syncthing
- **Environment**: Global `~/.env` on each machine (identical keys)

**Workflow:**
1. End work on Machine A → `sync-out.sh` (export MongoDB)
2. Syncthing syncs overnight (automatic)
3. Start work on Machine B → `sync-in.sh` (import MongoDB)

## Prerequisites

### On Both Machines

1. **MongoDB** installed and running
   ```bash
   # macOS
   brew install mongodb-community
   brew services start mongodb-community

   # Linux (Ubuntu/Debian)
   sudo apt install mongodb
   sudo systemctl start mongod
   ```

2. **Syncthing** installed and configured
   ```bash
   # macOS
   brew install syncthing
   brew services start syncthing

   # Linux
   sudo apt install syncthing
   systemctl --user enable syncthing
   systemctl --user start syncthing
   ```

3. **jq** for JSON parsing (optional but recommended)
   ```bash
   # macOS
   brew install jq

   # Linux
   sudo apt install jq
   ```

4. **Global ~/.env** file with API keys
   - Copy all variables from `backend/.env.example` to `~/.env`
   - Set actual API keys (OpenAI, Anthropic, Google, Twitter, etc.)
   - Ensure both machines have **identical** ~/.env files

## Initial Setup

### 1. Syncthing Configuration

Open Syncthing Web UI: http://localhost:8384

#### Add the Other Machine

1. **Actions** → **Show ID**
2. Copy your Device ID
3. On the other machine: **Actions** → **Add Remote Device**
4. Paste the Device ID and give it a name
5. **Save**

#### Configure Sync Folders

**Folder 1: Data Files**
- Path: `/path/to/SmartTrendTracer/backend/data`
- Label: `STT-Data`
- Share with: Other device
- File Versioning: **Staggered** (30 versions, 30 days)
- Ignore Patterns:
  ```
  *.pyc
  __pycache__
  *.log
  .DS_Store
  ```

**Folder 2: MongoDB Sync**
- Path: `/path/to/SmartTrendTracer/backend/mongodb_sync`
- Label: `STT-MongoDB-Sync`
- Share with: Other device
- File Versioning: **Staggered** (30 versions, 30 days)
- Ignore Patterns:
  ```
  backups/*
  ```

**Folder 3: Configuration**
- Path: `/path/to/SmartTrendTracer/backend`
- Label: `STT-Config`
- Share with: Other device
- Files to sync:
  - `llm.json`
  - `prompts_config.json`
  - `reddit_config.json`
  - `accounts.json`
  - `forwarded_authors.json`
- Ignore everything else

### 2. Test Syncthing

1. Create a test file in `backend/data/` on one machine
2. Verify it appears on the other machine
3. Delete the test file

## Daily Workflow

### Ending Work (Machine A)

```bash
cd ~/Documents/Development/Research/SmartTrendTracer/backend

# 1. Export MongoDB
./sync-out.sh

# 2. Commit code changes
cd ..
git add .
git commit -m "Work session: [description]"
git push

# 3. Verify Syncthing is syncing
# Open http://localhost:8384 and check "mongodb_sync" folder shows "Syncing" or "Up to Date"

# 4. Shut down (Syncthing will sync in background)
```

**What happens:**
- `sync-out.sh` exports MongoDB to `mongodb_sync/latest/`
- Creates metadata in `mongodb_sync/last_export.json`
- Syncthing detects the changes and starts syncing
- Sync continues even if machine is shut down (will resume on next boot)

### Starting Work (Machine B)

```bash
cd ~/path/to/SmartTrendTracer/backend

# 1. Pull latest code
cd ..
git pull

# 2. Check sync status
cd backend
./verify-sync.sh

# 3. Import MongoDB
./sync-in.sh

# 4. Verify everything is ready
mongosh smarttrendtracer --eval "db.tweets.countDocuments()"

# 5. Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (new terminal)
cd ../frontend
npm run dev

# Ready to work!
```

**What happens:**
- `verify-sync.sh` shows who exported, when, and from which machine
- `sync-in.sh` creates backup, then imports MongoDB (overwrites local)
- Local database now matches the other machine

## Script Reference

### sync-out.sh

**Purpose:** Export MongoDB for syncing

**Usage:**
```bash
./sync-out.sh
```

**What it does:**
1. Checks MongoDB is running
2. Shows current database statistics
3. Exports MongoDB to `mongodb_sync/latest/`
4. Creates metadata JSON with machine name, timestamp, doc count
5. Displays sync status

**Run this:** At the **END** of your work session

### sync-in.sh

**Purpose:** Import MongoDB from synced data

**Usage:**
```bash
./sync-in.sh
```

**What it does:**
1. Checks sync data exists
2. Shows source machine and export timestamp
3. Warns if data is stale (>7 days old)
4. Creates backup of current local MongoDB
5. Drops local database and imports synced data
6. Verifies import was successful

**Run this:** At the **START** of your work session on new machine

**Safety features:**
- Creates automatic backup before import
- Warns if importing from same machine
- Warns if data is old
- Requires confirmation before proceeding

### verify-sync.sh

**Purpose:** Check sync status without making changes

**Usage:**
```bash
./verify-sync.sh
```

**What it shows:**
- Current machine name
- Source machine (who exported last)
- Export timestamp and age
- Local MongoDB status
- Recommended actions
- Syncthing status

**Run this:** Anytime to check status (no side effects)

## Troubleshooting

### MongoDB Not Running

**Symptoms:**
- Scripts show "MongoDB is not running"

**Solutions:**
```bash
# macOS
brew services list | grep mongodb
brew services restart mongodb-community

# Linux
sudo systemctl status mongod
sudo systemctl restart mongod
```

### No Sync Data Found

**Symptoms:**
- `sync-in.sh` says "No sync data found"

**Causes:**
1. Haven't run `sync-out.sh` on other machine yet
2. Syncthing hasn't finished syncing

**Solutions:**
1. On the other machine, run `./sync-out.sh`
2. Check Syncthing UI: http://localhost:8384
3. Verify "mongodb_sync" folder shows "Up to Date"
4. Wait for sync to complete

### Data is Stale (Old)

**Symptoms:**
- `sync-in.sh` warns "Export is X days old"

**Causes:**
- Haven't synced from other machine recently
- Syncthing was offline

**Solutions:**
1. Check if you actually worked on the other machine recently
2. If yes: wait for Syncthing to sync
3. If no: proceed with import (data is still valid)
4. Consider running `sync-out.sh` on current machine if it has newer data

### Accidentally Worked on Wrong Machine

**Scenario:**
You started work on Machine B but forgot to run `sync-in.sh`. Now Machine B has new data that wasn't synced.

**Solutions:**

**Option A: Keep Machine B's data (it's newer)**
```bash
# On Machine B
./sync-out.sh
# This exports Machine B's data
# Syncthing will sync it to Machine A
# Next time on Machine A, sync-in.sh will import it
```

**Option B: Discard Machine B's work (Machine A is correct)**
```bash
# On Machine B
./sync-in.sh
# This imports Machine A's data, overwriting your work on Machine B
# Your Machine B work is backed up in mongodb_sync/backups/
```

**Option C: Merge manually (advanced)**
```bash
# On Machine B, backup your current work
mongodump --db=smarttrendtracer --out=/tmp/machine_b_backup

# Import Machine A's data
./sync-in.sh

# Now manually merge what you need from the backup
# This requires MongoDB knowledge and careful merging
```

### Syncthing Not Syncing

**Symptoms:**
- Syncthing shows "Disconnected" or folders stuck in "Scanning"

**Solutions:**
1. Check both machines are online
2. Check firewall settings (allow Syncthing ports)
3. Restart Syncthing:
   ```bash
   # macOS
   brew services restart syncthing

   # Linux
   systemctl --user restart syncthing
   ```
4. Check Syncthing logs for errors
5. Verify devices are connected in Web UI

### Import Failed

**Symptoms:**
- `sync-in.sh` shows "Import failed!"

**Solutions:**
1. Check MongoDB is running and accessible
2. Check disk space (`df -h`)
3. Check MongoDB logs for errors
4. Restore from backup:
   ```bash
   # The backup location is shown in the error message
   mongorestore --db=smarttrendtracer --drop /path/to/backup/smarttrendtracer
   ```

## File Synchronization Details

### What Gets Synced

**Via Syncthing (automatic):**
- `backend/data/papers/` - Research paper PDFs
- `backend/data/book_repository/` - Books (PDF, EPUB)
- `backend/data/paper_repository/` - Processed papers with images
- `backend/data/article_images/` - Substack article images
- `backend/data/rag_index/` - FAISS RAG indexes
- `backend/data/vector_store/` - Tag embeddings cache
- `backend/mongodb_sync/latest/` - MongoDB dumps
- `backend/mongodb_sync/last_export.json` - Sync metadata
- `backend/*.json` - Configuration files

**Via Git (manual):**
- All code in `backend/app/`
- All code in `frontend/src/`
- README, docs, etc.

**NOT Synced (machine-specific):**
- `backend/.env` - Use global `~/.env` instead
- `backend/venv/` - Recreate per machine
- `backend/node_modules/` - Recreate per machine
- `backend/logs/` - Machine-specific logs
- `backend/mongodb_sync/backups/` - Local backups only
- MongoDB data directory - Synced via dump/restore only

### Why Not Sync MongoDB Data Directory?

**DO NOT** sync MongoDB's data directory directly via Syncthing!

**Reasons:**
- **Corruption risk:** MongoDB writes can be in progress during sync
- **Platform differences:** Binary format may differ between versions
- **Lock files:** MongoDB lock files cause conflicts
- **Index incompatibility:** Indexes may not transfer correctly

**Instead:** Use `mongodump`/`mongorestore` (what our scripts do)
- Safe: MongoDB is snapshot-consistent
- Portable: Works across MongoDB versions and platforms
- Proven: Standard MongoDB backup/restore method

## Platform-Specific Notes

### macOS

- File paths use `/Users/username/`
- MongoDB via Homebrew: `brew services start mongodb-community`
- Case-insensitive filesystem (be aware when naming files)
- `.DS_Store` files automatically excluded

### Linux

- File paths use `/home/username/`
- MongoDB via apt: `sudo systemctl start mongod`
- Case-sensitive filesystem
- May need to set file permissions after sync

### Cross-Platform Compatibility

**Verified Compatible:**
- ✅ PDF files (binary, cross-platform)
- ✅ Images (PNG, JPG - binary, cross-platform)
- ✅ FAISS indexes (binary, same Python version)
- ✅ Pickle files (Python 3.12 on both machines)
- ✅ JSON configuration files
- ✅ MongoDB dumps (BSON format is portable)

**Potential Issues:**
- ⚠️ File permissions (Syncthing preserves, but check)
- ⚠️ Symlinks (avoid using, or configure Syncthing to follow)
- ⚠️ Case sensitivity (avoid filenames that differ only in case)

## Best Practices

### Do's ✅

- ✅ Always run `verify-sync.sh` before starting work
- ✅ Always run `sync-out.sh` at end of day
- ✅ Wait for Syncthing to show "Up to Date" before switching
- ✅ Commit code changes to git regularly
- ✅ Keep `~/.env` identical on both machines
- ✅ Check Syncthing UI occasionally

### Don'ts ❌

- ❌ Don't work on both machines in the same day
- ❌ Don't skip `sync-in.sh` when switching machines
- ❌ Don't manually copy MongoDB data directory
- ❌ Don't commit `.env` to git
- ❌ Don't ignore warnings from sync scripts
- ❌ Don't turn off Syncthing during work

### Workflow Tips

1. **Morning routine:**
   ```bash
   git pull
   ./verify-sync.sh
   ./sync-in.sh
   ```

2. **Evening routine:**
   ```bash
   ./sync-out.sh
   git add . && git commit -m "..." && git push
   ```

3. **Check Syncthing daily:** Quick glance at Web UI to ensure syncing

4. **Weekly maintenance:** Clean old backups:
   ```bash
   # Keep only last 5 backups
   cd backend/mongodb_sync/backups
   ls -t | tail -n +6 | xargs rm -rf
   ```

## Emergency Procedures

### Lost Data on One Machine

**Scenario:** Machine A had a disk failure.

**Solution:**
1. Reinstall MongoDB on Machine A
2. Run `sync-in.sh` on Machine A
3. Data is restored from Machine B (via Syncthing sync)

### Both Machines Out of Sync

**Scenario:** Worked on both machines accidentally.

**Solution:**
1. Decide which machine has the "truth" (most recent work)
2. On the correct machine, run `sync-out.sh`
3. On the other machine, run `sync-in.sh`
4. The "wrong" machine's data is backed up in `mongodb_sync/backups/`
5. Manually merge if needed

### Syncthing Conflict

**Scenario:** Syncthing created `.sync-conflict` files.

**Solution:**
1. Identify the correct version (usually most recent)
2. Keep the correct file
3. Delete the conflict files
4. Syncthing will propagate the change

## Advanced Usage

### Manual MongoDB Backup

```bash
# Create a named backup
mongodump --db=smarttrendtracer --out=backup_$(date +%Y%m%d)

# Restore from backup
mongorestore --db=smarttrendtracer --drop backup_20250122/smarttrendtracer
```

### Check MongoDB Size

```bash
mongosh smarttrendtracer --eval "db.stats(1024*1024)"
```

### Force Syncthing Sync

```bash
# Trigger immediate scan
# In Syncthing Web UI: Click folder → "Rescan"

# Or via API
curl -X POST http://localhost:8384/rest/db/scan?folder=STT-MongoDB-Sync
```

### Export Specific Collections

```bash
# Export only tweets
mongodump --db=smarttrendtracer --collection=tweets --out=tweets_backup

# Restore specific collection
mongorestore --db=smarttrendtracer --collection=tweets tweets_backup/smarttrendtracer/tweets.bson
```

## Security Considerations

1. **API Keys:**
   - Never commit `.env` to git
   - Keep `~/.env` with `chmod 600` permissions
   - Rotate keys regularly

2. **Syncthing:**
   - Enable encryption for syncing over internet
   - Use introducers for multi-device setup
   - Review shared folders regularly

3. **MongoDB:**
   - Enable authentication in production
   - Bind to localhost only (not 0.0.0.0)
   - Keep backups encrypted

## Support

### Common Questions

**Q: How long does sync take?**
A: Depends on data size and network speed. Typical: 5-30 minutes for full database.

**Q: Can I work offline?**
A: Yes! Sync when you have network. MongoDB export/import works offline.

**Q: What if I'm not sure which machine to sync from?**
A: Run `./verify-sync.sh` on both machines. It will tell you.

**Q: Can I add a third machine?**
A: Yes! Add it to Syncthing and follow the same workflow.

### Getting Help

1. Check this documentation
2. Run `./verify-sync.sh` to diagnose
3. Check Syncthing Web UI logs
4. Check MongoDB logs: `tail -f /usr/local/var/log/mongodb/mongo.log` (macOS)
5. Review script output for specific error messages

---

**Last Updated:** 2025-01-22
**Version:** 1.0
