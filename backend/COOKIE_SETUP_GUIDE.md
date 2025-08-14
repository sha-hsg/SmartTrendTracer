# 🍪 Twitter Cookie Setup for SmartTrendTracer

## Why Cookies?
- **Get RETWEETS**: API doesn't show retweets, cookies do!
- **No rate limits**: Unlimited collection
- **Full timeline**: See everything including replies

## Quick Setup (5 minutes)

### Step 1: Get Your Cookies from Twitter

1. **Open Chrome or Firefox**
2. **Go to twitter.com and login** as @sha_hsg
3. **Press F12** (Developer Tools)
4. **Navigate to:**
   - Chrome: `Application` tab → `Storage` → `Cookies` → `https://twitter.com`
   - Firefox: `Storage` tab → `Cookies` → `https://twitter.com`

5. **Find these 2 cookies:**
   - `auth_token` - Long string (most important!)
   - `ct0` - CSRF token

6. **Copy the VALUES** (not the names)

### Step 2: Setup Twscrape with Cookies

```bash
# Run the manual setup
python manual_cookie_setup.py

# It will ask for:
# 1. auth_token value: [paste your auth_token]
# 2. ct0 value: [paste your ct0]
```

### Step 3: Collect ALL Tweets (Including Retweets!)

```bash
# Test if it works
python test_twscrape.py

# Collect everything!
python collect_with_cookies.py
```

## What You Get

✅ **ALL tweets including:**
- Original tweets
- Retweets (like the Hugging Face one!)
- Quote tweets
- Everything!

✅ **No rate limits**
- Collect as much as you want
- All 7 accounts instantly

## Troubleshooting

### "Cookies don't work"
- Cookies expire after a while
- Login to Twitter again
- Get fresh cookies
- Run setup again

### "Can't find auth_token"
- Make sure you're logged in
- Look for a cookie named exactly `auth_token`
- It's a long string (100+ characters)

### "Still no retweets"
- Check if test_twscrape.py shows retweets
- Make sure cookies are from @sha_hsg account

## Alternative: Cookie Export Extension

1. Install Chrome extension: "EditThisCookie" or "Cookie-Editor"
2. Click extension while on twitter.com
3. Export all cookies as JSON
4. Save as `cookies.json` in backend folder
5. Run: `python setup_cookies.py`

## Security Note

⚠️ **Keep your cookies safe!**
- Don't share auth_token with anyone
- It gives full access to your account
- Stored locally only in your database

---

Once set up, you'll see ALL tweets including retweets that the API misses!