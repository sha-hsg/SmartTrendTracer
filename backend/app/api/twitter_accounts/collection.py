from app.config import settings
from app.repositories import tweets as tweet_repo
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from typing import Dict, List
from datetime import datetime, timezone
from bson import ObjectId

from app.database.mongodb import get_database
from app.services.twitter_lookup_service import get_twitter_lookup_service
from .models import serialize_account
from app.repositories import twitter_accounts_collection as repo
from app.repositories import twitter_accounts_collection_queries as queries

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{account_id}/toggle")
def toggle_account(account_id: str, db=Depends(get_database)):
    """Toggle the enabled status of an account."""
    return repo.toggle_account(account_id=account_id)


@router.post("/{account_id}/refresh")
def refresh_account_info(account_id: str, db=Depends(get_database)):
    """Refresh account info from Twitter API."""
    try:
        account = queries.twitter_accounts_find_one__refresh_account_info_2(account_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid account ID format")

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    service = get_twitter_lookup_service()
    if not service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Twitter lookup service not configured"
        )

    username = account.get('username')
    user_info = service.lookup_user(username)

    if not user_info:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find @{username} on Twitter"
        )

    # Update account with fresh data
    update_data = {
        'twitter_id': user_info.id,
        'display_name': user_info.name,
        'profile_image_url': user_info.profile_image_url,
        'followers_count': user_info.followers_count,
        'verified': user_info.verified,
        'updated_at': datetime.now(timezone.utc)
    }

    queries.twitter_accounts_update_one__refresh_account_info(update_data, account_id)

    updated = queries.twitter_accounts_find_one__refresh_account_info(account_id)
    return serialize_account(updated)


def _process_url_entities(urls: List[Dict]) -> List[Dict]:
    """
    Process URL entities to include preview data from Twitter Cards.
    Mirrors tweet_collector_service.process_urls_with_previews (same output schema).
    """
    processed_urls = []
    for url in urls:
        processed_url = {
            'url': url.get('url'),
            'expanded_url': url.get('expanded_url'),
            'display_url': url.get('display_url'),
            'title': url.get('title'),
            'description': url.get('description'),
            'unwound_url': url.get('unwound_url'),
        }
        if url.get('images'):
            processed_url['preview_images'] = url.get('images')
            if len(url['images']) > 0:
                processed_url['preview_image_url'] = url['images'][0].get('url')
        processed_urls.append(processed_url)
    return processed_urls


def _build_media_entry(raw_media: Dict) -> Dict:
    """Map a raw Twitter API media object to the collector's media schema."""
    return {
        'media_key': raw_media.get('media_key'),
        'type': raw_media.get('type'),
        'url': raw_media.get('url'),
        'preview_image_url': raw_media.get('preview_image_url'),
        'alt_text': raw_media.get('alt_text'),
        'width': raw_media.get('width'),
        'height': raw_media.get('height'),
        'duration_ms': raw_media.get('duration_ms'),
    }


def _collect_tweets_sync(db, account: Dict, account_id: str, max_tweets: int, remaining: int) -> Dict:
    """
    Blocking tweet collection for one account (runs in threadpool).

    Stores tweets with the exact same document schema as the collector service
    (tweet_collector_service.save_tweets_to_mongodb): `_id` = Twitter ID string,
    metrics.{like_count,retweet_count,...}, no separate `tweet_id` field.
    """
    import tweepy

    username = account.get('username')
    twitter_id = account.get('twitter_id')
    now = datetime.now(timezone.utc)

    bearer_token = settings.twitter_bearer_token
    if not bearer_token:
        raise HTTPException(
            status_code=503,
            detail="Twitter API not configured. Set TWITTER_BEARER_TOKEN."
        )

    try:
        client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=False)

        # Get collection state
        state = queries.collection_state_find_one___collect_tweets_sync(username)
        since_id = state.get('last_tweet_id') if state else None

        # Fetch tweets (same fields/expansions as the collector service)
        tweets_response = client.get_users_tweets(
            id=twitter_id,
            max_results=min(max_tweets, 100),  # Twitter API max is 100 per request
            since_id=since_id,
            tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'attachments'],
            media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type', 'duration_ms'],
            expansions=['attachments.media_keys', 'referenced_tweets.id',
                        'referenced_tweets.id.attachments.media_keys']
        )

        if not tweets_response or not tweets_response.data:
            return {
                'success': True,
                'message': f'No new tweets found for @{username}',
                'tweets_collected': 0,
                'new_tweets': 0,
                'remaining_budget': remaining
            }

        # Build lookups from includes (raw dicts, like the collector service)
        media_lookup = {}
        if tweets_response.includes and 'media' in tweets_response.includes:
            for media in tweets_response.includes['media']:
                media_lookup[media.media_key] = media.data

        referenced_lookup = {}
        if tweets_response.includes and 'tweets' in tweets_response.includes:
            for ref_tweet in tweets_response.includes['tweets']:
                referenced_lookup[str(ref_tweet.id)] = ref_tweet.data

        tweets_collected = 0
        newest_id = None

        for tweet in tweets_response.data:
            tweet_data = dict(tweet.data)
            tweet_id = str(tweet_data['id'])

            if not newest_id or int(tweet_id) > int(newest_id):
                newest_id = tweet_id

            if tweet_repo.tweet_exists(tweet_id):
                continue

            text = tweet_data.get('text', '')
            media_keys = list((tweet_data.get('attachments') or {}).get('media_keys', []))

            # Retweets: expand truncated text and take media from the original tweet
            # (same logic as tweet_collector_service)
            for ref in tweet_data.get('referenced_tweets') or []:
                if ref.get('type') == 'retweeted' and str(ref.get('id')) in referenced_lookup:
                    original = referenced_lookup[str(ref['id'])]
                    original_text = original.get('text', '')
                    if text.startswith('RT @'):
                        rt_prefix = text.split(':', 1)[0] + ': '
                        text = rt_prefix + original_text
                    media_keys.extend((original.get('attachments') or {}).get('media_keys', []))
                    break

            media = [
                _build_media_entry(media_lookup[key])
                for key in media_keys if key in media_lookup
            ]

            entities = tweet_data.get('entities') or {}
            tweet_doc = tweet_repo.build_tweet_document(
                tweet_id=tweet_id,
                text=text,
                author_id=tweet_data.get('author_id') or twitter_id,
                author_username=username,
                author_name=account.get('display_name', username),
                created_at=tweet_data.get('created_at'),
                public_metrics=tweet_data.get('public_metrics'),
                entities=entities,
                urls=_process_url_entities(entities.get('urls', [])),
                referenced_tweets=tweet_data.get('referenced_tweets', []),
                media=media,
                collected_at=now,
            )

            if tweet_repo.insert_tweet_if_new(tweet_doc):
                tweets_collected += 1

        # Update collection state (last_tweet_id only moves forward)
        if newest_id:
            tweet_repo.advance_collection_state(
                f'twitter_{username}', last_run=now,
                last_tweet_id=newest_id, tweets_collected=tweets_collected,
            )

        # Update account stats
        queries.twitter_accounts_update_one___collect_tweets_sync(account_id, now, tweets_collected)

        total_fetched = len(tweets_response.data)
        logger.info(f"Manual collection for @{username}: {tweets_collected}/{total_fetched} new tweets stored")
        return {
            'success': True,
            'message': f'Collected {tweets_collected} new tweets from @{username}',
            'tweets_collected': total_fetched,  # Total fetched from API
            'new_tweets': tweets_collected,  # Newly stored (non-duplicates)
            'remaining_budget': remaining - tweets_collected
        }

    except tweepy.TooManyRequests:
        raise HTTPException(
            status_code=429,
            detail="Twitter API rate limit reached. Please wait 15 minutes."
        )
    except tweepy.Unauthorized:
        raise HTTPException(
            status_code=401,
            detail="Twitter API authentication failed. Check TWITTER_BEARER_TOKEN."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual collection failed for @{username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Collection failed: {str(e)}"
        )


@router.post("/{account_id}/collect")
async def trigger_collection(
    account_id: str,
    max_tweets: int = Query(100, ge=10, le=500, description="Maximum tweets to collect"),
    db=Depends(get_database)
):
    """
    Manually trigger tweet collection for a specific account.

    The blocking Twitter API calls run in a threadpool so the event loop
    is not blocked; the response is returned once collection finished.
    Respects the monthly tweet budget (Basic Account Mode).
    """
    try:
        account = queries.twitter_accounts_find_one__trigger_collection(account_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid account ID format")

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    username = account.get('username')
    twitter_id = account.get('twitter_id')

    if not twitter_id:
        raise HTTPException(
            status_code=400,
            detail=f"Account @{username} has no Twitter ID. Please refresh the account first."
        )

    # Check usage limits
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    monthly_count = queries.tweets_count_documents__trigger_collection(month_start)

    if monthly_count >= 10000:
        raise HTTPException(
            status_code=429,
            detail="Monthly tweet limit (10,000) reached. Wait until next month."
        )

    remaining = 10000 - monthly_count
    actual_max = min(max_tweets, remaining)

    return await run_in_threadpool(
        _collect_tweets_sync, db, account, account_id, actual_max, remaining
    )
