"""
Twitter Lookup Service - Provides user lookup functionality using Twitter API v2.
Uses Tweepy to retrieve user information by username.
"""
from app.config import settings
import os
import tweepy
from typing import Optional
from dataclasses import dataclass


@dataclass
class TwitterUserInfo:
    """Data class representing Twitter user information."""
    id: str
    username: str
    name: str
    description: Optional[str]
    profile_image_url: Optional[str]
    followers_count: int
    following_count: int
    tweet_count: int
    verified: bool
    created_at: Optional[str]


class TwitterLookupService:
    """Service for looking up Twitter users by username."""

    def __init__(self):
        """Initialize the Twitter lookup service with API credentials."""
        self.bearer_token = settings.twitter_bearer_token
        self.client = None
        self._initialized = False

    def _ensure_client(self):
        """Lazily initialize the Twitter client."""
        if not self._initialized:
            if not self.bearer_token:
                raise ValueError(
                    "TWITTER_BEARER_TOKEN environment variable is required. "
                    "Get your bearer token from https://developer.twitter.com/"
                )
            self.client = tweepy.Client(bearer_token=self.bearer_token)
            self._initialized = True

    def lookup_user(self, username: str) -> Optional[TwitterUserInfo]:
        """
        Look up a Twitter user by username.

        Args:
            username: The Twitter username (without @ symbol)

        Returns:
            TwitterUserInfo object if found, None otherwise

        Raises:
            ValueError: If bearer token is not configured
            tweepy.TweepyException: If API call fails
        """
        self._ensure_client()

        # Remove @ if present
        username = username.lstrip('@')

        try:
            response = self.client.get_user(
                username=username,
                user_fields=[
                    'id',
                    'name',
                    'username',
                    'description',
                    'profile_image_url',
                    'public_metrics',
                    'verified',
                    'created_at'
                ]
            )

            if not response.data:
                return None

            user = response.data
            metrics = user.public_metrics or {}

            return TwitterUserInfo(
                id=str(user.id),
                username=user.username,
                name=user.name,
                description=user.description,
                profile_image_url=user.profile_image_url,
                followers_count=metrics.get('followers_count', 0),
                following_count=metrics.get('following_count', 0),
                tweet_count=metrics.get('tweet_count', 0),
                verified=user.verified or False,
                created_at=user.created_at.isoformat() if user.created_at else None
            )

        except tweepy.NotFound:
            return None
        except tweepy.TweepyException as e:
            # Log the error and re-raise
            print(f"Twitter API error looking up user '{username}': {e}")
            raise

    def validate_user(self, username: str) -> dict:
        """
        Validate if a username exists on Twitter.

        Args:
            username: The Twitter username to validate

        Returns:
            dict with 'exists' boolean and optional 'user' info
        """
        try:
            user_info = self.lookup_user(username)
            if user_info:
                return {
                    'exists': True,
                    'user': {
                        'id': user_info.id,
                        'username': user_info.username,
                        'name': user_info.name,
                        'description': user_info.description,
                        'profile_image_url': user_info.profile_image_url,
                        'followers_count': user_info.followers_count,
                        'verified': user_info.verified
                    }
                }
            return {'exists': False, 'user': None}
        except ValueError as e:
            return {'exists': False, 'error': str(e)}
        except Exception as e:
            return {'exists': False, 'error': f"API error: {str(e)}"}

    def is_configured(self) -> bool:
        """Check if the service is properly configured with API credentials."""
        return bool(settings.twitter_bearer_token)


# Singleton instance
_twitter_lookup_service: Optional[TwitterLookupService] = None


def get_twitter_lookup_service() -> TwitterLookupService:
    """Get the singleton Twitter lookup service instance."""
    global _twitter_lookup_service
    if _twitter_lookup_service is None:
        _twitter_lookup_service = TwitterLookupService()
    return _twitter_lookup_service
