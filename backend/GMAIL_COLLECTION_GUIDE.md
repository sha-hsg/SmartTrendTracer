# Gmail Substack Collection Guide

## Overview
The Gmail collector now includes:
1. **Automatic artifact cleaning** - Removes table artifacts like `---|---|---` and lone `|` characters
2. **Date-based collection** - Collect emails from specific time periods
3. **Special handling for forwarded emails** - More lenient image filtering and better cleaning

## Key Improvements

### Comprehensive Artifact Cleaning (Built-in)
The collector now automatically performs 3-pass cleaning to remove:

**Pass 1 - Pipe Prefixes:**
- Removes `| | |` from line beginnings
- Transforms `| | | [View in browser]` → `[View in browser]`

**Pass 2 - Image Tables:**
- Cleans `| ![Image](url)|` → `![Image](url)`
- Removes `---|---|---` separators after images

**Pass 3 - Empty Artifacts:**
- Removes lines with just `|`, `| |`, or `| | |`
- Removes standalone separator lines
- Removes excessive dashes

**Also handles:**
- Invisible Unicode characters (fixes word counts)
- Excessive whitespace
- Preserves legitimate content (links, images, code blocks)

This cleaning happens automatically during collection - all emails are cleaned!

### Image Preservation
- **Direct emails**: Standard image filtering (removes tracking pixels)
- **Forwarded emails**: More lenient filtering (keeps 18x18 avatars and icons)
- Removes CID images (email attachments that can't be displayed)
- Preserves all content images from Substack CDN

## Collection Commands

### Basic Collection

```bash
cd backend

# Collect latest 50 Substack emails (default)
python -m app.collectors.gmail_substack_collector

# Collect more emails
python -m app.collectors.gmail_substack_collector --max 100
```

### Date-Based Collection

#### Collect emails from a specific date (e.g., August 11, 2025)
```bash
python -m app.collectors.gmail_substack_collector --on 2025-08-11
```

#### Collect emails after a certain date
```bash
python -m app.collectors.gmail_substack_collector --after 2025-08-11
```

#### Collect emails before a certain date
```bash
python -m app.collectors.gmail_substack_collector --before 2025-08-12
```

#### Collect emails within a date range
```bash
python -m app.collectors.gmail_substack_collector --after 2025-08-01 --before 2025-08-15
```

### Forwarded Emails Only

#### Collect only forwarded newsletters
```bash
python -m app.collectors.gmail_substack_collector --forwarded
```

#### Collect forwarded emails from a specific date
```bash
python -m app.collectors.gmail_substack_collector --forwarded --on 2025-08-11
```

#### Collect forwarded emails after a date
```bash
python -m app.collectors.gmail_substack_collector --forwarded --after 2025-08-10
```

### Restore Deleted Articles

If you've soft-deleted articles in the UI but want to re-import them:

```bash
# Restore and re-import deleted articles from a specific date
python -m app.collectors.gmail_substack_collector --on 2025-08-11 --restore-deleted

# Restore all deleted articles from last week
python -m app.collectors.gmail_substack_collector --after 2025-08-05 --restore-deleted --max 200

# Restore only forwarded deleted articles
python -m app.collectors.gmail_substack_collector --forwarded --restore-deleted
```

When using `--restore-deleted`:
- Soft-deleted articles will be undeleted
- Their content will be updated with fresh conversion
- All improvements (artifact cleaning, image preservation) will be applied

### Combined Examples

#### Collect all Substack emails from August 11, 2025
```bash
# Direct and forwarded emails from that date
python -m app.collectors.gmail_substack_collector --on 2025-08-11 --max 100
```

#### Collect last week's emails
```bash
python -m app.collectors.gmail_substack_collector --after 2025-08-05 --max 200
```

#### Collect only Nathan Lambert's forwarded emails from last month
```bash
python -m app.collectors.gmail_substack_collector --forwarded --after 2025-07-01 --before 2025-08-01
```

## Custom Queries

You can also use Gmail's search syntax directly:

```bash
# Search for specific author
python -m app.collectors.gmail_substack_collector --query "from:oneusefulthing@substack.com"

# Search for specific keywords
python -m app.collectors.gmail_substack_collector --query "from:substack GPT-5"

# Complex query with date
python -m app.collectors.gmail_substack_collector --query "from:substack after:2025-08-10 before:2025-08-12"
```

## First-Time Setup

If you haven't authenticated yet:

```bash
python -m app.collectors.gmail_substack_collector --setup
```

This will open a browser for Gmail authentication.

## Checking Results

After collection, check the database:

```bash
# Count articles by author
sqlite3 data/tweets.db "SELECT a.name, COUNT(s.id) FROM substack_authors a LEFT JOIN substack_articles s ON a.id = s.author_id GROUP BY a.name;"

# Check recent articles
sqlite3 data/tweets.db "SELECT title, published_at FROM substack_articles ORDER BY published_at DESC LIMIT 10;"

# Check articles from specific date
sqlite3 data/tweets.db "SELECT title, published_at FROM substack_articles WHERE date(published_at) = '2025-08-11';"
```

## Configuration

### Forwarded Authors
Edit `backend/forwarded_authors.json` to configure which forwarded authors to collect:

```json
{
  "forwarded_authors": [
    {"name": "Nathan Lambert", "email": "robotic@substack.com"},
    {"name": "Gary Marcus", "email": "garymarcus@substack.com"},
    {"name": "Sebastian Raschka", "email": "sebastianraschka@substack.com"}
  ]
}
```

## Notes

- The collector automatically skips articles that already exist in the database
- Deleted articles (marked as deleted in DB) won't be re-collected
- Date format must be `YYYY-MM-DD` (e.g., `2025-08-11`)
- Gmail date filters use the email's received date, not the article's published date
- The `--max` parameter limits the number of emails processed, not found

## Troubleshooting

### No emails found
- Check your date format (must be YYYY-MM-DD)
- Gmail might have different timezone - try adjacent dates
- Use `--max 200` to search more emails

### Missing images
- Forwarded emails are now handled specially with more lenient image filtering
- CID images (email attachments) cannot be displayed and are removed
- Run the reprocessing script if needed: `python reprocess_forwarded_articles.py`

### Artifacts in old articles
To clean artifacts from previously collected articles:
```bash
python clean_final_artifacts.py
```

## Examples for Your Request

To collect all Substack emails from August 11, 2025:

```bash
cd backend

# Collect ALL emails from August 11 (both direct and forwarded)
python -m app.collectors.gmail_substack_collector --on 2025-08-11 --max 200

# Or just forwarded emails from that date
python -m app.collectors.gmail_substack_collector --forwarded --on 2025-08-11
```

The collector will:
1. Search Gmail for emails from that specific date
2. Process both direct Substack subscriptions and forwarded newsletters
3. Clean all table artifacts automatically
4. Preserve images appropriately (lenient for forwarded emails)
5. Save to the database with clean markdown