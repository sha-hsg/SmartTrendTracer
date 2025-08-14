# Substack Integration Setup Guide

This guide will help you set up Substack newsletter collection for SmartTrendTracer.

## Prerequisites

1. Gmail account where you receive (or can forward) Substack newsletters
2. Google Cloud Console access (free)
3. Python environment with required dependencies

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements_substack.txt
```

## Step 2: Create Database Tables

```bash
python migrate_substack.py
```

## Step 3: Setup Gmail API

### Option A: Interactive Setup (Recommended)

```bash
python setup_gmail.py
```

This will guide you through:
1. Enabling Gmail API in Google Cloud Console
2. Creating OAuth credentials
3. Downloading credentials.json
4. Authenticating with your Gmail account

### Option B: Manual Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `credentials.json` to backend directory
6. Run authentication:
   ```bash
   python -m app.collectors.gmail_substack_collector --setup
   ```

## Step 4: Configure Authors

Edit `backend/substack_authors.json` to add the Substack authors you follow:

```json
{
  "authors": [
    {
      "subdomain": "astralcodexten",
      "name": "Astral Codex Ten",
      "tags": ["rationality", "philosophy"]
    }
  ]
}
```

## Step 5: Collect Newsletters

### One-time collection:
```bash
python -m app.collectors.gmail_substack_collector
```

### With custom parameters:
```bash
# Collect only unread newsletters
python -m app.collectors.gmail_substack_collector --query "from:substack.com is:unread"

# Collect last 100 newsletters
python -m app.collectors.gmail_substack_collector --max 100
```

## Step 6: Access in Dashboard

Start the backend API:
```bash
npm run api
```

Start the frontend:
```bash
cd ../frontend
npm run dev
```

Navigate to `http://localhost:3000` and click on the "Substack" tab.

## Gmail Filter Tips

To better organize Substack emails:

1. In Gmail, create a filter:
   - From: `substack.com`
   - Apply label: `Substack` or `Newsletter`
   
2. Then collect with:
   ```bash
   python -m app.collectors.gmail_substack_collector --query "label:Substack"
   ```

## Forwarding Setup (Optional)

If you want to keep Substack emails separate:

1. Create a dedicated Gmail account for SmartTrendTracer
2. In your main email, forward Substack emails to this account
3. Set up Gmail API on the dedicated account

## Troubleshooting

### "credentials.json not found"
- Download from Google Cloud Console
- Place in `backend/` directory

### "Token expired"
- Delete `token.pickle`
- Run authentication again

### No emails found
- Check Gmail search query
- Verify emails are in inbox
- Try broader search: `from:substack.com`

### Rate limiting
- Gmail API has generous limits (1 billion units/day)
- Each email fetch = ~5 units
- Unlikely to hit limits with normal usage

## Features

Once set up, you can:
- 📖 Read full articles in Markdown format
- 🏷️ Tag articles and snippets
- ✂️ Highlight and annotate text snippets
- 📊 Analyze trends across articles
- 🤖 Generate AI summaries
- 🔍 Search across all content
- 📈 Track reading patterns

## Next Steps

1. Set up automated collection (cron job or scheduler)
2. Configure LLM for article summarization
3. Create reading lists and collections
4. Export annotations and highlights