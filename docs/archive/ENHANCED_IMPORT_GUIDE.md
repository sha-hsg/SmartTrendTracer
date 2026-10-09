# Enhanced Article Import Guide

## Overview
The Enhanced Article Import feature allows you to import subscriber-only content from Substack and other publications using browser authentication cookies. This guide explains how to use this feature to import full articles that you have access to as a paid subscriber.

## Features
- **Basic Import**: For publicly accessible articles
- **Cookie Authentication**: Import subscriber-only content using browser cookies
- **cURL Import**: Direct import using cURL commands from browser DevTools
- **Paywall Detection**: Automatically detects if an article requires authentication
- **Content Verification**: Shows content increase percentage when re-importing

## How to Use

### Method 1: Basic Import (Public Articles)
1. Open the Substack Dashboard in SmartTrendTracer
2. Click "Import from URL" button
3. Enter the article URL
4. Click "Import Article"

### Method 2: Enhanced Import with Cookies (Subscriber Content)

#### Step 1: Get Your Browser Cookies
1. **Sign in to the publication** in your web browser
2. **Navigate to the article** you want to import
3. **Open Developer Tools** (F12 or right-click → Inspect)
4. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
5. Click on **Cookies** in the left sidebar
6. Find cookies for the publication domain (e.g., `magazine.sebastianraschka.com`)
7. **Copy important cookies** like:
   - `connect.sid` (session ID)
   - `cookie_storage_key`
   - Any authentication-related cookies

#### Step 2: Format Your Cookie String
Combine cookies in this format:
```
cookie_name1=value1; cookie_name2=value2; cookie_name3=value3
```

Example:
```
connect.sid=s%3AkSKHV5VA8pk-txZIn1NKg_HNYb60Dfru.OlM%2FHOpUi8vu4EKUzzEMi3uMHhEdFhfKjqc7dgpPIsg; cookie_storage_key=d83cec84-23da-4f94-bf73-e5c4d381caa9
```

#### Step 3: Import Using Cookie Authentication
1. Click **"Import (Subscriber)"** button in the dashboard
2. Enter the article URL
3. Click on **"Cookie Auth"** tab
4. Paste your cookie string
5. Click **"Import with Authentication"**

### Method 3: cURL Import (Advanced)

#### Step 1: Get cURL Command from Browser
1. Sign in and navigate to the article
2. Open Developer Tools (F12)
3. Go to **Network** tab
4. **Refresh the page** (F5)
5. Find the main article request (usually the first one)
6. Right-click on it → **Copy** → **Copy as cURL**

#### Step 2: Import Using cURL
1. Click **"Import (Subscriber)"** button
2. Enter the article URL
3. Click on **"cURL Import"** tab
4. Paste the complete cURL command
5. Click **"Import with cURL"**

## API Endpoints

### Check Paywall Status
```http
POST /api/v2/articles/enhanced/check-paywall?url={article_url}
```

### Basic Import
```http
POST /api/v2/articles/enhanced/import-basic
{
  "url": "https://example.substack.com/p/article"
}
```

### Cookie String Import
```http
POST /api/v2/articles/enhanced/import-with-cookie-string
{
  "url": "https://example.substack.com/p/article",
  "cookies": "session_id=abc123; auth_token=xyz789"
}
```

### cURL Import
```http
POST /api/v2/articles/enhanced/import-with-cookies
{
  "url": "https://example.substack.com/p/article",
  "curl_command": "curl 'https://...' -H 'cookie: ...'"
}
```

## Testing the API

Run the test script to verify the endpoints:
```bash
cd backend
python test_enhanced_import.py
```

## Important Notes

### Security
- **Cookies are NOT stored**: They are used only for the immediate import request
- **Use your own cookies**: Only use cookies from your authenticated sessions
- **Cookies expire**: You may need to refresh cookies if they expire

### Supported Sites
- Substack publications (primary support)
- Medium articles
- Personal blogs
- Most standard HTML article pages

### Troubleshooting

#### "Could not find cookies in cURL command"
- Make sure you copied the complete cURL command
- Check that the command includes `-H 'cookie: ...'` or `--cookie '...'`

#### "This article requires authentication"
- The article is behind a paywall
- Use the Cookie Auth or cURL Import method

#### "Import failed: Could not find article content"
- The site structure may not be supported
- Try using the cURL method for better compatibility

#### Content appears truncated
- Verify you're signed in to the publication
- Check that cookies haven't expired
- Try refreshing your browser session and getting new cookies

## Example: Importing Sebastian Raschka's Article

1. **Sign in** to https://magazine.sebastianraschka.com
2. **Navigate** to the article: https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one
3. **Open DevTools** and go to Application → Cookies
4. **Copy cookies** for `magazine.sebastianraschka.com`
5. **Format as string**: `connect.sid=xxx; cookie_storage_key=yyy`
6. **Use Enhanced Import** in SmartTrendTracer with the cookie string
7. **Verify** the import shows full content (4,400+ words instead of 1,295)

## Success Indicators
- ✅ Full article content imported
- ✅ Word count matches the original article
- ✅ "Content Increase" shows percentage if re-importing
- ✅ No paywall message in imported content
- ✅ References/conclusion sections present at the end

## Support
For issues or questions about the enhanced import feature:
1. Check the troubleshooting section above
2. Verify your cookies are current and valid
3. Try the alternative import methods
4. Check the API test results with `test_enhanced_import.py`