import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone

from app.database.mongodb import get_database
from app.services.twitter_lookup_service import get_twitter_lookup_service
from .models import (
    TwitterAccountCreate,
    TwitterAccountUpdate,
    TwitterAccountResponse,
    serialize_account,
)
from app.repositories import twitter_accounts_crud as repo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[TwitterAccountResponse])
def list_accounts(
    enabled_only: bool = Query(False, description="Only return enabled accounts"),
    tier: Optional[int] = Query(None, ge=1, le=3, description="Filter by tier"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db=Depends(get_database)
):
    """List all Twitter accounts with optional filtering."""
    return repo.list_accounts(enabled_only=enabled_only, tier=tier, category=category)


@router.get("/lookup")
def lookup_twitter_user(username: str = Query(..., description="Twitter username to look up")):
    """
    Look up a Twitter user by username to get their ID and profile info.
    This uses the Twitter API and requires TWITTER_BEARER_TOKEN to be set.
    """
    service = get_twitter_lookup_service()

    if not service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Twitter lookup service not configured. Set TWITTER_BEARER_TOKEN environment variable."
        )

    result = service.validate_user(username)

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/", response_model=TwitterAccountResponse)
def create_account(data: TwitterAccountCreate, db=Depends(get_database)):
    """
    Create a new Twitter account to monitor.
    Automatically looks up Twitter ID if TWITTER_BEARER_TOKEN is configured.
    """
    username = data.username.lstrip('@')

    # Check if already exists
    existing = db.twitter_accounts.find_one({'username': {'$regex': f'^{username}$', '$options': 'i'}})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Account @{username} already exists"
        )

    # Try to look up Twitter user info
    twitter_id = ''
    display_name = data.display_name or username
    profile_image_url = None
    followers_count = None
    verified = None

    service = get_twitter_lookup_service()
    if service.is_configured():
        try:
            user_info = service.lookup_user(username)
            if user_info:
                twitter_id = user_info.id
                display_name = data.display_name or user_info.name
                profile_image_url = user_info.profile_image_url
                followers_count = user_info.followers_count
                verified = user_info.verified
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Twitter user @{username} not found"
                )
        except HTTPException:
            raise
        except Exception as e:
            # Log but continue without Twitter info
            logger.warning(f"Could not lookup Twitter user @{username}: {e}")

    now = datetime.now(timezone.utc)
    document = {
        'twitter_id': twitter_id,
        'username': username,
        'display_name': display_name,
        'category': data.category,
        'description': data.description,
        'tier': data.tier,
        'enabled': data.enabled,
        'created_at': now,
        'updated_at': now,
        'profile_image_url': profile_image_url,
        'followers_count': followers_count,
        'verified': verified,
        'last_collected_at': None,
        'tweets_collected': 0
    }

    result = db.twitter_accounts.insert_one(document)
    document['_id'] = result.inserted_id

    return serialize_account(document)


@router.put("/{account_id}", response_model=TwitterAccountResponse)
def update_account(account_id: str, data: TwitterAccountUpdate, db=Depends(get_database)):
    """Update an existing Twitter account."""
    return repo.update_account(account_id=account_id, data=data)


@router.delete("/{account_id}")
def delete_account(
    account_id: str,
    delete_tweets: bool = Query(False, description="Also delete all tweets from this account"),
    db=Depends(get_database)
):
    """Delete a Twitter account. Optionally delete all associated tweets."""
    return repo.delete_account(account_id=account_id, delete_tweets=delete_tweets)
