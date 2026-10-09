import pickle
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailLoginRequired(RuntimeError):
    """The Gmail token is missing or revoked and a browser login is needed."""


LOGIN_HINT = ("Gmail login needed (token missing or expired). Run once in a terminal:\n"
              "  cd backend && venv/bin/python -m app.collectors.gmail_substack_collector --setup")


def authenticate_gmail(credentials_file=None, token_file=None, interactive: bool = True):
    """Authenticate with the Gmail API and return the service object.
    interactive=False (scheduler) never opens a browser: it raises
    GmailLoginRequired when a new login is needed."""
    from app.paths import GMAIL_CREDENTIALS, GMAIL_TOKEN
    credentials_file = Path(credentials_file or GMAIL_CREDENTIALS)
    token_path = Path(token_file or GMAIL_TOKEN)
    creds = None
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except Exception as e:            # revoked/expired refresh token (invalid_grant)
                logger.warning(f"Gmail token refresh failed: {e}")
        if not refreshed:
            if not interactive:
                raise GmailLoginRequired(LOGIN_HINT)
            if not credentials_file.exists():
                raise FileNotFoundError(
                    f"Gmail credentials file not found: {credentials_file}\n"
                    "Create OAuth 2.0 desktop credentials for the Gmail API in the Google Cloud console "
                    "and save them as backend/credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)
