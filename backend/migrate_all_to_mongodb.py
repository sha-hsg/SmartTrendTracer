#!/usr/bin/env python3
"""
Complete migration from SQLite to MongoDB
Migrates all remaining data: papers, analyses, references, authors, sections, entities
"""
import sqlite3
import sys
from pymongo import MongoClient
from datetime import datetime, timezone
import json
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLiteToMongoMigration:
    def __init__(self):
        # MongoDB connection
        self.mongo_client = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo_client.smarttrendtracer
        
        # SQLite connection
        self.sqlite_conn = sqlite3.connect('data/tweets.db')
        self.sqlite_conn.row_factory = sqlite3.Row
        
        logger.info("Connected to MongoDB and SQLite")
    
    def migrate_papers_complete(self):
        """Migrate papers with all embedded data"""
        logger.info("Migrating papers with embedded analyses, references, sections...")
        
        # Get papers from SQLite
        papers_cursor = self.sqlite_conn.execute("""
            SELECT * FROM papers ORDER BY id
        """)
        
        migrated_count = 0
        updated_count = 0
        
        for paper_row in papers_cursor:
            paper_id = paper_row['id']
            
            # Check if paper already exists in MongoDB
            existing_paper = self.db.papers.find_one({'old_sqlite_id': paper_id})
            
            # Prepare paper document
            paper_doc = {
                'old_sqlite_id': paper_id,
                'title': paper_row['title'],
                'abstract': paper_row['abstract'],
                'content': paper_row['content'],
                'pdf_path': paper_row['pdf_path'],
                'pdf_url': paper_row['pdf_url'],
                'arxiv_id': paper_row['arxiv_id'],
                'doi': paper_row['doi'],
                'publication_date': paper_row['publication_date'],
                'published_date': paper_row['published_date'],
                'conference': paper_row['conference'],
                'journal': paper_row['journal'],
                'citation_count': paper_row['citation_count'],
                'page_count': paper_row['page_count'],
                'word_count': paper_row['word_count'],
                'language': paper_row['language'],
                'categories': paper_row['categories'],
                'authors': paper_row['authors'],
                'processor_used': paper_row['processor_used'],
                'processing_error': paper_row['processing_error'],
                'is_flagged': bool(paper_row['is_flagged']),
                'flag_notes': paper_row['flag_notes'],
                'dblp_key': paper_row['dblp_key'],
                'dblp_url': paper_row['dblp_url'],
                'bibtex': paper_row['bibtex'],
                'processed': bool(paper_row['processed']),
                'created_at': self.parse_datetime(paper_row['created_at']),
                'updated_at': self.parse_datetime(paper_row['updated_at']),
            }
            
            # Get analyses
            analyses = self.get_paper_analyses(paper_id)
            if analyses:
                paper_doc['analyses'] = analyses
                
            # Get references
            references = self.get_paper_references(paper_id)
            if references:
                paper_doc['references'] = references
                
            # Get sections
            sections = self.get_paper_sections(paper_id)
            if sections:
                paper_doc['sections'] = sections
                
            # Get authors (separate table)
            authors_detailed = self.get_paper_authors(paper_id)
            if authors_detailed:
                paper_doc['authors_detailed'] = authors_detailed
                
            # Get snippets
            snippets = self.get_paper_snippets(paper_id)
            if snippets:
                paper_doc['snippets'] = snippets
                
            # Get concept_ids from tag_instances
            concept_ids = self.get_content_concepts(paper_id, 'paper')
            if concept_ids:
                paper_doc['concept_ids'] = concept_ids
            
            if existing_paper:
                # Update existing paper
                self.db.papers.update_one(
                    {'_id': existing_paper['_id']},
                    {'$set': paper_doc}
                )
                updated_count += 1
                if updated_count % 10 == 0:
                    logger.info(f"Updated {updated_count} papers...")
            else:
                # Insert new paper
                self.db.papers.insert_one(paper_doc)
                migrated_count += 1
                if migrated_count % 10 == 0:
                    logger.info(f"Migrated {migrated_count} papers...")
        
        logger.info(f"Papers migration complete: {migrated_count} new, {updated_count} updated")
    
    def migrate_substack_articles_complete(self):
        """Migrate Substack articles with embedded data"""
        logger.info("Migrating Substack articles with embedded snippets...")
        
        articles_cursor = self.sqlite_conn.execute("""
            SELECT a.*, auth.name as author_name, auth.email as author_email
            FROM substack_articles a
            LEFT JOIN substack_authors auth ON a.author_id = auth.id
            ORDER BY a.id
        """)
        
        migrated_count = 0
        updated_count = 0
        
        for article_row in articles_cursor:
            article_id = article_row['id']
            
            # Check if article already exists
            existing_article = self.db.articles.find_one({'old_sqlite_id': article_id})
            
            # Prepare article document
            article_doc = {
                'old_sqlite_id': article_id,
                'substack_id': article_row['substack_id'],
                'title': article_row['title'],
                'subtitle': article_row['subtitle'],
                'slug': article_row['slug'],
                'content_html': article_row['content_html'],
                'content_markdown': article_row['content_markdown'],
                'preview': article_row['preview'],
                'url': article_row['url'],
                'published_at': self.parse_datetime(article_row['published_at']),
                'collected_at': self.parse_datetime(article_row['collected_at']),
                'word_count': article_row['word_count'],
                'reading_time_minutes': article_row['reading_time_minutes'],
                'likes': article_row['likes'],
                'comments': article_row['comments'],
                'processed': bool(article_row['processed']) if article_row['processed'] is not None else False,
                'summarized': bool(article_row['summarized']) if article_row['summarized'] is not None else False,
                'summary': article_row['summary'],
                'key_points': json.loads(article_row['key_points']) if article_row['key_points'] else None,
                'topics': json.loads(article_row['topics']) if article_row['topics'] else None,
                'sentiment': article_row['sentiment'],
                'author_id': article_row['author_id'],
                'author_name': article_row['author_name'],
                'author_email': article_row['author_email'],
                'deleted': bool(article_row['deleted']) if article_row['deleted'] is not None else False,
            }
            
            # Get snippets
            snippets = self.get_article_snippets(article_id)
            if snippets:
                article_doc['snippets'] = snippets
                
            # Get concept_ids
            concept_ids = self.get_content_concepts(article_id, 'article')
            if concept_ids:
                article_doc['concept_ids'] = concept_ids
            
            if existing_article:
                self.db.articles.update_one(
                    {'_id': existing_article['_id']},
                    {'$set': article_doc}
                )
                updated_count += 1
            else:
                self.db.articles.insert_one(article_doc)
                migrated_count += 1
        
        logger.info(f"Articles migration complete: {migrated_count} new, {updated_count} updated")
    
    def migrate_extracted_entities(self):
        """Migrate extracted entities as a separate collection"""
        logger.info("Migrating extracted entities...")
        
        entities_cursor = self.sqlite_conn.execute("""
            SELECT * FROM extracted_entities ORDER BY id
        """)
        
        # Clear existing entities
        self.db.extracted_entities.delete_many({})
        
        entities = []
        for entity_row in entities_cursor:
            entity_doc = {
                'old_sqlite_id': entity_row['id'],
                'tweet_id': entity_row['tweet_id'],
                'subject': entity_row['subject'],
                'predicate': entity_row['predicate'],
                'object': entity_row['object'],
                'confidence': entity_row['confidence'],
                'extraction_method': entity_row['extraction_method'],
                'created_at': self.parse_datetime(entity_row['created_at'])
            }
            entities.append(entity_doc)
            
            # Batch insert every 1000 entities
            if len(entities) >= 1000:
                self.db.extracted_entities.insert_many(entities)
                entities = []
                logger.info(f"Inserted batch of entities...")
        
        # Insert remaining entities
        if entities:
            self.db.extracted_entities.insert_many(entities)
        
        total_entities = self.db.extracted_entities.count_documents({})
        logger.info(f"Entities migration complete: {total_entities} entities")
    
    def get_paper_analyses(self, paper_id):
        """Get all analyses for a paper"""
        cursor = self.sqlite_conn.execute("""
            SELECT * FROM paper_analyses 
            WHERE paper_id = ? 
            ORDER BY created_at DESC
        """, (paper_id,))
        
        analyses = []
        for row in cursor:
            analysis = {
                'old_sqlite_id': row['id'],
                'analysis_type': row['analysis_type'],
                'analysis_name': row['analysis_name'],
                'prompt_used': row['prompt_used'],
                'content': row['content'],
                'model_used': row['model_used'],
                'model_parameters': json.loads(row['model_parameters']) if row['model_parameters'] else None,
                'confidence_score': row['confidence_score'],
                'word_count': row['word_count'],
                'version': row['version'],
                'is_latest': bool(row['is_latest']),
                'user_rating': row['user_rating'],
                'user_notes': row['user_notes'],
                'generated_at': self.parse_datetime(row['generated_at']),
                'created_at': self.parse_datetime(row['created_at']),
                'updated_at': self.parse_datetime(row['updated_at'])
            }
            analyses.append(analysis)
        
        return analyses
    
    def get_paper_references(self, paper_id):
        """Get all references for a paper"""
        cursor = self.sqlite_conn.execute("""
            SELECT * FROM paper_references 
            WHERE paper_id = ? 
            ORDER BY id
        """, (paper_id,))
        
        references = []
        for row in cursor:
            reference = {
                'old_sqlite_id': row['id'],
                'cited_paper_id': row['cited_paper_id'],
                'raw_citation': row['raw_citation'],
                'title': row['title'],
                'authors': row['authors'],
                'year': row['year'],
                'venue': row['venue'],
                'doi': row['doi']
            }
            references.append(reference)
        
        return references
    
    def get_paper_sections(self, paper_id):
        """Get all sections for a paper"""
        cursor = self.sqlite_conn.execute("""
            SELECT * FROM paper_sections 
            WHERE paper_id = ? 
            ORDER BY position
        """, (paper_id,))
        
        sections = []
        for row in cursor:
            section = {
                'old_sqlite_id': row['id'],
                'section_type': row['section_type'],
                'title': row['title'],
                'content': row['content'],
                'position': row['position'],
                'page_start': row['page_start'],
                'page_end': row['page_end']
            }
            sections.append(section)
        
        return sections
    
    def get_paper_authors(self, paper_id):
        """Get detailed authors for a paper"""
        cursor = self.sqlite_conn.execute("""
            SELECT * FROM paper_authors 
            WHERE paper_id = ? 
            ORDER BY position
        """, (paper_id,))
        
        authors = []
        for row in cursor:
            author = {
                'old_sqlite_id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'affiliation': row['affiliation'],
                'position': row['position'],
                'is_corresponding': bool(row['is_corresponding'])
            }
            authors.append(author)
        
        return authors
    
    def get_paper_snippets(self, paper_id):
        """Get all snippets for a paper"""
        cursor = self.sqlite_conn.execute("""
            SELECT * FROM paper_snippets 
            WHERE paper_id = ? 
            ORDER BY created_at
        """, (paper_id,))
        
        snippets = []
        for row in cursor:
            snippet = {
                'old_sqlite_id': row['id'],
                'text': row['text'],
                'page_number': row['page_number'],
                'annotation': row['annotation'],
                'category': row['category'],
                'importance': row['importance'],
                'created_at': self.parse_datetime(row['created_at'])
            }
            snippets.append(snippet)
        
        return snippets
    
    def get_article_snippets(self, article_id):
        """Get all snippets for a Substack article"""
        cursor = self.sqlite_conn.execute("""
            SELECT * FROM article_snippets 
            WHERE article_id = ? 
            ORDER BY created_at
        """, (article_id,))
        
        snippets = []
        for row in cursor:
            snippet = {
                'old_sqlite_id': row['id'],
                'text': row['text'],
                'annotation': row['annotation'],
                'category': row['category'],
                'importance': row['importance'],
                'created_at': self.parse_datetime(row['created_at'])
            }
            snippets.append(snippet)
        
        return snippets
    
    def get_content_concepts(self, content_id, content_type):
        """Get concept IDs for content from tag_instances"""
        cursor = self.sqlite_conn.execute("""
            SELECT concept_id FROM tag_instances 
            WHERE content_id = ? AND content_type = ?
        """, (str(content_id), content_type))
        
        concept_ids = [row[0] for row in cursor if row[0]]
        return concept_ids
    
    def parse_datetime(self, dt_str):
        """Parse datetime string to datetime object"""
        if not dt_str:
            return None
            
        try:
            # Try different datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            logger.warning(f"Could not parse datetime: {dt_str}")
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_str}: {e}")
            return datetime.now()
    
    def create_indexes(self):
        """Create indexes for better performance"""
        logger.info("Creating MongoDB indexes...")
        
        # Helper function to safely create index
        def safe_create_index(collection, index_spec, name=None):
            try:
                if name:
                    collection.create_index(index_spec, name=name)
                else:
                    collection.create_index(index_spec)
                logger.info(f"Created index {index_spec} on {collection.name}")
            except Exception as e:
                if "already exists" in str(e) or "IndexKeySpecsConflict" in str(e):
                    logger.info(f"Index {index_spec} on {collection.name} already exists, skipping")
                else:
                    logger.warning(f"Failed to create index {index_spec} on {collection.name}: {e}")
        
        # Papers indexes
        safe_create_index(self.db.papers, [("title", "text")])
        safe_create_index(self.db.papers, [("doi", 1)], "doi_unique")
        safe_create_index(self.db.papers, [("arxiv_id", 1)], "arxiv_id_unique")
        safe_create_index(self.db.papers, [("old_sqlite_id", 1)], "old_sqlite_id_unique")
        safe_create_index(self.db.papers, [("dblp_key", 1)], "dblp_key_unique")
        
        # Articles indexes
        safe_create_index(self.db.articles, [("title", "text")])
        safe_create_index(self.db.articles, [("old_sqlite_id", 1)], "articles_old_sqlite_id")
        safe_create_index(self.db.articles, [("published_at", -1)], "articles_published_at")
        
        # Entities indexes
        safe_create_index(self.db.extracted_entities, [("tweet_id", 1)], "entities_tweet_id")
        safe_create_index(self.db.extracted_entities, [("subject", 1)], "entities_subject")
        
        logger.info("Index creation completed")
    
    def run_full_migration(self):
        """Run the complete migration"""
        logger.info("Starting complete SQLite to MongoDB migration...")
        
        try:
            # Migrate papers with all embedded data
            self.migrate_papers_complete()
            
            # Migrate Substack articles
            self.migrate_substack_articles_complete()
            
            # Migrate extracted entities
            self.migrate_extracted_entities()
            
            # Create indexes
            self.create_indexes()
            
            logger.info("✅ Migration completed successfully!")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.sqlite_conn.close()
            self.mongo_client.close()
    
    def print_summary(self):
        """Print migration summary"""
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        
        # Count MongoDB collections
        collections = {
            'papers': self.db.papers.count_documents({}),
            'articles': self.db.articles.count_documents({}),
            'extracted_entities': self.db.extracted_entities.count_documents({}),
            'tweets': self.db.tweets.count_documents({}),
            'tag_concepts_v2': self.db.tag_concepts_v2.count_documents({}),
            'tag_instances': self.db.tag_instances.count_documents({}),
        }
        
        for collection, count in collections.items():
            logger.info(f"{collection:20}: {count:,} documents")
        
        total_docs = sum(collections.values())
        logger.info(f"{'TOTAL':20}: {total_docs:,} documents")
        logger.info("="*60)

if __name__ == "__main__":
    migration = SQLiteToMongoMigration()
    migration.run_full_migration()