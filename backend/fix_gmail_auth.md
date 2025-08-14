# Fix Gmail Authentication "Access Blocked" Issue

## Quick Fix: Enable Test Mode

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **OAuth consent screen**
4. Under **Test users**, click **+ ADD USERS**
5. Add your Gmail email address
6. Click **SAVE**

Now try authenticating again - it should work!

## Alternative: Use "Internal" App Type

If you're using a Google Workspace account:

1. Go to **OAuth consent screen**
2. Edit the app
3. Change User Type to **Internal** (if available)
4. This removes all verification requirements

## Option 3: Use Service Account (Advanced)

For fully automated collection without OAuth prompts:

```python
# We can implement service account authentication
# This requires different setup but works without user interaction
```

## Option 4: Use App Password (Simpler but Less Secure)

We could switch to IMAP with app-specific password:
1. Enable 2-factor authentication in Gmail
2. Generate app-specific password
3. Use IMAP to fetch emails

Would you like me to implement IMAP-based collection instead?