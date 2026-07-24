import pickle
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail(credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
    """Authenticate with Gmail API and return the service object"""
    creds = None
    token_path = Path(token_file)

    # Load existing token
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_file).exists():
                raise FileNotFoundError(
                    f"Gmail credentials file not found: {credentials_file}\n"
                    "Please follow these steps:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create a new project or select existing\n"
                    "3. Enable Gmail API\n"
                    "4. Create OAuth 2.0 credentials\n"
                    "5. Download credentials.json to this directory"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service
