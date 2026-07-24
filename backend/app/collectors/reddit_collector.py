"""
Reddit Data Collector using PRAW (Python Reddit API Wrapper)
Collects posts from specified subreddits and stores them in MongoDB
"""
import praw
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.database.mongodb import get_client, get_database
from bson import ObjectId

load_dotenv()

class RedditCollector:
    """Reddit collector service for gathering posts from AI/ML subreddits"""
    
    def __init__(self):
        """Initialize Reddit collector with API credentials and MongoDB connection"""
        
        # Reddit API credentials
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'SmartTrendTracer:v1.0 (by /u/smarttrendtracer)')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in environment variables")
        
        # Initialize PRAW Reddit instance
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
        
        # Test authentication
        try:
            self.reddit.auth.limits
            print("✅ Reddit API authentication successful")
        except Exception as e:
            raise ValueError(f"Reddit API authentication failed: {e}")
        
        # MongoDB connection
        self.mongo_client = get_client()
        self.db = get_database()
        self.posts_collection = self.db.reddit_posts
        self.collection_state = self.db.collection_state
        
        # Load Reddit configuration (absolute path: backend/reddit_config.json,
        # resolved relative to this file so it works regardless of CWD)
        config_path = Path(__file__).resolve().parents[2] / 'reddit_config.json'
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.subreddits = self.config['subreddits']
        self.settings = self.config['collection_settings']
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def collect_posts(self, max_posts_per_subreddit: int = None) -> Dict[str, int]:
        """
        Collect recent posts from configured subreddits
        
        Args:
            max_posts_per_subreddit: Maximum posts to collect per subreddit
            
        Returns:
            Dictionary with collection statistics
        """
        if max_posts_per_subreddit is None:
            max_posts_per_subreddit = self.settings['posts_per_subreddit']
        
        stats = {
            'new_posts': 0,
            'updated_posts': 0,
            'skipped_posts': 0,
            'subreddits_processed': 0,
            'errors': []
        }
        
        # Get last collection time for incremental collection
        last_collection = self._get_last_collection_time()
        
        for subreddit_config in self.subreddits:
            try:
                subreddit_name = subreddit_config['name']
                self.logger.info(f"📋 Collecting from r/{subreddit_name}...")
                
                subreddit_stats = self._collect_from_subreddit(
                    subreddit_config, 
                    max_posts_per_subreddit,
                    last_collection
                )
                
                stats['new_posts'] += subreddit_stats['new']
                stats['updated_posts'] += subreddit_stats['updated']
                stats['skipped_posts'] += subreddit_stats['skipped']
                stats['subreddits_processed'] += 1
                
                self.logger.info(f"✅ r/{subreddit_name}: {subreddit_stats['new']} new, {subreddit_stats['updated']} updated")
                
            except Exception as e:
                error_msg = f"Error collecting from r/{subreddit_config['name']}: {str(e)}"
                self.logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Update collection state
        self._update_collection_state(stats)
        
        return stats
    
    def _collect_from_subreddit(self, subreddit_config: Dict, max_posts: int, since: datetime) -> Dict[str, int]:
        """Collect posts from a single subreddit"""
        subreddit_name = subreddit_config['name']
        
        stats = {'new': 0, 'updated': 0, 'skipped': 0}
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get hot posts from the subreddit
            posts = subreddit.hot(limit=max_posts)
            
            for submission in posts:
                try:
                    # Check if post is too old
                    post_date = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                    
                    if since and post_date < since:
                        stats['skipped'] += 1
                        continue
                    
                    # Check minimum score threshold
                    min_score = self.settings.get('min_score', 5)
                    if submission.score < min_score:
                        stats['skipped'] += 1
                        continue
                    
                    # Create post document
                    post_doc = self._create_post_document(submission, subreddit_config)
                    
                    # Check if post already exists
                    existing_post = self.posts_collection.find_one({'reddit_id': submission.id})
                    
                    if existing_post:
                        # Update existing post
                        self.posts_collection.update_one(
                            {'reddit_id': submission.id},
                            {'$set': post_doc}
                        )
                        stats['updated'] += 1
                    else:
                        # Insert new post
                        post_doc['created_at'] = datetime.now(timezone.utc)
                        self.posts_collection.insert_one(post_doc)
                        stats['new'] += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing post {submission.id}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error accessing r/{subreddit_name}: {e}")
            raise
        
        return stats
    
    def _create_post_document(self, submission, subreddit_config: Dict) -> Dict[str, Any]:
        """Create MongoDB document from Reddit submission"""
        
        # Get comments if configured
        comments = []
        if self.settings.get('include_comments', False):
            max_comments = self.settings.get('max_comments_per_post', 10)
            try:
                submission.comments.replace_more(limit=0)  # Remove "more comments" objects
                for comment in submission.comments.list()[:max_comments]:
                    if hasattr(comment, 'body') and comment.body != '[deleted]' and comment.body != '[removed]':
                        comments.append({
                            'id': comment.id,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'body': comment.body,
                            'score': comment.score,
                            'created_utc': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
                            'permalink': f"https://reddit.com{comment.permalink}"
                        })
            except Exception as e:
                self.logger.warning(f"Error getting comments for {submission.id}: {e}")
        
        # Extract URLs from post
        urls = []
        if submission.url and not submission.url.startswith('https://www.reddit.com'):
            urls.append(submission.url)
        
        # Parse selftext for URLs if it's a text post
        if submission.selftext and 'http' in submission.selftext:
            import re
            found_urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', submission.selftext)
            urls.extend(found_urls)
        
        doc = {
            'reddit_id': submission.id,
            'title': submission.title,
            'selftext': submission.selftext or '',
            'author': str(submission.author) if submission.author else '[deleted]',
            'subreddit': submission.subreddit.display_name,
            'subreddit_config': subreddit_config,
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'created_utc': datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            'permalink': f"https://reddit.com{submission.permalink}",
            'url': submission.url,
            'urls': list(set(urls)),  # Remove duplicates
            'is_self': submission.is_self,
            'is_video': submission.is_video,
            'over_18': submission.over_18,
            'spoiler': submission.spoiler,
            'stickied': submission.stickied,
            'distinguished': submission.distinguished,
            'gilded': getattr(submission, 'gilded', 0),
            'comments': comments,
            'updated_at': datetime.now(timezone.utc),
            # Fields for compatibility with existing systems
            'tags': [],
            'processed': False,
            'content_type': 'reddit_post'
        }
        
        return doc
    
    def _get_last_collection_time(self) -> Optional[datetime]:
        """Get the last successful collection time"""
        state = self.collection_state.find_one({'collector': 'reddit'})
        if state and 'last_collection' in state:
            return state['last_collection']
        return None
    
    def _update_collection_state(self, stats: Dict):
        """Update collection state with latest statistics"""
        state_doc = {
            'collector': 'reddit',
            'last_collection': datetime.now(timezone.utc),
            'stats': stats,
            'subreddits_count': len(self.subreddits),
            'total_posts': self.posts_collection.count_documents({})
        }
        
        self.collection_state.update_one(
            {'collector': 'reddit'},
            {'$set': state_doc},
            upsert=True
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get current collection statistics"""
        total_posts = self.posts_collection.count_documents({})
        
        # Posts by subreddit
        pipeline = [
            {'$group': {'_id': '$subreddit', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        by_subreddit = list(self.posts_collection.aggregate(pipeline))
        
        # Recent posts (last 24 hours)
        since_yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_posts = self.posts_collection.count_documents({
            'created_utc': {'$gte': since_yesterday}
        })
        
        # Get last collection state
        state = self.collection_state.find_one({'collector': 'reddit'})
        
        return {
            'total_posts': total_posts,
            'posts_by_subreddit': by_subreddit,
            'recent_posts_24h': recent_posts,
            'subreddits_monitored': len(self.subreddits),
            'last_collection': state.get('last_collection') if state else None,
            'last_collection_stats': state.get('stats') if state else None
        }

# Standalone collection script
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        collector = RedditCollector()
        
        print("🔍 Starting Reddit collection...")
        print(f"📋 Monitoring {len(collector.subreddits)} subreddits:")
        for sub in collector.subreddits:
            print(f"  - r/{sub['name']} ({sub['category']})")
        
        # Collect posts
        stats = collector.collect_posts()
        
        print(f"\n✅ Collection complete:")
        print(f"  📊 New posts: {stats['new_posts']}")
        print(f"  🔄 Updated posts: {stats['updated_posts']}")
        print(f"  ⏭️  Skipped posts: {stats['skipped_posts']}")
        print(f"  📁 Subreddits processed: {stats['subreddits_processed']}")
        
        if stats['errors']:
            print(f"  ❌ Errors: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"    - {error}")
        
        # Show overall stats
        overall_stats = collector.get_collection_stats()
        print(f"\n📈 Overall Statistics:")
        print(f"  Total posts in database: {overall_stats['total_posts']}")
        print(f"  Posts in last 24h: {overall_stats['recent_posts_24h']}")
        
        print(f"\n📋 Posts by subreddit:")
        for sub_stats in overall_stats['posts_by_subreddit']:
            print(f"  r/{sub_stats['_id']}: {sub_stats['count']} posts")
        
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        sys.exit(1)
