#!/usr/bin/env python3
"""
Standalone Tweet Collector Service (hardened)
- Runs independently from the web server
- Collects tweets on a fixed cadence with proper rate limiting
- Robust DB session handling (no leaks), pagination, and graceful shutdown
- Log rotation and configurable timings via environment variables
"""

import os
import sys
import time
import signal
import logging
import random
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Ensure relative imports work when invoked as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

from app.models import get_db, CollectionState, Tweet
from app.collectors.twitter_collector import TwitterCollector
from app.persistent_rate_limiter import get_persistent_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func  # (kept in case future queries need it)

from logging.handlers import TimedRotatingFileHandler


# =========================
# Configuration via ENV
# =========================
# Main collection interval (default 15 min)
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "900"))
# Minimum minutes between runs (for multi-instance safety)
MIN_SKIP_MINUTES = float(os.getenv("MIN_SKIP_MINUTES", "5"))
# Delay between accounts to be nice to API
INTER_ACCOUNT_DELAY_SECONDS = float(os.getenv("INTER_ACCOUNT_DELAY_SECONDS", "2"))
# Add +/- jitter (fraction) to main sleep to avoid synchronized clients
SLEEP_JITTER_PCT = float(os.getenv("SLEEP_JITTER_PCT", "0.1"))
# Max tweets per page (most APIs allow up to 100)
PER_PAGE_MAX_RESULTS = int(os.getenv("PER_PAGE_MAX_RESULTS", "100"))
# Optional per-account hard cap (safety break for runaway pagination), 0 = unlimited
PER_ACCOUNT_MAX_PAGES = int(os.getenv("PER_ACCOUNT_MAX_PAGES", "0"))

# =========================
# Logging
# =========================
log_dir = Path(__file__).resolve().parent
log_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Rotate daily, keep 7 days
file_handler = TimedRotatingFileHandler(
    filename=str(log_dir / "tweet_collector.log"),
    when="D",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
stream_handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Avoid duplicate handlers if script reloaded
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
else:
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

# =========================
# Shutdown handling
# =========================
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info("Received shutdown signal (%s), stopping collector...", signum)
    running = False


# =========================
# Helper utilities
# =========================
def jitter_sleep(total_seconds: float):
    """
    Sleep in small 1s steps to remain responsive to shutdown.
    Applies +/- jitter to desynchronize with other clients.
    """
    if total_seconds <= 0:
        return

    # Apply jitter once per cycle (e.g., 10% of total)
    if SLEEP_JITTER_PCT > 0:
        delta = total_seconds * SLEEP_JITTER_PCT
        total_seconds = total_seconds + random.uniform(-delta, delta)
        total_seconds = max(0, total_seconds)

    # Sleep in 1-second chunks so Ctrl+C/SIGTERM is responsive
    end_time = time.time() + total_seconds
    while running and time.time() < end_time:
        time.sleep(1)


def get_since_id_for_account(db_session, username: str):
    """
    Determine the since_id for a given account from DB.
    We prefer a dedicated twitter_id field if present; fall back to id.
    Ordering by the monotonic Snowflake (twitter_id) is ideal; otherwise use created_at.
    """
    # Try to detect the model field name at runtime
    twitter_id_attr = "twitter_id" if hasattr(Tweet, "twitter_id") else "id"

    # Use created_at desc as in the original code to find the newest stored tweet
    latest_tweet = (
        db_session.query(Tweet)
        .filter(Tweet.author_username == username)
        .order_by(Tweet.created_at.desc())
        .first()
    )

    if latest_tweet is None:
        return None

    return getattr(latest_tweet, twitter_id_attr, None)


def is_rate_limit_error(exc: Exception) -> bool:
    """
    Detect a 429-like rate limit error more robustly than string matching.
    Works with common HTTP client exceptions, falls back to message sniffing.
    """
    # Tweepy/twitter clients often attach response/status_code
    status_code = getattr(getattr(exc, "response", None), "status_code", None)
    if status_code == 429:
        return True

    code = getattr(exc, "status_code", None)
    if code == 429:
        return True

    # Fallback heuristic
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "too many requests" in msg


def _get_resp_meta_next_token(meta: Any) -> Optional[str]:
    """
    Extract next pagination token from response meta across SDK variants.
    """
    if not meta:
        return None
    # Try attribute then mapping
    return getattr(meta, "next_token", None) or (meta.get("next_token") if isinstance(meta, dict) else None)


def _get_includes_as_dicts(includes: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Normalize includes to dicts for media and referenced tweets.
    Works with SDKs that expose .includes as obj or dict.
    """
    if not includes:
        return {}, {}

    # If it's a dict-like
    if isinstance(includes, dict):
        media_list = includes.get("media", []) or []
        tweets_list = includes.get("tweets", []) or []
    else:
        # Attribute style, default to empty
        media_list = getattr(includes, "media", []) or []
        tweets_list = getattr(includes, "tweets", []) or []

    media_dict = {}
    for m in media_list:
        key = getattr(m, "media_key", None)
        if key:
            media_dict[key] = m

    ref_dict = {}
    for t in tweets_list:
        # Some SDKs use int id; normalize to str
        tid = getattr(t, "id", None)
        if tid is not None:
            ref_dict[str(tid)] = t

    return media_dict, ref_dict


# =========================
# Account ID Verification
# =========================
def verify_and_update_account_ids():
    """
    Verify Twitter account IDs at startup and update accounts.json if needed.
    This prevents collection failures due to incorrect IDs.
    """
    logger.info("🔍 Verifying Twitter account IDs...")
    
    accounts_file = Path(__file__).parent / "accounts.json"
    if not accounts_file.exists():
        logger.warning("accounts.json not found, skipping ID verification")
        return
    
    try:
        # Load accounts from file
        with open(accounts_file, 'r') as f:
            accounts_data = json.load(f)
        
        accounts: List[Dict] = accounts_data.get("accounts", [])
        if not accounts:
            logger.warning("No accounts found in accounts.json")
            return
        
        # Create Twitter collector for API access
        db = next(get_db())
        collector = TwitterCollector(db_session=db)
        
        updated = False
        rate_limiter = get_persistent_rate_limiter()
        
        for account in accounts:
            username = account.get("username")
            stored_id = account.get("id")
            
            if not username:
                continue
                
            # Check rate limit before making request
            if not rate_limiter.can_make_request():
                logger.warning("Rate limited during ID verification, skipping remaining accounts")
                break
            
            try:
                # Look up user by username to get correct ID
                logger.info(f"  Checking @{username} (stored ID: {stored_id})...")
                rate_limiter.record_request()
                
                user_response = collector.client.get_user(username=username)
                if user_response and hasattr(user_response, 'data'):
                    actual_id = str(user_response.data.id)
                    
                    if actual_id != stored_id:
                        logger.warning(f"  ⚠️  ID mismatch for @{username}: stored={stored_id}, actual={actual_id}")
                        logger.info(f"  ✅ Updating @{username} ID to {actual_id}")
                        account["id"] = actual_id
                        updated = True
                    else:
                        logger.info(f"  ✓ @{username} ID is correct: {actual_id}")
                else:
                    logger.warning(f"  ⚠️  Could not verify @{username} - user not found")
                    
                # Small delay between lookups to be nice to API
                time.sleep(0.5)
                
            except Exception as e:
                if is_rate_limit_error(e):
                    logger.warning(f"Rate limited while verifying @{username}, stopping verification")
                    rate_limiter.handle_429_error()
                    break
                else:
                    logger.error(f"  ❌ Error verifying @{username}: {e}")
        
        # Update accounts.json if any IDs were corrected
        if updated:
            logger.info("📝 Updating accounts.json with corrected IDs...")
            with open(accounts_file, 'w') as f:
                json.dump(accounts_data, f, indent=2)
            logger.info("✅ accounts.json updated successfully")
            
            # Reload the config to use updated IDs
            # Note: This assumes ACCOUNTS_TO_FOLLOW is loaded from accounts.json
            logger.info("🔄 Reloading account configuration...")
            # Force reload of the config module
            from app import config
            import importlib
            importlib.reload(config)
            global ACCOUNTS_TO_FOLLOW
            from app.config import ACCOUNTS_TO_FOLLOW
        else:
            logger.info("✅ All account IDs verified correctly")
            
    except Exception as e:
        logger.error(f"Error during ID verification: {e}")
        logger.info("Continuing with existing IDs...")
    finally:
        try:
            db.close()
        except:
            pass


# =========================
# Core collection
# =========================
def collect_tweets() -> Tuple[bool, float]:
    """
    Collect tweets from monitored accounts.

    Returns:
        (success, wait_time_seconds)
        - success=False, wait_time>0: rate-limited; caller should sleep that long
        - success=True: completed (may still have collected 0 tweets)
        - success=False, wait_time=0: unexpected error; caller may retry later
    """
    db = next(get_db())
    try:
        logger.info("=" * 60)
        logger.info("Starting tweet collection cycle")

        # Obtain the persistent rate limiter for the process/node
        rate_limiter = get_persistent_rate_limiter()

        # Check upfront rate limit before beginning the cycle
        if not rate_limiter.can_make_request():
            wait_time = rate_limiter.get_wait_time()
            logger.warning("Rate limited before start; must wait %s sec (%.1f min)",
                           wait_time, wait_time / 60.0)
            return False, wait_time  # <-- NO DB leak due to finally: db.close()

        # Respect minimum spacing between runs (multi-instance guard heuristic)
        last_run = CollectionState.get_last_run(db)
        if last_run:
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            minutes_since = (datetime.now(timezone.utc) - last_run).total_seconds() / 60.0
            logger.info("Last successful collection: %.1f minutes ago", minutes_since)
            if minutes_since < MIN_SKIP_MINUTES:
                logger.info("Too recent (< %.1f min); skipping collection", MIN_SKIP_MINUTES)
                return True, 0.0

        collector = TwitterCollector(db_session=db)
        new_tweets_total = 0
        collected_from = []
        completed_all_accounts = True  # flipped to False if we break early

        # Iterate accounts
        for account in ACCOUNTS_TO_FOLLOW:
            if not running:
                completed_all_accounts = False
                logger.info("Shutdown requested; stopping mid-cycle.")
                break

            username = account.get("username")
            user_id = account.get("id")
            if not username or not user_id:
                logger.warning("Skipping account with missing username/id: %r", account)
                continue

            logger.info("Collecting from @%s ...", username)

            # Check rate limit per account before the request
            if not rate_limiter.can_make_request():
                wait_time = rate_limiter.get_wait_time()
                logger.warning("Hit rate limit before @%s; need to wait %s sec", username, wait_time)
                completed_all_accounts = False
                return False, wait_time

            # Pessimistically record the request (safer than post-call)
            rate_limiter.record_request()

            # Determine since_id to avoid duplicates
            since_id = get_since_id_for_account(db, username)

            account_new = 0
            page_count = 0
            next_token = None

            # Paginate until exhausted or limit reached
            while running:
                try:
                    # Optional page cap to prevent runaway loops
                    if PER_ACCOUNT_MAX_PAGES and page_count >= PER_ACCOUNT_MAX_PAGES:
                        logger.info("Reached PER_ACCOUNT_MAX_PAGES (%d) for @%s", PER_ACCOUNT_MAX_PAGES, username)
                        break

                    resp = collector.client.get_users_tweets(
                        id=user_id,
                        max_results=PER_PAGE_MAX_RESULTS,
                        since_id=since_id,
                        tweet_fields=[
                            'created_at', 'public_metrics', 'referenced_tweets',
                            'entities', 'attachments', 'note_tweet'
                        ],
                        media_fields=[
                            'preview_image_url', 'url', 'alt_text', 'type', 'width', 'height'
                        ],
                        expansions=[
                            'attachments.media_keys',
                            'referenced_tweets.id',
                            'referenced_tweets.id.attachments.media_keys'
                        ],
                        pagination_token=next_token
                    )

                    data = getattr(resp, "data", None) or []
                    includes = getattr(resp, "includes", None)
                    meta = getattr(resp, "meta", None) or (resp if isinstance(resp, dict) else None)

                    media_dict, referenced_tweets_dict = _get_includes_as_dicts(includes)

                    # Prefer public save method; fall back to legacy private method
                    save_func = getattr(collector, "save_tweet", None) or getattr(collector, "_save_tweet")

                    for t in data:
                        # save_tweet returns True if it was a new insert
                        if save_func(t, account, media_dict, referenced_tweets_dict):
                            new_tweets_total += 1
                            account_new += 1

                    page_count += 1
                    # Determine next page
                    next_token = _get_resp_meta_next_token(meta)
                    if not next_token:
                        break  # no more pages

                    # Gentle short pause between pages to be nice to API
                    if not running:
                        break
                    time.sleep(0.5)

                except Exception as e:
                    if is_rate_limit_error(e):
                        logger.error("Rate limit during @%s page %d: %s", username, page_count, e)
                        # Let the limiter compute its backoff
                        rate_limiter.handle_429_error()
                        completed_all_accounts = False
                        
                        # IMPORTANT: Commit any tweets collected so far before returning
                        if new_tweets_total > 0:
                            try:
                                logger.info("Committing %d tweets collected before rate limit...", new_tweets_total)
                                db.commit()
                            except Exception as commit_error:
                                logger.error("Failed to commit tweets before rate limit: %s", commit_error)
                                db.rollback()
                        
                        # Return the wait time so main loop sleeps appropriately
                        return False, rate_limiter.get_wait_time()
                    else:
                        logger.error("Error collecting from @%s (page %d): %s", username, page_count, e)
                        # Do not abort entire cycle on one account's error; move on
                        break

            if account_new > 0:
                logger.info("  ✓ Collected %d new tweets from @%s", account_new, username)
                collected_from.append(username)
            else:
                logger.info("  - No new tweets from @%s", username)

            # Small delay between accounts (configurable)
            if running and INTER_ACCOUNT_DELAY_SECONDS > 0:
                time.sleep(INTER_ACCOUNT_DELAY_SECONDS)

        # Persist tweets regardless of whether all accounts completed
        try:
            db.commit()
        except Exception as e:
            logger.error("Commit failed; rolling back: %s", e)
            db.rollback()
            # Treat as failure so caller can retry later
            return False, 0.0

        # Only mark last_run on fully successful, all-accounts cycle
        if completed_all_accounts:
            CollectionState.update_last_run(db, tweet_count=new_tweets_total)
            try:
                db.commit()
            except Exception as e:
                logger.error("Failed to update collection state; rolling back: %s", e)
                db.rollback()
                return False, 0.0

        # Summary
        logger.info("Collection complete: %d new tweets from %d accounts%s",
                    new_tweets_total, len(collected_from),
                    "" if completed_all_accounts else " (partial)")
        if collected_from:
            logger.info("Collected from: %s", ", ".join(collected_from))

        # success=True, no enforced wait time
        return True, 0.0

    except Exception as e:
        # Rollback any partial transaction on unexpected errors
        logger.error("Error during collection: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return False, 0.0

    finally:
        # Always close the session (prevents connection leaks)
        try:
            db.close()
        except Exception:
            pass


# =========================
# Main loop
# =========================
def main():
    """Main collector loop with graceful shutdown and jittered cadence."""
    global running

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("🚀 Tweet Collector Service Started")
    
    # Verify and update account IDs on startup
    verify_and_update_account_ids()
    
    logger.info("Monitoring %d accounts", len(ACCOUNTS_TO_FOLLOW))
    logger.info("Will collect tweets every %s seconds (~%.0f minutes)",
                COLLECTION_INTERVAL_SECONDS, COLLECTION_INTERVAL_SECONDS / 60.0)
    logger.info("Press Ctrl+C to stop\n")

    while running:
        try:
            success, wait_time = collect_tweets()

            if not running:
                break

            if not success and wait_time > 0:
                # Rate-limited: sleep the backoff precisely (no extra jitter)
                logger.info("Rate limited; sleeping %.1f seconds before next attempt...", wait_time)
                jitter_sleep(wait_time)
            else:
                # Normal cadence sleep (with jitter)
                logger.info("Next collection in ~%.0f minutes", COLLECTION_INTERVAL_SECONDS / 60.0)
                logger.info("-" * 60)
                jitter_sleep(COLLECTION_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received; shutting down.")
            break
        except Exception as e:
            logger.error("Unexpected error in main loop: %s", e)
            # Cooldown before retrying the loop
            jitter_sleep(60)

    logger.info("Tweet Collector Service stopped")


if __name__ == "__main__":
    main()