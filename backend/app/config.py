"""
Configuration for SmartTrendTracer
"""
import os
import json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Load Twitter accounts from JSON file
def load_accounts():
    """Load accounts from accounts.json"""
    accounts_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'accounts.json')
    try:
        with open(accounts_file, 'r') as f:
            data = json.load(f)
            return data['accounts']
    except FileNotFoundError:
        print(f"Warning: {accounts_file} not found, using default accounts")
        return [
            {"username": "OpenAI", "id": "4398626122"},
            {"username": "emollick", "id": "39125788"},
            {"username": "stanfordnlp", "id": "118263124"},
            {"username": "AnthropicAI", "id": "1353836358901501952"},
            {"username": "GoogleDeepMind", "id": "4783690002"},
            {"username": "huggingface", "id": "778764142412984320"},
            {"username": "sama", "id": "1605"}
        ]

# Twitter accounts to follow
ACCOUNTS_TO_FOLLOW = load_accounts()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/tweets.db")

# Twitter API configuration
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("BACKEND_PORT", os.getenv("API_PORT", "8088")))

# Frontend URL for CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Rate limiting
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds