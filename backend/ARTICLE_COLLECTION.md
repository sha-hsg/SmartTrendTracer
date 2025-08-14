# Substack Article Collection Guide

## Collecting Today's Articles Only

### Quick Start - Simple Command

```bash
cd backend

# Collect ALL articles from today (both forwarded and direct)
python todays_articles.py

# Collect ONLY forwarded articles from today
python todays_articles.py --forwarded-only
```

### Advanced Command with Options

```bash
cd backend

# Collect all articles from today with detailed logging
python collect_todays_articles.py

# Collect only forwarded articles
python collect_todays_articles.py --forwarded-only

# Collect only direct subscriptions
python collect_todays_articles.py --direct-only

# Enable verbose debug logging
python collect_todays_articles.py --verbose
```

## How It Works

### Date Filtering
- The scripts automatically filter for emails received **today only**
- Uses Gmail's date query format: `after:2025/1/11 before:2025/1/12`
- Time is in UTC, from midnight to current time

### Article Types

#### Forwarded Articles
- From: `siegfried.handschuh@unisg.ch`
- Authors: Nathan Lambert, Gary Marcus, Sebastian Raschka
- These are newsletters forwarded from your university email

#### Direct Subscriptions
- From: `substack.com`
- Authors: Ethan Mollick, David Szabo-Stuban
- These are newsletters sent directly to your Gmail

### Gmail Query Examples

The scripts build queries like:
```
# Today's forwarded articles only
(from:siegfried.handschuh@unisg.ch AND substack) AND after:2025/1/11

# Today's direct articles only
from:substack.com AND after:2025/1/11

# All of today's articles
(from:substack.com OR from:siegfried.handschuh@unisg.ch) AND after:2025/1/11
```

## Output

The scripts will show:
- Number of emails found
- Articles being processed
- Duplicates skipped
- Final statistics

Example output:
```
=== Starting Today's Article Collection ===
Collection date: 2025-01-11
Including forwarded articles in search
Including direct subscription articles in search
Gmail query: (from:substack.com OR from:siegfried.handschuh@unisg.ch) AND after:2025/1/11

📬 Found 3 Substack emails
✓ Saved: "AI's Next Frontier" by Nathan Lambert
✓ Saved: "The Alignment Problem" by Gary Marcus
⚠ Duplicate: "One Useful Thing" by Ethan Mollick

=== Collection Summary ===
Date: 2025-01-11
New articles collected: 2
  - Forwarded: 2
  - Direct: 0
Duplicates skipped: 1
```

## Viewing Collected Articles

After collection, view your articles at:
```
http://localhost:3000/substack
```

## Troubleshooting

### No Articles Found
- Check if you have new emails from today
- Verify Gmail authentication is working
- Check if articles are already in the database (duplicates)

### Authentication Issues
- Delete `token.pickle` and re-authenticate:
  ```bash
  rm token.pickle
  python todays_articles.py
  ```

### Date/Time Issues
- The script uses UTC time
- "Today" means from UTC midnight to now
- Check your timezone if articles seem missing

## Database Location
Articles are stored in: `backend/data/tweets.db`

## Authors Configuration
Forwarded authors are configured in: `backend/forwarded_authors.json`