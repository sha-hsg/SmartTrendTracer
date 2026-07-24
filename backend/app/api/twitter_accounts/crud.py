import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId

from app.database.mongodb import get_database
from app.services.twitter_lookup_service import get_twitter_lookup_service
from .models import (
    TwitterAccountCreate,
    TwitterAccountUpdate,
    TwitterAccountResponse,
    serialize_account,
)

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
    query = {}

    if enabled_only:
        query['enabled'] = True

    if tier is not None:
        query['tier'] = tier

    if category:
        query['category'] = category

    accounts = list(db.twitter_accounts.find(query).sort([
        ('tier', 1),
        ('username', 1)
    ]))

    return [serialize_account(acc) for acc in accounts]


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
    try:
        account = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid account ID format")

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Build update document
    update_data = {'updated_at': datetime.now(timezone.utc)}

    if data.display_name is not None:
        update_data['display_name'] = data.display_name
    if data.category is not None:
        update_data['category'] = data.category
    if data.description is not None:
        update_data['description'] = data.description
    if data.tier is not None:
        update_data['tier'] = data.tier
    if data.enabled is not None:
        update_data['enabled'] = data.enabled

    db.twitter_accounts.update_one(
        {'_id': ObjectId(account_id)},
        {'$set': update_data}
    )

    # Fetch updated document
    updated = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    return serialize_account(updated)


@router.delete("/{account_id}")
def delete_account(
    account_id: str,
    delete_tweets: bool = Query(False, description="Also delete all tweets from this account"),
    db=Depends(get_database)
):
    """Delete a Twitter account. Optionally delete all associated tweets."""
    try:
        account = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid account ID format")

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    username = account.get('username')
    tweets_deleted = 0

    # Optionally delete tweets
    if delete_tweets:
        result = db.tweets.delete_many({'author_username': username})
        tweets_deleted = result.deleted_count

    # Delete account
    db.twitter_accounts.delete_one({'_id': ObjectId(account_id)})

    return {
        'message': f"Account @{username} deleted successfully",
        'tweets_deleted': tweets_deleted
    }
