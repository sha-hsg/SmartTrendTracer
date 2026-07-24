"""
Concept-only tag service for MongoDB.
All tags are now concepts with IDs. No more orphan tags or text-based tags.
"""

from app.services.concept_tag.lookup import ConceptLookupMixin
from app.services.concept_tag.tagging import ConceptTaggingMixin


class ConceptOnlyTagService(ConceptLookupMixin, ConceptTaggingMixin):
    """Service for managing tags as concepts in MongoDB"""

    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            from app.database.mongodb import get_client, get_database

            cls._client = get_client()
            cls._db = get_database()
        return cls._instance

    @property
    def db(self):
        """Get database instance"""
        return self._db

    @property
    def tag_instances(self):
        """Get tag_instances collection"""
        return self.db.tag_instances

    @property
    def tag_concepts(self):
        """Get tag_concepts_v2 collection"""
        return self.db.tag_concepts_v2

    @property
    def tag_aliases(self):
        """Get tag_aliases_v2 collection"""
        return self.db.tag_aliases_v2
