#!/bin/bash
# Cron script to fix missing media
# Add to crontab with: */20 * * * * /path/to/media_fixer_cron.sh

cd /Users/siehan/Sync/05-Development/02-SG/SG2025/SmartTrendTracer/backend
source venv/bin/activate
python fix_media_with_resume.py >> media_fix.log 2>&1