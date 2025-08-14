# Collecting Sebastian Raschka's Forwarded Newsletters

## Command to Collect Sebastian Raschka's Articles from August 11, 2025

To collect forwarded emails from Sebastian Raschka from a specific date, use:

```bash
cd backend

# Option 1: Using a custom Gmail query
python -m app.collectors.gmail_substack_collector --query "from:me to:me (Sebastian Raschka OR sebastianraschka@substack.com) after:2025-08-11" --max 100

# Option 2: More specific query with both author name and email
python -m app.collectors.gmail_substack_collector --query "from:me to:me Sebastian Raschka sebastianraschka@substack.com after:2025-08-11 before:2025-08-12" --max 100

# Option 3: Collect ALL forwarded Substack emails from that date
python -m app.collectors.gmail_substack_collector --query "from:me to:me substack after:2025-08-11" --max 200
```

## How Forwarded Emails Are Processed

The Gmail Substack collector automatically detects and specially processes forwarded emails:

### 1. **Detection**
Forwarded emails are detected by looking for:
- `From:` and `Date:` headers in the HTML body
- `Original Message` or `Forwarded message` text
- MS Outlook mobile reference markers
- Presence of `@substack.com` in forwarded headers

### 2. **Special Processing for Forwarded Emails**
When a forwarded email is detected:

- **📧 Aggressive Cleaning**: Removes forwarding headers and metadata
- **🖼️ Lenient Image Filtering**: Keeps smaller images (18x18 avatars/icons)
- **📝 Smart Title Extraction**: Uses email subject instead of trying to extract from content
- **🧹 Extra Markdown Cleanup**: Additional pass to clean forwarding artifacts

### 3. **Configured Forwarded Authors**
The system recognizes these forwarded authors (configured in `forwarded_authors.json`):
- Nathan Lambert (robotic@substack.com)
- Gary Marcus (garymarcus@substack.com)
- Sebastian Raschka (sebastianraschka@substack.com)

## Verifying Collection

After running the collection, verify the results:

```bash
# Check how many Sebastian Raschka articles were collected
sqlite3 data/tweets.db "SELECT COUNT(*) FROM substack_articles sa JOIN substack_authors a ON sa.author_id = a.id WHERE a.name = 'Sebastian Raschka';"

# List Sebastian Raschka's articles
sqlite3 data/tweets.db "SELECT sa.title, sa.published_at FROM substack_articles sa JOIN substack_authors a ON sa.author_id = a.id WHERE a.name = 'Sebastian Raschka' ORDER BY sa.published_at DESC;"

# Check articles from August 11, 2025
sqlite3 data/tweets.db "SELECT sa.title, a.name FROM substack_articles sa JOIN substack_authors a ON sa.author_id = a.id WHERE date(sa.published_at) = '2025-08-11';"
```

## Full Processing Pipeline

When collecting forwarded emails, the collector:

1. **Searches Gmail** with your query
2. **Detects forwarded emails** automatically
3. **Applies special cleaning**:
   - Removes forwarding headers
   - Preserves content images
   - Cleans table artifacts (pipes, separators)
   - Removes invisible characters
4. **Saves to database** with proper author attribution

## Example Collection Session

```bash
# Collect Sebastian Raschka's forwarded emails from August 11
python -m app.collectors.gmail_substack_collector --query "from:me to:me Sebastian Raschka after:2025-08-11 before:2025-08-12" --max 50

# Expected output:
📧 Final query: from:me to:me Sebastian Raschka after:2025-08-11 before:2025-08-12...
🔍 Searching for Substack newsletters...
📧 Authenticating with Gmail...
📬 Found X Substack emails

📖 Processing email 1/X...
  📧 Detected forwarded email, applying aggressive cleaning...
  ✅ Saved: [Article Title]...
```

## Notes

- The `--max` parameter limits how many emails are processed
- Use date ranges (`after:` and `before:`) to narrow your search
- The collector automatically handles all artifact cleaning
- Forwarded emails get special processing for better results
- All configured forwarded authors are properly attributed