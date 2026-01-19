#!/usr/bin/env python3
"""
Complete SQLite to MongoDB Migration Script
Migrates all data from SQLite to MongoDB for SmartTrendTracer
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient, ASCENDING, TEXT
from bson import ObjectId
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SQLiteToMongoDBMigrator:
    def __init__(self, sqlite_path: str = "data/tweets.db", mongodb_url: str = "mongodb://localhost:27017/"):
        """Initialize the migrator with database connections"""
        self.sqlite_path = sqlite_path
        self.mongodb_url = mongodb_url
        
        # Connect to SQLite
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        self.cursor = self.sqlite_conn.cursor()
        
        # Connect to MongoDB
        self.mongo_client = MongoClient(mongodb_url)
        self.mongo_db = self.mongo_client.smarttrendtracer
        
        # Track migration stats
        self.stats = {
            'tweets': 0,
            'papers': 0,
            'articles': 0,
            'media': 0,
            'authors': 0,
            'snippets': 0,
            'errors': []
        }
    
    def create_mongodb_collections(self):
        """Create MongoDB collections with proper indexes"""
        logger.info("Creating MongoDB collections and indexes...")
        
        # Drop existing collections for clean migration
        collections_to_drop = ['tweets', 'papers', 'articles', 'tweet_media', 
                              'paper_authors', 'paper_sections', 'paper_references',
                              'article_snippets', 'paper_snippets', 'substack_authors']
        
        for coll in collections_to_drop:
            if coll in self.mongo_db.list_collection_names():
                self.mongo_db[coll].drop()
                logger.info(f"Dropped existing collection: {coll}")
        
        # Create collections with indexes
        
        # Tweets collection
        tweets = self.mongo_db.tweets
        # Don't create unique index on 'id' field since we use _id
        tweets.create_index([("author_username", ASCENDING)])
        tweets.create_index([("created_at", ASCENDING)])
        tweets.create_index([("text", TEXT)])
        
        # Papers collection
        papers = self.mongo_db.papers
        papers.create_index([("title", TEXT)])
        papers.create_index([("arxiv_id", ASCENDING)], sparse=True)
        papers.create_index([("doi", ASCENDING)], sparse=True)
        papers.create_index([("created_at", ASCENDING)])
        
        # Articles collection
        articles = self.mongo_db.articles
        articles.create_index([("substack_id", ASCENDING)], unique=True, sparse=True)
        articles.create_index([("author_id", ASCENDING)])
        articles.create_index([("published_at", ASCENDING)])
        articles.create_index([("title", TEXT)])
        
        logger.info("Collections and indexes created successfully")
    
    def migrate_tweets(self):
        """Migrate tweets and their media"""
        logger.info("Migrating tweets...")
        
        # Get all tweets
        self.cursor.execute("""
            SELECT t.*, 
                   GROUP_CONCAT(tm.media_key || ':::' || tm.type || ':::' || 
                               COALESCE(tm.url, '') || ':::' || 
                               COALESCE(tm.preview_image_url, '') || ':::' ||
                               COALESCE(tm.alt_text, '') || ':::' ||
                               COALESCE(tm.width, 0) || ':::' ||
                               COALESCE(tm.height, 0) || ':::' ||
                               COALESCE(tm.duration_ms, 0), '|||') as media_data
            FROM tweets t
            LEFT JOIN tweet_media tm ON t.id = tm.tweet_id
            GROUP BY t.id
        """)
        
        tweets = self.cursor.fetchall()
        tweet_docs = []
        
        for tweet in tweets:
            try:
                # Parse media
                media = []
                if tweet['media_data']:
                    for media_item in tweet['media_data'].split('|||'):
                        if media_item and ':::' in media_item:
                            parts = media_item.split(':::')
                            if len(parts) >= 8:
                                media.append({
                                    'media_key': parts[0],
                                    'type': parts[1],
                                    'url': parts[2] if parts[2] != '' else None,
                                    'preview_image_url': parts[3] if parts[3] != '' else None,
                                    'alt_text': parts[4] if parts[4] != '' else None,
                                    'width': int(parts[5]) if parts[5] and parts[5] != '0' else None,
                                    'height': int(parts[6]) if parts[6] and parts[6] != '0' else None,
                                    'duration_ms': int(parts[7]) if parts[7] and parts[7] != '0' else None
                                })
                
                # Get concept IDs from tag_instances
                self.cursor.execute("""
                    SELECT DISTINCT concept_id 
                    FROM tag_instances 
                    WHERE content_type = 'tweet' AND content_id = ? AND deleted = 0
                """, (tweet['id'],))
                concept_rows = self.cursor.fetchall()
                concept_ids = [row['concept_id'] for row in concept_rows if row['concept_id']]
                
                # Convert to MongoDB concept IDs (they're stored in MongoDB already)
                mongo_concept_ids = []
                for concept_id in concept_ids:
                    # Check if it's numeric (old SQLite concept) or string (MongoDB concept)
                    if isinstance(concept_id, int):
                        # Look up the MongoDB concept by old SQLite ID
                        mongo_concept = self.mongo_db.tag_concepts_v2.find_one({'old_sqlite_id': concept_id})
                        if mongo_concept:
                            mongo_concept_ids.append(str(mongo_concept['_id']))
                    else:
                        mongo_concept_ids.append(str(concept_id))
                
                # Create tweet document
                tweet_doc = {
                    '_id': tweet['id'],  # Use Twitter ID as MongoDB _id
                    'text': tweet['text'],
                    'author_id': tweet['author_id'],
                    'author_username': tweet['author_username'],
                    'author_name': tweet['author_name'],
                    'created_at': datetime.fromisoformat(tweet['created_at']) if tweet['created_at'] else None,
                    'collected_at': datetime.fromisoformat(tweet['collected_at']) if tweet['collected_at'] else None,
                    'processed': bool(tweet['processed']),
                    'metrics': {
                        'retweet_count': tweet['retweet_count'] or 0,
                        'like_count': tweet['like_count'] or 0,
                        'reply_count': tweet['reply_count'] or 0,
                        'quote_count': tweet['quote_count'] or 0
                    },
                    'hashtags': json.loads(tweet['hashtags']) if tweet['hashtags'] else [],
                    'mentions': json.loads(tweet['mentions']) if tweet['mentions'] else [],
                    'urls': json.loads(tweet['urls']) if tweet['urls'] else [],
                    'referenced_tweets': json.loads(tweet['referenced_tweets']) if tweet['referenced_tweets'] else [],
                    'media': media,
                    'media_count': len(media),
                    'concept_ids': mongo_concept_ids
                }
                
                tweet_docs.append(tweet_doc)
                
            except Exception as e:
                logger.error(f"Error processing tweet {tweet['id']}: {e}")
                self.stats['errors'].append(f"Tweet {tweet['id']}: {e}")
        
        # Bulk insert tweets
        if tweet_docs:
            try:
                result = self.mongo_db.tweets.insert_many(tweet_docs, ordered=False)
                self.stats['tweets'] = len(result.inserted_ids)
                logger.info(f"Migrated {len(result.inserted_ids)} tweets")
            except Exception as e:
                logger.error(f"Error bulk inserting tweets: {e}")
                # Try inserting one by one
                for doc in tweet_docs:
                    try:
                        self.mongo_db.tweets.insert_one(doc)
                        self.stats['tweets'] += 1
                    except Exception as e2:
                        logger.error(f"Error inserting tweet {doc['_id']}: {e2}")
    
    def migrate_papers(self):
        """Migrate papers and related data"""
        logger.info("Migrating papers...")
        
        # Get all papers
        self.cursor.execute("SELECT * FROM papers")
        papers = self.cursor.fetchall()
        
        for paper in papers:
            try:
                paper_id = paper['id']
                
                # Get authors
                self.cursor.execute("""
                    SELECT * FROM paper_authors 
                    WHERE paper_id = ? 
                    ORDER BY position
                """, (paper_id,))
                authors = [dict(row) for row in self.cursor.fetchall()]
                
                # Get sections
                self.cursor.execute("""
                    SELECT * FROM paper_sections 
                    WHERE paper_id = ? 
                    ORDER BY position
                """, (paper_id,))
                sections = [dict(row) for row in self.cursor.fetchall()]
                
                # Get references
                self.cursor.execute("""
                    SELECT * FROM paper_references 
                    WHERE paper_id = ?
                """, (paper_id,))
                references = [dict(row) for row in self.cursor.fetchall()]
                
                # Get snippets
                self.cursor.execute("""
                    SELECT * FROM paper_snippets 
                    WHERE paper_id = ?
                """, (paper_id,))
                snippets = [dict(row) for row in self.cursor.fetchall()]
                
                # Get analyses
                self.cursor.execute("""
                    SELECT * FROM paper_analyses 
                    WHERE paper_id = ?
                """, (paper_id,))
                analyses = [dict(row) for row in self.cursor.fetchall()]
                
                # Get repository info
                self.cursor.execute("""
                    SELECT * FROM paper_repository 
                    WHERE paper_id = ?
                """, (paper_id,))
                repo_info = self.cursor.fetchone()
                
                # Get concept IDs
                self.cursor.execute("""
                    SELECT DISTINCT concept_id 
                    FROM tag_instances 
                    WHERE content_type = 'paper' AND content_id = ? AND deleted = 0
                """, (str(paper_id),))
                concept_rows = self.cursor.fetchall()
                concept_ids = []
                for row in concept_rows:
                    if row['concept_id']:
                        # Convert to string if needed
                        concept_ids.append(str(row['concept_id']))
                
                # Create paper document
                paper_doc = {
                    '_id': ObjectId(),
                    'old_sqlite_id': paper_id,
                    'title': paper['title'],
                    'abstract': paper['abstract'],
                    'content': paper['content'],
                    'pdf_path': paper['pdf_path'],
                    'pdf_url': paper['pdf_url'],
                    'arxiv_id': paper['arxiv_id'],
                    'doi': paper['doi'],
                    'publication_date': paper['publication_date'],
                    'published_date': paper['published_date'],
                    'conference': paper['conference'],
                    'journal': paper['journal'],
                    'citation_count': paper['citation_count'] or 0,
                    'page_count': paper['page_count'] or 0,
                    'word_count': paper['word_count'] or 0,
                    'language': paper['language'] or 'en',
                    'categories': json.loads(paper['categories']) if paper['categories'] else [],
                    'authors': authors,
                    'sections': sections,
                    'references': references,
                    'snippets': snippets,
                    'analyses': analyses,
                    'repository': dict(repo_info) if repo_info else None,
                    'processor_used': paper['processor_used'],
                    'processing_error': paper['processing_error'],
                    'is_flagged': bool(paper['is_flagged']),
                    'flag_notes': paper['flag_notes'],
                    'dblp_key': paper['dblp_key'],
                    'dblp_url': paper['dblp_url'],
                    'bibtex': paper['bibtex'],
                    'processed': bool(paper['processed']),
                    'concept_ids': concept_ids,
                    'created_at': datetime.fromisoformat(paper['created_at']) if paper['created_at'] else datetime.now(),
                    'updated_at': datetime.fromisoformat(paper['updated_at']) if paper['updated_at'] else None
                }
                
                # Insert paper
                result = self.mongo_db.papers.insert_one(paper_doc)
                self.stats['papers'] += 1
                
                # Update tag_instances with new MongoDB paper ID
                if concept_ids:
                    self.mongo_db.tag_instances.update_many(
                        {'content_type': 'paper', 'content_id': str(paper_id)},
                        {'$set': {'content_id': str(result.inserted_id)}}
                    )
                
            except Exception as e:
                logger.error(f"Error migrating paper {paper_id}: {e}")
                self.stats['errors'].append(f"Paper {paper_id}: {e}")
        
        logger.info(f"Migrated {self.stats['papers']} papers")
    
    def migrate_articles(self):
        """Migrate Substack articles and related data"""
        logger.info("Migrating articles...")
        
        # First migrate authors
        self.cursor.execute("SELECT * FROM substack_authors")
        authors = self.cursor.fetchall()
        author_map = {}  # Map old ID to new MongoDB ID
        
        for author in authors:
            try:
                author_doc = {
                    '_id': ObjectId(),
                    'old_sqlite_id': author['id'],
                    'subdomain': author['subdomain'],
                    'name': author['name'],
                    'description': author['description'],
                    'url': author['url'],
                    'email': author['email'],
                    'created_at': datetime.fromisoformat(author['created_at']) if author['created_at'] else datetime.now(),
                    'updated_at': datetime.fromisoformat(author['updated_at']) if author['updated_at'] else None
                }
                
                result = self.mongo_db.substack_authors.insert_one(author_doc)
                author_map[author['id']] = result.inserted_id
                self.stats['authors'] += 1
                
            except Exception as e:
                logger.error(f"Error migrating author {author['id']}: {e}")
        
        # Now migrate articles
        self.cursor.execute("SELECT * FROM substack_articles")
        articles = self.cursor.fetchall()
        
        for article in articles:
            try:
                article_id = article['id']
                
                # Get snippets
                self.cursor.execute("""
                    SELECT * FROM article_snippets 
                    WHERE article_id = ?
                """, (article_id,))
                snippets = [dict(row) for row in self.cursor.fetchall()]
                
                # Get concept IDs
                self.cursor.execute("""
                    SELECT DISTINCT concept_id 
                    FROM tag_instances 
                    WHERE content_type = 'article' AND content_id = ? AND deleted = 0
                """, (str(article_id),))
                concept_rows = self.cursor.fetchall()
                concept_ids = []
                for row in concept_rows:
                    if row['concept_id']:
                        concept_ids.append(str(row['concept_id']))
                
                # Create article document
                article_doc = {
                    '_id': ObjectId(),
                    'old_sqlite_id': article_id,
                    'substack_id': article['substack_id'],
                    'title': article['title'],
                    'subtitle': article['subtitle'],
                    'slug': article['slug'],
                    'url': article['url'],
                    'content_html': article['content_html'],
                    'content_markdown': article['content_markdown'],
                    'preview': article['preview'],
                    'word_count': article['word_count'] or 0,
                    'reading_time_minutes': article['reading_time_minutes'] or 0,
                    'author_id': author_map.get(article['author_id']),
                    'author_sqlite_id': article['author_id'],  # Keep for reference
                    'published_at': datetime.fromisoformat(article['published_at']) if article['published_at'] else None,
                    'collected_at': datetime.fromisoformat(article['collected_at']) if article['collected_at'] else None,
                    'metrics': {
                        'likes': article['likes'] or 0,
                        'comments': article['comments'] or 0
                    },
                    'processed': bool(article['processed']),
                    'summarized': bool(article['summarized']),
                    'deleted': bool(article['deleted']),
                    'summary': article['summary'],
                    'key_points': json.loads(article['key_points']) if article['key_points'] else [],
                    'topics': json.loads(article['topics']) if article['topics'] else [],
                    'sentiment': article['sentiment'],
                    'snippets': snippets,
                    'concept_ids': concept_ids
                }
                
                # Insert article
                result = self.mongo_db.articles.insert_one(article_doc)
                self.stats['articles'] += 1
                
                # Update tag_instances with new MongoDB article ID
                if concept_ids:
                    self.mongo_db.tag_instances.update_many(
                        {'content_type': 'article', 'content_id': str(article_id)},
                        {'$set': {'content_id': str(result.inserted_id)}}
                    )
                
            except Exception as e:
                logger.error(f"Error migrating article {article_id}: {e}")
                self.stats['errors'].append(f"Article {article_id}: {e}")
        
        logger.info(f"Migrated {self.stats['articles']} articles and {self.stats['authors']} authors")
    
    def verify_migration(self):
        """Verify the migration was successful"""
        logger.info("\n=== Migration Verification ===")
        
        # Count records in MongoDB
        mongo_counts = {
            'tweets': self.mongo_db.tweets.count_documents({}),
            'papers': self.mongo_db.papers.count_documents({}),
            'articles': self.mongo_db.articles.count_documents({}),
            'authors': self.mongo_db.substack_authors.count_documents({}),
            'tag_instances': self.mongo_db.tag_instances.count_documents({})
        }
        
        # Count records in SQLite
        sqlite_counts = {}
        for table in ['tweets', 'papers', 'substack_articles', 'substack_authors']:
            self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            sqlite_counts[table] = self.cursor.fetchone()['count']
        
        logger.info("\nRecord counts comparison:")
        logger.info(f"Tweets: SQLite={sqlite_counts['tweets']}, MongoDB={mongo_counts['tweets']}")
        logger.info(f"Papers: SQLite={sqlite_counts['papers']}, MongoDB={mongo_counts['papers']}")
        logger.info(f"Articles: SQLite={sqlite_counts['substack_articles']}, MongoDB={mongo_counts['articles']}")
        logger.info(f"Authors: SQLite={sqlite_counts['substack_authors']}, MongoDB={mongo_counts['authors']}")
        
        # Sample data verification
        logger.info("\nSample data verification:")
        
        # Check a tweet
        sample_tweet = self.mongo_db.tweets.find_one()
        if sample_tweet:
            logger.info(f"Sample tweet: {sample_tweet['_id'][:50]}...")
            logger.info(f"  - Has media: {len(sample_tweet.get('media', []))} items")
            logger.info(f"  - Has concepts: {len(sample_tweet.get('concept_ids', []))} concepts")
        
        # Check a paper
        sample_paper = self.mongo_db.papers.find_one()
        if sample_paper:
            logger.info(f"Sample paper: {sample_paper['title'][:50]}...")
            logger.info(f"  - Has authors: {len(sample_paper.get('authors', []))} authors")
            logger.info(f"  - Has sections: {len(sample_paper.get('sections', []))} sections")
        
        # Check an article
        sample_article = self.mongo_db.articles.find_one()
        if sample_article:
            logger.info(f"Sample article: {sample_article['title'][:50]}...")
            logger.info(f"  - Has snippets: {len(sample_article.get('snippets', []))} snippets")
        
        if self.stats['errors']:
            logger.warning(f"\n{len(self.stats['errors'])} errors occurred during migration:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                logger.warning(f"  - {error}")
    
    def migrate_all(self):
        """Run the complete migration"""
        logger.info("Starting complete SQLite to MongoDB migration...")
        logger.info(f"SQLite database: {self.sqlite_path}")
        logger.info(f"MongoDB URL: {self.mongodb_url}")
        
        try:
            # Create collections and indexes
            self.create_mongodb_collections()
            
            # Migrate data
            self.migrate_tweets()
            self.migrate_papers()
            self.migrate_articles()
            
            # Verify migration
            self.verify_migration()
            
            logger.info("\n=== Migration Complete ===")
            logger.info(f"Tweets migrated: {self.stats['tweets']}")
            logger.info(f"Papers migrated: {self.stats['papers']}")
            logger.info(f"Articles migrated: {self.stats['articles']}")
            logger.info(f"Authors migrated: {self.stats['authors']}")
            logger.info(f"Total errors: {len(self.stats['errors'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        
        finally:
            # Close connections
            self.sqlite_conn.close()
            self.mongo_client.close()


def main():
    """Main migration function"""
    # Create backup of SQLite database
    import shutil
    from datetime import datetime
    
    backup_path = f"data/tweets.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy("data/tweets.db", backup_path)
    logger.info(f"Created SQLite backup: {backup_path}")
    
    # Run migration
    migrator = SQLiteToMongoDBMigrator()
    success = migrator.migrate_all()
    
    if success:
        logger.info("\n✅ Migration completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Update all API endpoints to use MongoDB")
        logger.info("2. Test all functionality")
        logger.info("3. Remove SQLite dependencies from requirements.txt")
    else:
        logger.error("\n❌ Migration failed! Check errors above.")
        logger.info(f"SQLite backup available at: {backup_path}")


if __name__ == "__main__":
    main()