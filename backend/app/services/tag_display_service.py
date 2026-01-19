"""
Tag Display Service - Handles display name retrieval for tags
"""
from typing import Dict, Optional
from .slug_normalizer import to_display_name
import logging

logger = logging.getLogger(__name__)

class TagDisplayService:
    """Service for retrieving display names for tags"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, str] = {}
        self._load_normalization_table()
    
    def _load_normalization_table(self):
        """Load tag normalization mappings from database"""
        try:
            # Check if normalization table exists
            result = self.db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tag_normalization'"
            ))
            if not result.fetchone():
                logger.debug("tag_normalization table doesn't exist yet")
                return
            
            # Load all mappings
            result = self.db.execute(text(
                "SELECT original_tag, display_name FROM tag_normalization"
            ))
            for original, display in result:
                self._cache[original] = display
            
            logger.info(f"Loaded {len(self._cache)} tag display mappings")
            
        except Exception as e:
            logger.warning(f"Could not load tag normalization table: {e}")
    
    def get_display_name(self, tag: str) -> str:
        """
        Get the display name for a tag.
        
        Args:
            tag: The original tag text
            
        Returns:
            The display name for UI presentation
        """
        if not tag:
            return tag
        
        # Check cache first
        if tag in self._cache:
            return self._cache[tag]
        
        # Check tag_normalization table
        try:
            result = self.db.execute(text(
                "SELECT display_name FROM tag_normalization WHERE original_tag = :tag"
            ), {"tag": tag})
            row = result.fetchone()
            if row:
                display = row[0]
                self._cache[tag] = display
                return display
        except Exception as e:
            logger.debug(f"Could not query tag_normalization: {e}")
        
        # Check tag_concepts table
        try:
            from ..models.tag_ontology import TagConcept
            concept = self.db.query(TagConcept).filter(
                TagConcept.tag == tag
            ).first()
            if concept and concept.display_name:
                display = concept.display_name
                self._cache[tag] = display
                return display
        except Exception as e:
            logger.debug(f"Could not query tag_concepts: {e}")
        
        # Generate display name using normalizer
        display = to_display_name(tag)
        self._cache[tag] = display
        return display
    
    def get_display_names_bulk(self, tags: list) -> Dict[str, str]:
        """
        Get display names for multiple tags at once.
        
        Args:
            tags: List of tag strings
            
        Returns:
            Dictionary mapping original tags to display names
        """
        result = {}
        for tag in tags:
            result[tag] = self.get_display_name(tag)
        return result