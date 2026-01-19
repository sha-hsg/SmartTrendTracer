"""
Tag service using MongoDB for tag concept management
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from app.database.mongodb import get_mongodb
from app.models.mongodb_models import (
    TagConcept, TagAlias, TagRelation, 
    TagInstance, ConceptStatus, AliasType
)

logger = logging.getLogger(__name__)

class TagServiceMongoDB:
    """Service for managing tags using MongoDB"""
    
    def __init__(self):
        self.mongo = get_mongodb()
    
    def get_concept_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a concept by its slug"""
        return self.mongo.concepts.find_one({"slug": slug})
    
    def get_concept_by_id(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Get a concept by its ID"""
        return self.mongo.concepts.find_one({"id": concept_id})
    
    def get_concept_by_alias(self, alias_text: str) -> Optional[Dict[str, Any]]:
        """Get a concept by any of its aliases"""
        alias = self.mongo.aliases.find_one({"alias_text": alias_text.lower()})
        if alias:
            return self.get_concept_by_id(alias['concept_id'])
        return None
    
    def get_all_concepts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all concepts, optionally filtered by status"""
        query = {}
        if status:
            query["status"] = status
        return list(self.mongo.concepts.find(query))
    
    def get_root_concepts(self) -> List[Dict[str, Any]]:
        """Get all root concepts (no parents)"""
        return list(self.mongo.concepts.find({
            "$or": [
                {"parents": []},
                {"parents": {"$exists": False}}
            ]
        }))
    
    def get_concept_children(self, concept_id: str) -> List[Dict[str, Any]]:
        """Get all direct children of a concept"""
        return list(self.mongo.concepts.find({"parents": concept_id}))
    
    def get_concept_descendants(self, concept_id: str) -> List[Dict[str, Any]]:
        """Get all descendants of a concept (recursive)"""
        descendants = []
        to_process = [concept_id]
        processed = set()
        
        while to_process:
            current_id = to_process.pop(0)
            if current_id in processed:
                continue
            processed.add(current_id)
            
            children = self.get_concept_children(current_id)
            descendants.extend(children)
            to_process.extend([child['id'] for child in children])
        
        return descendants
    
    def create_concept(self, concept_data: Dict[str, Any]) -> str:
        """Create a new concept"""
        # Generate ID if not provided
        if 'id' not in concept_data:
            concept_data['id'] = self._generate_concept_id()
        
        # Set defaults
        concept_data.setdefault('status', ConceptStatus.ACTIVE.value)
        concept_data.setdefault('usage_count', 0)
        concept_data.setdefault('parents', [])
        concept_data.setdefault('children', [])
        concept_data.setdefault('level', 0)
        concept_data.setdefault('metadata', {})
        concept_data.setdefault('created_at', datetime.utcnow())
        concept_data.setdefault('updated_at', datetime.utcnow())
        
        # Insert concept
        result = self.mongo.concepts.insert_one(concept_data)
        
        # Update parent's children list
        for parent_id in concept_data['parents']:
            self.mongo.concepts.update_one(
                {"id": parent_id},
                {"$addToSet": {"children": concept_data['id']}}
            )
        
        return concept_data['id']
    
    def update_concept(self, concept_id: str, updates: Dict[str, Any]) -> bool:
        """Update a concept"""
        updates['updated_at'] = datetime.utcnow()
        
        # Handle parent changes
        if 'parents' in updates:
            old_concept = self.get_concept_by_id(concept_id)
            if old_concept:
                old_parents = set(old_concept.get('parents', []))
                new_parents = set(updates['parents'])
                
                # Remove from old parents
                for parent_id in old_parents - new_parents:
                    self.mongo.concepts.update_one(
                        {"id": parent_id},
                        {"$pull": {"children": concept_id}}
                    )
                
                # Add to new parents
                for parent_id in new_parents - old_parents:
                    self.mongo.concepts.update_one(
                        {"id": parent_id},
                        {"$addToSet": {"children": concept_id}}
                    )
        
        result = self.mongo.concepts.update_one(
            {"id": concept_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    def create_alias(self, alias_text: str, concept_id: str, 
                    alias_type: str = "synonym", confidence: float = 1.0) -> bool:
        """Create an alias for a concept"""
        alias_data = {
            "alias_text": alias_text.lower(),
            "concept_id": concept_id,
            "alias_type": alias_type,
            "confidence": confidence,
            "created_at": datetime.utcnow()
        }
        
        try:
            self.mongo.aliases.insert_one(alias_data)
            return True
        except Exception as e:
            logger.error(f"Failed to create alias: {e}")
            return False
    
    def get_concept_aliases(self, concept_id: str) -> List[Dict[str, Any]]:
        """Get all aliases for a concept"""
        return list(self.mongo.aliases.find({"concept_id": concept_id}))
    
    def record_tag_instance(self, content_type: str, content_id: str,
                           tag_text: str, tag_type: str = "manual") -> bool:
        """Record a tag being used on content"""
        # Try to find the concept
        concept = self.get_concept_by_alias(tag_text)
        concept_id = concept['id'] if concept else None
        display_name = concept['display_name'] if concept else tag_text
        
        instance_data = {
            "content_type": content_type,
            "content_id": str(content_id),
            "concept_id": concept_id,
            "original_text": tag_text,
            "display_name": display_name,
            "tag_type": tag_type,
            "metadata": {},
            "created_at": datetime.utcnow()
        }
        
        try:
            self.mongo.instances.insert_one(instance_data)
            
            # Update usage count if concept exists
            if concept_id:
                self.mongo.concepts.update_one(
                    {"id": concept_id},
                    {"$inc": {"usage_count": 1}}
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to record tag instance: {e}")
            return False
    
    def get_content_tags(self, content_type: str, content_id: str) -> List[Dict[str, Any]]:
        """Get all tags for a piece of content"""
        return list(self.mongo.instances.find({
            "content_type": content_type,
            "content_id": str(content_id)
        }))
    
    def get_concept_usage_stats(self, concept_id: str) -> Dict[str, int]:
        """Get usage statistics for a concept"""
        # Count direct usage
        direct_count = self.mongo.instances.count_documents({"concept_id": concept_id})
        
        # Count alias usage
        aliases = self.get_concept_aliases(concept_id)
        alias_texts = [a['alias_text'] for a in aliases]
        alias_count = self.mongo.instances.count_documents({
            "original_text": {"$in": alias_texts}
        })
        
        # Count by content type
        pipeline = [
            {"$match": {"concept_id": concept_id}},
            {"$group": {
                "_id": "$content_type",
                "count": {"$sum": 1}
            }}
        ]
        type_counts = {
            doc['_id']: doc['count'] 
            for doc in self.mongo.instances.aggregate(pipeline)
        }
        
        return {
            "total": direct_count + alias_count,
            "direct": direct_count,
            "via_aliases": alias_count,
            "tweets": type_counts.get("tweet", 0),
            "papers": type_counts.get("paper", 0),
            "articles": type_counts.get("article", 0)
        }
    
    def search_concepts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for concepts by text"""
        # Search in display names and slugs
        concepts = list(self.mongo.concepts.find({
            "$or": [
                {"display_name": {"$regex": query, "$options": "i"}},
                {"slug": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }).limit(limit))
        
        # Also search in aliases
        aliases = list(self.mongo.aliases.find({
            "alias_text": {"$regex": query, "$options": "i"}
        }).limit(limit))
        
        # Get concepts for found aliases
        for alias in aliases:
            concept = self.get_concept_by_id(alias['concept_id'])
            if concept and concept not in concepts:
                concepts.append(concept)
        
        return concepts[:limit]
    
    def _generate_concept_id(self) -> str:
        """Generate a new concept ID"""
        # Get the highest existing ID
        last_concept = self.mongo.concepts.find_one(
            {},
            sort=[("id", -1)]
        )
        
        if last_concept and last_concept['id'].startswith('c_'):
            try:
                last_num = int(last_concept['id'][2:])
                return f"c_{last_num + 1:04d}"
            except:
                pass
        
        return "c_0001"
    
    def apply_reorganization_proposal(self, proposal_id: str) -> bool:
        """Apply a reorganization proposal from MongoDB"""
        proposal = self.mongo.proposals.find_one({"proposal_id": proposal_id})
        if not proposal or proposal['status'] != 'draft':
            return False
        
        try:
            # Clear existing concepts and aliases
            self.mongo.concepts.delete_many({})
            self.mongo.aliases.delete_many({})
            self.mongo.relations.delete_many({})
            
            # Apply concepts
            for concept_data in proposal['concepts']:
                concept_data['created_at'] = datetime.utcnow()
                concept_data['updated_at'] = datetime.utcnow()
                self.mongo.concepts.insert_one(concept_data)
            
            # Apply aliases
            for alias_data in proposal['aliases']:
                alias_data['created_at'] = datetime.utcnow()
                self.mongo.aliases.insert_one(alias_data)
            
            # Apply relations
            for relation_data in proposal.get('relations', []):
                relation_data['created_at'] = datetime.utcnow()
                self.mongo.relations.insert_one(relation_data)
            
            # Update proposal status
            self.mongo.proposals.update_one(
                {"proposal_id": proposal_id},
                {
                    "$set": {
                        "status": "applied",
                        "applied_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Successfully applied reorganization proposal {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply reorganization proposal: {e}")
            return False


# Singleton instance
_tag_service_mongodb = None

def get_tag_service_mongodb() -> TagServiceMongoDB:
    """Get the MongoDB tag service instance"""
    global _tag_service_mongodb
    if _tag_service_mongodb is None:
        _tag_service_mongodb = TagServiceMongoDB()
    return _tag_service_mongodb