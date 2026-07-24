"""
Author Management and Normalization Service

Provides intelligent author name normalization, multi-author parsing,
and fuzzy matching for the Articles system.
"""

import re
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher
from bson import ObjectId
from datetime import datetime, timezone


class AuthorService:
    """Service for managing and normalizing article authors"""

    def __init__(self, db):
        """Initialize with MongoDB database connection"""
        self.db = db
        self.authors_collection = db.substack_authors
        self.articles_collection = db.articles

    def normalize_name(self, name: str) -> str:
        """
        Normalize an author name by removing suffixes and extra whitespace.

        Examples:
            "Sebastian Raschka, PhD" → "Sebastian Raschka"
            "Cameron R. Wolfe, Ph.D." → "Cameron R. Wolfe"
            "John   Smith" → "John Smith"

        Args:
            name: Raw author name

        Returns:
            Normalized author name
        """
        if not name or not isinstance(name, str):
            return None

        # Remove common academic suffixes
        # Pattern matches: , PhD | , Ph.D. | , MD | , Dr. | PhD | Ph.D. at end of string
        suffixes_pattern = r',?\s*(PhD|Ph\.D\.|MD|M\.D\.|Dr\.?|Esq\.?)\s*$'
        name = re.sub(suffixes_pattern, '', name, flags=re.IGNORECASE)

        # Remove extra whitespace and normalize
        name = ' '.join(name.split())

        # Remove trailing commas/periods that might be left over
        name = name.rstrip('.,')

        return name.strip()

    def parse_author_string(self, author_str: str) -> Tuple[str, List[str]]:
        """
        Parse author string that may contain multiple authors.

        Handles formats like:
            "John Doe" → ("John Doe", [])
            "John Doe and Jane Smith" → ("John Doe", ["Jane Smith"])
            "A, B and C" → ("A", ["B", "C"])

        Args:
            author_str: Raw author string

        Returns:
            Tuple of (primary_author, co_authors_list)
        """
        if not author_str or not isinstance(author_str, str):
            return (None, [])

        # Normalize the input
        author_str = author_str.strip()

        # Split by " and " (most common separator)
        if ' and ' in author_str.lower():
            parts = re.split(r'\s+and\s+', author_str, flags=re.IGNORECASE)
            primary = self.normalize_name(parts[0])
            co_authors = [self.normalize_name(a) for a in parts[1:] if a.strip()]
            return (primary, co_authors)

        # Split by comma (less common, e.g., "Smith, John and Doe, Jane")
        elif ',' in author_str and ' and ' not in author_str.lower():
            # Check if it's just a name with suffix (e.g., "John Smith, PhD")
            parts = author_str.split(',')
            if len(parts) == 2 and len(parts[1].strip().split()) <= 2:
                # Likely "Name, Suffix" format
                return (self.normalize_name(author_str), [])
            else:
                # Multiple authors separated by commas
                primary = self.normalize_name(parts[0])
                co_authors = [self.normalize_name(a) for a in parts[1:] if a.strip()]
                return (primary, co_authors)

        # Single author
        return (self.normalize_name(author_str), [])

    def similarity_score(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings (0.0 to 1.0).

        Uses SequenceMatcher for fuzzy string matching.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0 = completely different, 1.0 = identical)
        """
        if not str1 or not str2:
            return 0.0

        # Normalize for comparison
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()

        return SequenceMatcher(None, s1, s2).ratio()

    def find_similar_authors(self, name: str, threshold: float = 0.85) -> List[Dict]:
        """
        Find authors in database with similar names (fuzzy matching).

        Args:
            name: Author name to search for
            threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of author documents with similarity scores
        """
        if not name:
            return []

        normalized_name = self.normalize_name(name)

        # Get all authors from database
        all_authors = list(self.authors_collection.find({}, {'name': 1, 'canonical_name': 1}))

        similar = []
        for author in all_authors:
            author_name = author.get('canonical_name') or author.get('name')
            if not author_name:
                continue

            score = self.similarity_score(normalized_name, author_name)
            if score >= threshold:
                similar.append({
                    '_id': author['_id'],
                    'name': author_name,
                    'similarity': score
                })

        # Sort by similarity score (highest first)
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar

    def find_or_create_author(
        self,
        name: str,
        email: Optional[str] = None,
        subdomain: Optional[str] = None,
        auto_create: bool = True
    ) -> Optional[ObjectId]:
        """
        Find an existing author by normalized name or create a new one.

        Uses fuzzy matching to find similar authors. If auto_create is True
        and no match is found, creates a new author record.

        Args:
            name: Author name (will be normalized)
            email: Optional author email
            subdomain: Optional Substack subdomain
            auto_create: Whether to create new author if not found

        Returns:
            ObjectId of found or created author, or None if not found and auto_create=False
        """
        if not name:
            return None

        normalized_name = self.normalize_name(name)

        # First try exact match on canonical_name or name
        author = self.authors_collection.find_one({
            '$or': [
                {'canonical_name': normalized_name},
                {'name': normalized_name}
            ]
        })

        if author:
            return author['_id']

        # Try fuzzy matching (high threshold for automatic matching)
        similar = self.find_similar_authors(normalized_name, threshold=0.9)
        if similar:
            # Return the most similar author
            return similar[0]['_id']

        # No match found
        if not auto_create:
            return None

        # Create new author
        author_doc = {
            'canonical_name': normalized_name,
            'display_name': name,  # Keep original formatting for display
            'name_variations': [name, normalized_name],
            'email': email,
            'subdomain': subdomain or self._generate_subdomain(normalized_name),
            'article_count': 0,
            'last_article_date': None,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

        result = self.authors_collection.insert_one(author_doc)
        return result.inserted_id

    def _generate_subdomain(self, name: str) -> str:
        """Generate a subdomain from author name (lowercase, no spaces)"""
        if not name:
            return None

        # Convert to lowercase, replace spaces with nothing
        subdomain = name.lower().replace(' ', '').replace('.', '')
        # Remove special characters
        subdomain = re.sub(r'[^a-z0-9]', '', subdomain)
        return subdomain

    def get_canonical_author(self, name: str) -> Optional[Dict]:
        """
        Get the canonical author record for a given name.

        Args:
            name: Author name (any variation)

        Returns:
            Author document with canonical information, or None if not found
        """
        if not name:
            return None

        normalized_name = self.normalize_name(name)

        # Try exact match first
        author = self.authors_collection.find_one({
            '$or': [
                {'canonical_name': normalized_name},
                {'name': normalized_name},
                {'name_variations': normalized_name}
            ]
        })

        if author:
            return author

        # Try fuzzy matching
        similar = self.find_similar_authors(normalized_name, threshold=0.85)
        if similar:
            # Get full document of most similar author
            return self.authors_collection.find_one({'_id': similar[0]['_id']})

        return None

    def update_author_stats(self, author_id: ObjectId) -> bool:
        """
        Update article_count and last_article_date for an author.

        Args:
            author_id: ObjectId of author to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Count articles where this author is primary
            article_count = self.articles_collection.count_documents({
                'primary_author_id': author_id
            })

            # Also count co-authored articles
            co_author_count = self.articles_collection.count_documents({
                'co_author_ids': author_id
            })

            total_count = article_count + co_author_count

            # Get most recent article date
            recent_article = self.articles_collection.find_one(
                {
                    '$or': [
                        {'primary_author_id': author_id},
                        {'co_author_ids': author_id}
                    ]
                },
                sort=[('published_at', -1)]
            )

            last_date = recent_article.get('published_at') if recent_article else None

            # Update author record
            self.authors_collection.update_one(
                {'_id': author_id},
                {
                    '$set': {
                        'article_count': total_count,
                        'last_article_date': last_date,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )

            return True

        except Exception as e:
            print(f"Error updating author stats: {e}")
            return False

    def merge_authors(self, source_id: ObjectId, target_id: ObjectId) -> bool:
        """
        Merge two author records (source → target).

        All articles from source author are reassigned to target author,
        then source author is deleted.

        Args:
            source_id: Author to merge from (will be deleted)
            target_id: Author to merge into (will be kept)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get both author records
            source = self.authors_collection.find_one({'_id': source_id})
            target = self.authors_collection.find_one({'_id': target_id})

            if not source or not target:
                return False

            # Update all articles with source as primary author
            self.articles_collection.update_many(
                {'primary_author_id': source_id},
                {'$set': {'primary_author_id': target_id}}
            )

            # Update all articles with source as co-author
            # First, find all articles with source_id in co_author_ids
            articles_with_source = list(self.articles_collection.find(
                {'co_author_ids': source_id},
                {'_id': 1}
            ))
            article_ids = [doc['_id'] for doc in articles_with_source]

            # Remove source_id from co_author_ids
            if article_ids:
                self.articles_collection.update_many(
                    {'_id': {'$in': article_ids}},
                    {'$pull': {'co_author_ids': source_id}}
                )
                # Then add target_id to co_author_ids
                self.articles_collection.update_many(
                    {'_id': {'$in': article_ids}},
                    {'$addToSet': {'co_author_ids': target_id}}
                )

            # Merge name variations
            source_variations = source.get('name_variations', [])
            self.authors_collection.update_one(
                {'_id': target_id},
                {
                    '$addToSet': {
                        'name_variations': {'$each': source_variations}
                    }
                }
            )

            # Update target stats
            self.update_author_stats(target_id)

            # Delete source author
            self.authors_collection.delete_one({'_id': source_id})

            return True

        except Exception as e:
            print(f"Error merging authors: {e}")
            return False
