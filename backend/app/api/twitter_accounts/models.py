from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Pydantic models
class TwitterAccountCreate(BaseModel):
    """Model for creating a new Twitter account."""
    username: str = Field(..., min_length=1, max_length=50, description="Twitter username (@ optional)")
    display_name: Optional[str] = Field(None, description="Optional display name (uses Twitter name if not provided)")
    category: str = Field("Other", description="Account category")
    description: Optional[str] = Field(None, description="Account description")
    tier: int = Field(2, ge=1, le=3, description="Collection priority tier")
    enabled: bool = Field(True, description="Whether to collect from this account")


class TwitterAccountUpdate(BaseModel):
    """Model for updating a Twitter account."""
    display_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[int] = Field(None, ge=1, le=3)
    enabled: Optional[bool] = None


class TwitterAccountResponse(BaseModel):
    """Response model for Twitter account."""
    id: str
    twitter_id: str
    username: str
    display_name: str
    category: str
    description: Optional[str]
    tier: int
    enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    profile_image_url: Optional[str]
    followers_count: Optional[int]
    verified: Optional[bool]
    last_collected_at: Optional[datetime]
    tweets_collected: int

    class Config:
        from_attributes = True


def serialize_account(account: dict) -> dict:
    """Serialize MongoDB account document to response format."""
    return {
        'id': str(account['_id']),
        'twitter_id': account.get('twitter_id', ''),
        'username': account.get('username', ''),
        'display_name': account.get('display_name', account.get('username', '')),
        'category': account.get('category', 'Other'),
        'description': account.get('description'),
        'tier': account.get('tier', 2),
        'enabled': account.get('enabled', True),
        'created_at': account.get('created_at'),
        'updated_at': account.get('updated_at'),
        'profile_image_url': account.get('profile_image_url'),
        'followers_count': account.get('followers_count'),
        'verified': account.get('verified'),
        'last_collected_at': account.get('last_collected_at'),
        'tweets_collected': account.get('tweets_collected', 0)
    }
